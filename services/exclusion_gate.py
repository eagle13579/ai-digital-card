
"""芯森态 · Negative Scoring 排除规则门禁
在评分前过滤低质线索，支持可配置规则集
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class ExclusionRule:
    """排除规则定义"""
    rule_id: str
    name: str
    description: str
    severity: str  # soft(降级) / hard(直接排除)
    condition_fn: str  # Python表达式字符串，在eval中执行
    penalty: float = 0.0  # soft模式下扣分


class ExclusionGate:
    """排除门禁 — 评分前过滤低质线索"""

    def __init__(self):
        self.rules = self._default_rules()

    def _default_rules(self) -> List[ExclusionRule]:
        return [
            ExclusionRule(
                rule_id="EX-001", name="观察期",
                description="进群<7天，标记观察期",
                severity="soft",
                condition_fn="join_days < 7",
                penalty=15.0,
            ),
            ExclusionRule(
                rule_id="EX-002", name="沉默用户",
                description="进群>30天从未发言",
                severity="soft",
                condition_fn="join_days > 30 and msg_total == 0",
                penalty=25.0,
            ),
            ExclusionRule(
                rule_id="EX-003", name="长尾沉默",
                description="进群>90天无购买记录",
                severity="hard",
                condition_fn="join_days > 90 and has_purchased == 0",
            ),
            ExclusionRule(
                rule_id="EX-004", name="区域不符",
                description="城市不在300城目标范围",
                severity="hard",
                condition_fn="city_match == 0",
            ),
            ExclusionRule(
                rule_id="EX-005", name="低活跃僵尸",
                description="近30天消息<5条且无购买",
                severity="soft",
                condition_fn="msg_last_30d < 5 and has_purchased == 0",
                penalty=20.0,
            ),
            ExclusionRule(
                rule_id="EX-006", name="疑似马甲",
                description="新账号(<3天)且多群重复昵称",
                severity="hard",
                condition_fn="join_days < 3",
            ),
        ]

    def evaluate(self, user_data: Dict) -> Dict:
        """对单个用户执行全量排除规则评估
        
        Args:
            user_data: 用户特征字典, 含 join_days/msg_total/has_purchased 等字段
        
        Returns:
            {
                "excluded": bool,          # 是否被硬排除
                "triggers": List[str],     # 触发的规则ID列表
                "penalty": float,          # soft规则累计扣分
                "details": List[Dict],     # 每条规则触发详情
            }
        """
        triggers = []
        details = []
        total_penalty = 0.0
        hard_excluded = False

        for rule in self.rules:
            try:
                # 安全eval — 只允许访问user_data字典
                triggered = eval(rule.condition_fn, {"__builtins__": {}}, user_data)
            except:
                triggered = False

            if triggered:
                triggers.append(rule.rule_id)
                details.append({
                    "rule_id": rule.rule_id,
                    "name": rule.name,
                    "severity": rule.severity,
                    "penalty": rule.penalty,
                })
                if rule.severity == "hard":
                    hard_excluded = True
                else:
                    total_penalty += rule.penalty

        return {
            "excluded": hard_excluded,
            "triggers": triggers,
            "penalty": round(total_penalty, 1),
            "details": details,
        }

    def batch_evaluate(self, users: List[Dict]) -> List[Dict]:
        """批量评估"""
        return [self.evaluate(u) for u in users]
