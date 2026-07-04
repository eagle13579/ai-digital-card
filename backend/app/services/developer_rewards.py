"""
链客宝 — 开发者奖励计划服务
===============================
奖励类型:
  - 安装奖励: 每次安装获得积分
  - 质量奖励: 高评分插件额外奖励
  - 活动奖励: 月度最佳插件奖励

积分兑换:
  - API 调用额度
  - 推广曝光

排行榜: GET /api/v1/app-store/leaderboard
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import func as sa_func, desc
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.app_store import (
    Plugin,
    PluginInstall,
    DeveloperReward,
    DeveloperRewardBalance,
    DeveloperRewardType,
    DeveloperRewardStatus,
    RewardRedemption,
    RewardRedemptionCreate,
    RewardLeaderboardEntry,
)
from app.models.user import User

logger = logging.getLogger("chainke.developer_rewards")

# ── 积分常量 ─────────────────────────────────────────────────────────
POINTS_PER_INSTALL = 10           # 每次安装 10 积分
QUALITY_BONUS_THRESHOLD = 4.5     # 评分 >= 4.5 获得质量奖励
QUALITY_BONUS_POINTS = 100        # 质量奖励积分
MONTHLY_ACTIVITY_POINTS = 500     # 月度最佳插件奖励
API_QUOTA_PER_100_POINTS = 1000   # 100 积分兑换 1000 次 API 调用
PROMOTION_IMPRESSIONS_PER_100 = 5000  # 100 积分兑换 5000 次推广曝光

REWARD_TYPES = {
    DeveloperRewardType.INSTALL: "安装奖励",
    DeveloperRewardType.QUALITY: "质量奖励",
    DeveloperRewardType.ACTIVITY: "活动奖励",
    DeveloperRewardType.BONUS: "额外奖励",
}


# ===================================================================
# 依赖
# ===================================================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _get_or_create_balance(db: Session, developer_id: int) -> DeveloperRewardBalance:
    """获取或创建开发者积分余额"""
    balance = db.query(DeveloperRewardBalance).filter(
        DeveloperRewardBalance.developer_id == developer_id
    ).first()
    if not balance:
        balance = DeveloperRewardBalance(
            developer_id=developer_id,
            total_points=0,
            used_points=0,
            balance=0,
        )
        db.add(balance)
        db.flush()
    return balance


# ===================================================================
# 奖励发放
# ===================================================================


def award_install_reward(db: Session, developer_id: int, plugin_id: int) -> Optional[DeveloperReward]:
    """发放安装奖励"""
    reward = DeveloperReward(
        developer_id=developer_id,
        reward_type=DeveloperRewardType.INSTALL,
        points=POINTS_PER_INSTALL,
        reason=f"插件安装奖励 (Plugin #{plugin_id})",
        source_id=plugin_id,
        source_desc=f"插件 #{plugin_id} 安装",
        status=DeveloperRewardStatus.PENDING,
    )
    db.add(reward)
    db.flush()
    return reward


def award_quality_reward(db: Session, developer_id: int, plugin_id: int, rating: float) -> Optional[DeveloperReward]:
    """发放质量奖励（评分达到阈值）"""
    if rating < QUALITY_BONUS_THRESHOLD:
        return None

    # 检查是否已经为该插件发放过质量奖励
    existing = db.query(DeveloperReward).filter(
        DeveloperReward.developer_id == developer_id,
        DeveloperReward.reward_type == DeveloperRewardType.QUALITY,
        DeveloperReward.source_id == plugin_id,
    ).first()
    if existing:
        return None

    reward = DeveloperReward(
        developer_id=developer_id,
        reward_type=DeveloperRewardType.QUALITY,
        points=QUALITY_BONUS_POINTS,
        reason=f"插件质量奖励: 评分 {rating:.1f}",
        source_id=plugin_id,
        source_desc=f"插件 #{plugin_id} 评分奖励",
        status=DeveloperRewardStatus.PENDING,
    )
    db.add(reward)
    db.flush()
    return reward


def issue_monthly_activity_reward(db: Session, developer_id: int, plugin_id: int, rank: int = 1) -> DeveloperReward:
    """发放月度活动奖励（月度最佳插件）"""
    points = MONTHLY_ACTIVITY_POINTS
    if rank > 1:
        points = max(100, MONTHLY_ACTIVITY_POINTS - (rank - 1) * 100)

    reward = DeveloperReward(
        developer_id=developer_id,
        reward_type=DeveloperRewardType.ACTIVITY,
        points=points,
        reason=f"月度最佳插件 #{(rank)} (Plugin #{plugin_id})",
        source_id=plugin_id,
        source_desc=f"月度活动排名 #{rank}",
        status=DeveloperRewardStatus.PENDING,
    )
    db.add(reward)
    db.flush()
    return reward


def issue_rewards(db: Session, developer_id: int) -> int:
    """发放所有待发放奖励，更新余额"""
    pending = db.query(DeveloperReward).filter(
        DeveloperReward.developer_id == developer_id,
        DeveloperReward.status == DeveloperRewardStatus.PENDING,
    ).all()

    if not pending:
        return 0

    total_points = sum(r.points for r in pending)
    now = datetime.utcnow()

    for reward in pending:
        reward.status = DeveloperRewardStatus.ISSUED
        reward.issued_at = now

    balance = _get_or_create_balance(db, developer_id)
    balance.total_points += total_points
    balance.balance += total_points
    balance.updated_at = now

    db.flush()
    logger.info("[Rewards] 开发者 %d: 发放 %d 条奖励, 共 %d 积分", developer_id, len(pending), total_points)
    return total_points


def issue_all_pending_rewards(db: Session) -> dict:
    """发放所有开发者的待发放奖励"""
    developer_ids = [
        r[0] for r in db.query(DeveloperReward.developer_id).filter(
            DeveloperReward.status == DeveloperRewardStatus.PENDING
        ).distinct().all()
    ]
    total_issued = 0
    for dev_id in developer_ids:
        total_issued += issue_rewards(db, dev_id)
    db.commit()
    return {"developers": len(developer_ids), "points_issued": total_issued}


# ===================================================================
# 积分兑换
# ===================================================================


def redeem_rewards(
    db: Session,
    developer_id: int,
    data: RewardRedemptionCreate,
) -> Optional[RewardRedemption]:
    """积分兑换"""
    balance = _get_or_create_balance(db, developer_id)
    if balance.balance < data.points_spent:
        logger.warning("[Rewards] 开发者 %d 积分不足: 需要 %d, 可用 %d",
                       developer_id, data.points_spent, balance.balance)
        return None

    # 计算兑换量
    quota_amount = data.quota_amount
    if data.redemption_type == "api_quota":
        quota_amount = quota_amount or (data.points_spent // 100) * API_QUOTA_PER_100_POINTS
    elif data.redemption_type == "promotion":
        quota_amount = quota_amount or (data.points_spent // 100) * PROMOTION_IMPRESSIONS_PER_100

    redemption = RewardRedemption(
        developer_id=developer_id,
        points_spent=data.points_spent,
        redemption_type=data.redemption_type,
        quota_amount=quota_amount,
        description=data.description or f"兑换 {data.redemption_type} x{quota_amount}",
        status="completed",
    )
    db.add(redemption)

    balance.used_points += data.points_spent
    balance.balance -= data.points_spent
    balance.updated_at = datetime.utcnow()

    db.flush()
    logger.info("[Rewards] 开发者 %d: 兑换 %s, 消耗 %d 积分",
                developer_id, data.redemption_type, data.points_spent)
    return redemption


# ===================================================================
# 查询
# ===================================================================


def get_developer_balance(db: Session, developer_id: int) -> Optional[DeveloperRewardBalance]:
    """获取开发者积分余额"""
    return _get_or_create_balance(db, developer_id)


def get_developer_rewards(
    db: Session,
    developer_id: int,
    limit: int = 50,
    offset: int = 0,
) -> list[DeveloperReward]:
    """获取开发者奖励记录"""
    return db.query(DeveloperReward).filter(
        DeveloperReward.developer_id == developer_id
    ).order_by(desc(DeveloperReward.created_at)).offset(offset).limit(limit).all()


def get_developer_redemptions(
    db: Session,
    developer_id: int,
    limit: int = 50,
    offset: int = 0,
) -> list[RewardRedemption]:
    """获取开发者兑换记录"""
    return db.query(RewardRedemption).filter(
        RewardRedemption.developer_id == developer_id
    ).order_by(desc(RewardRedemption.created_at)).offset(offset).limit(limit).all()


# ===================================================================
# 排行榜
# ===================================================================


def get_leaderboard(
    db: Session,
    limit: int = 20,
    offset: int = 0,
) -> list[RewardLeaderboardEntry]:
    """获取开发者积分排行榜"""
    balances = db.query(
        DeveloperRewardBalance,
    ).order_by(
        desc(DeveloperRewardBalance.total_points)
    ).offset(offset).limit(limit).all()

    entries = []
    for i, row in enumerate(balances):
        balance = row
        user = db.query(User).filter(User.id == balance.developer_id).first()
        plugin_count = db.query(Plugin).filter(
            Plugin.developer_id == balance.developer_id
        ).count()

        entries.append(RewardLeaderboardEntry(
            rank=offset + i + 1,
            developer_id=balance.developer_id,
            developer_name=user.name or user.username if user else f"Developer #{balance.developer_id}",
            total_points=balance.total_points,
            balance=balance.balance,
            plugin_count=plugin_count,
        ))

    return entries


# ===================================================================
# 自动奖励钩子（供其他模块调用）
# ===================================================================


def on_plugin_installed(plugin_id: int, developer_id: int) -> None:
    """插件安装回调：记录安装奖励"""
    db = SessionLocal()
    try:
        award_install_reward(db, developer_id, plugin_id)
        db.commit()
        logger.info("[Rewards] 安装奖励已记录: developer=%d, plugin=%d", developer_id, plugin_id)
    except Exception as e:
        db.rollback()
        logger.error("[Rewards] 安装奖励记录失败: %s", e)
    finally:
        db.close()


def on_plugin_rated(plugin_id: int, developer_id: int, rating: float) -> None:
    """插件评分回调：发放质量奖励"""
    db = SessionLocal()
    try:
        reward = award_quality_reward(db, developer_id, plugin_id, rating)
        if reward:
            db.commit()
            logger.info("[Rewards] 质量奖励已记录: developer=%d, plugin=%d, rating=%.1f",
                        developer_id, plugin_id, rating)
    except Exception as e:
        db.rollback()
        logger.error("[Rewards] 质量奖励记录失败: %s", e)
    finally:
        db.close()
