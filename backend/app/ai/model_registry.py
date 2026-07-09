"""
模型注册 — ModelRegistry
- 版本管理 + stage 提升 (staging / production)
- 字典 + SQLite 持久化
- 生产模型获取
"""

import json
import logging
import os
import sqlite3
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

DB_PATH = "model_registry.db"


@dataclass
class ModelRecord:
    """模型记录。"""
    name: str
    version: str
    path: str
    metrics: Dict[str, Any] = field(default_factory=dict)
    stage: str = "none"          # none / staging / production
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class ModelRegistry:
    """模型注册中心 (线程安全, SQLite 持久化)。

    说明: 使用文件路径时数据持久化到磁盘；使用 ':memory:' 仅在当前连接有效。
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_db()

    # ── SQLite 初始化 ─────────────────────────────────────────

    def _init_db(self):
        # 使用持久连接避免 :memory: 模式丢失表
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS models (
                name TEXT NOT NULL,
                version TEXT NOT NULL,
                path TEXT NOT NULL,
                metrics TEXT DEFAULT '{}',
                stage TEXT DEFAULT 'none',
                created_at TEXT DEFAULT (datetime('now')),
                PRIMARY KEY (name, version)
            )
        """)
        self._conn.commit()

    def _row_to_record(self, row: tuple) -> ModelRecord:
        return ModelRecord(
            name=row[0],
            version=row[1],
            path=row[2],
            metrics=json.loads(row[3]) if row[3] else {},
            stage=row[4],
            created_at=row[5],
        )

    # ── CRUD ──────────────────────────────────────────────────

    def register_model(
        self,
        name: str,
        version: str,
        path: str,
        metrics: Optional[Dict[str, Any]] = None,
    ) -> ModelRecord:
        """注册一个新模型版本。"""
        record = ModelRecord(
            name=name,
            version=version,
            path=path,
            metrics=metrics or {},
        )
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO models (name, version, path, metrics, stage, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (record.name, record.version, record.path,
                 json.dumps(record.metrics), record.stage, record.created_at),
            )
            self._conn.commit()
        logger.info("注册模型: %s v%s (path=%s)", name, version, path)
        return record

    def get_model(self, name: str, version: str) -> Optional[ModelRecord]:
        """获取指定版本模型。"""
        with self._lock:
            cursor = self._conn.execute(
                "SELECT name, version, path, metrics, stage, created_at FROM models "
                "WHERE name=? AND version=?",
                (name, version),
            )
            row = cursor.fetchone()
        if row is None:
            logger.warning("模型未找到: %s v%s", name, version)
            return None
        return self._row_to_record(row)

    def list_models(self) -> List[ModelRecord]:
        """列出所有已注册模型。"""
        with self._lock:
            cursor = self._conn.execute(
                "SELECT name, version, path, metrics, stage, created_at FROM models "
                "ORDER BY name, created_at DESC"
            )
            rows = cursor.fetchall()
        return [self._row_to_record(r) for r in rows]

    # ── Stage 提升 ────────────────────────────────────────────

    def promote_model(self, name: str, version: str, stage: str) -> Optional[ModelRecord]:
        """提升模型到指定 stage (staging / production)。

        提升到 production 时会自动将同一 name 下其他 production 模型降级为 staging。
        """
        if stage not in ("staging", "production"):
            raise ValueError("stage 必须是 staging 或 production")

        with self._lock:
            # 检查模型是否存在
            cursor = self._conn.execute(
                "SELECT name, version, path, metrics, stage, created_at FROM models "
                "WHERE name=? AND version=?",
                (name, version),
            )
            row = cursor.fetchone()
            if row is None:
                logger.warning("提升失败: 模型 %s v%s 不存在", name, version)
                return None

            if stage == "production":
                # 降级当前 production
                self._conn.execute(
                    "UPDATE models SET stage='staging' WHERE name=? AND stage='production'",
                    (name,),
                )

            self._conn.execute(
                "UPDATE models SET stage=? WHERE name=? AND version=?",
                (stage, name, version),
            )
            self._conn.commit()

            # 返回更新后的记录
            cursor = self._conn.execute(
                "SELECT name, version, path, metrics, stage, created_at FROM models "
                "WHERE name=? AND version=?",
                (name, version),
            )
            updated = self._row_to_record(cursor.fetchone())
            logger.info("模型提升: %s v%s → %s", name, version, stage)
            return updated

    def get_production_model(self, name: str) -> Optional[ModelRecord]:
        """获取生产环境模型。"""
        with self._lock:
            cursor = self._conn.execute(
                "SELECT name, version, path, metrics, stage, created_at FROM models "
                "WHERE name=? AND stage='production' ORDER BY created_at DESC LIMIT 1",
                (name,),
            )
            row = cursor.fetchone()
        if row is None:
            logger.info("模型 %s 没有 production 版本", name)
            return None
        return self._row_to_record(row)

    # ── 模型 A/B 自动对比 ─────────────────────────────────────

    def compare_models(self, name: str, metric: str = "auto") -> Optional[dict]:
        """比较最新 staging 模型与当前 production 模型的指标, 自动提升更优者。

        流程:
          1. 获取当前 production 模型和最新 staging 模型
          2. 用指定指标比较
          3. staging 更优 → 自动 promote 到 production

        Args:
            name: 模型名称
            metric: 指标名称, "auto" 自动选择(按优先级: accuracy/f1/precision/recall)

        Returns:
            dict: {compared, production, staging, winner, metric, prod_value, stage_value}
        """
        production = self.get_production_model(name)
        staging = self._get_staging_model(name)

        if not staging:
            logger.info("[compare_models] %s: 无 staging 模型, 跳过", name)
            return None

        result = {
            "compared": False,
            "production": production,
            "staging": staging,
            "winner": "none",
            "metric": metric,
            "prod_value": None,
            "stage_value": None,
        }

        if not production:
            logger.info("[compare_models] %s: 无 production, 直接提升 staging v%s",
                        name, staging.version)
            promoted = self.promote_model(name, staging.version)
            result["compared"] = True
            result["winner"] = "staging"
            result["production"] = promoted
            return result

        # 自动选择指标
        if metric == "auto":
            for m in ("accuracy", "f1", "precision", "recall", "ndcg", "auc"):
                if m in staging.metrics and m in production.metrics:
                    metric = m
                    break
            if metric == "auto":
                common = set(staging.metrics.keys()) & set(production.metrics.keys())
                if common:
                    metric = list(common)[0]

        if metric not in staging.metrics or metric not in production.metrics:
            logger.info("[compare_models] %s: 指标 '%s' 不全, 跳过", name, metric)
            return None

        prod_val = float(production.metrics[metric])
        stage_val = float(staging.metrics[metric])
        result["metric"] = metric
        result["prod_value"] = prod_val
        result["stage_value"] = stage_val

        if stage_val > prod_val:
            logger.info("[compare_models] %s: staging(%.4f) > production(%.4f), 自动提升",
                        name, stage_val, prod_val)
            promoted = self.promote_model(name, staging.version)
            result["compared"] = True
            result["winner"] = "staging"
            result["production"] = promoted
        else:
            logger.info("[compare_models] %s: staging(%.4f) <= production(%.4f), 保持现状",
                        name, stage_val, prod_val)
            result["compared"] = True
            result["winner"] = "production"

        return result

    def _get_staging_model(self, name: str) -> Optional[ModelRecord]:
        """获取最新 staging 模型。"""
        cursor = self._conn.execute(
            "SELECT name, version, path, metrics, stage, created_at FROM models "
            "WHERE name=? AND stage='staging' "
            "ORDER BY created_at DESC LIMIT 1",
            (name,),
        )
        row = cursor.fetchone()
        return self._row_to_record(row) if row else None

    # ── 模型健康检查 ──────────────────────────────────────────

    def health_check(self) -> Tuple[int, int]:
        """检查所有 production 模型的文件是否存在。

        返回:
            (healthy_count, total_count) — 健康的模型数量 / 总计数量
        """
        with self._lock:
            cursor = self._conn.execute(
                "SELECT name, version, path, stage FROM models WHERE stage='production'"
            )
            rows = cursor.fetchall()

        total = len(rows)
        healthy = 0

        for name, version, path, stage in rows:
            if os.path.exists(path):
                healthy += 1
                logger.debug("健康检查通过: %s v%s (%s)", name, version, path)
            else:
                logger.warning("健康检查失败: %s v%s 文件不存在 (%s)", name, version, path)

        logger.info("模型健康检查: %d/%d 通过", healthy, total)
        return (healthy, total)

    # ── 模型回滚 ──────────────────────────────────────────────

    def rollback(self, name: str) -> Optional[ModelRecord]:
        """回滚模型: 将上一个 production 版本恢复为 production, 当前版本降为 staging。

        逻辑:
            1. 找出当前 production 版本 → 降级为 staging
            2. 找出上一个 production 版本（时间最接近的 staging 中曾为 production 的）→ 提升为 production
            3. 如果当前没有 production 版本, 从 staging 中选最新的提升

        返回:
            提升后的 ModelRecord, 如果无可用版本则返回 None
        """
        with self._lock:
            # 1. 获取当前 production 版本
            cursor = self._conn.execute(
                "SELECT name, version, path, metrics, stage, created_at FROM models "
                "WHERE name=? AND stage='production' ORDER BY created_at DESC LIMIT 1",
                (name,),
            )
            current_prod = cursor.fetchone()

            # 2. 获取所有 staging 版本, 按创建时间倒序
            cursor = self._conn.execute(
                "SELECT name, version, path, metrics, stage, created_at FROM models "
                "WHERE name=? AND stage='staging' ORDER BY created_at DESC",
                (name,),
            )
            staging_rows = cursor.fetchall()

            if not staging_rows:
                logger.warning("回滚失败: 模型 %s 没有可用的 staging 版本", name)
                return None

            # 3. 降级当前 production → staging (如果有)
            if current_prod is not None:
                self._conn.execute(
                    "UPDATE models SET stage='staging' WHERE name=? AND version=?",
                    (name, current_prod[1]),
                )
                logger.info("降级当前 production: %s v%s → staging", name, current_prod[1])

            # 4. 将最新的 staging 提升为 production
            target_version = staging_rows[0][1]
            self._conn.execute(
                "UPDATE models SET stage='production' WHERE name=? AND version=?",
                (name, target_version),
            )
            self._conn.commit()

            # 5. 返回更新后的记录
            cursor = self._conn.execute(
                "SELECT name, version, path, metrics, stage, created_at FROM models "
                "WHERE name=? AND version=?",
                (name, target_version),
            )
            updated = self._row_to_record(cursor.fetchone())
            logger.info("模型回滚: %s v%s → production (前 production 已降级)", name, target_version)
            return updated
