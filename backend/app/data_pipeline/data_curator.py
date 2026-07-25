"""
数据治理层 — 去重 + 标准化 + 质量控制
"""
import os
import json
import hashlib
import datetime
from typing import Dict, List, Optional, Any

CURATOR_STATE_PATH = os.path.join(os.path.dirname(__file__), ".data_curator_state.json")


class DataCurator:
    """数据治理器：去重 + 标准化 + 质量控制"""

    def __init__(self):
        self._seen_hashes: Dict[str, float] = {}
        self._load_state()

    def _load_state(self):
        if os.path.exists(CURATOR_STATE_PATH):
            with open(CURATOR_STATE_PATH, "r", encoding="utf-8") as f:
                self._seen_hashes = json.load(f)

    def _save_state(self):
        os.makedirs(os.path.dirname(CURATOR_STATE_PATH), exist_ok=True)
        with open(CURATOR_STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(self._seen_hashes, f, indent=2)

    def compute_hash(self, data: dict) -> str:
        """基于关键字段计算数据指纹"""
        key_fields = {}
        for field in ["url", "title", "content", "name", "company", "business_id"]:
            if field in data:
                key_fields[field] = data[field]
        raw = json.dumps(key_fields, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(raw.encode("utf-8")).hexdigest()

    def is_duplicate(self, data: dict, window_minutes: int = 60) -> bool:
        """检查是否重复（窗口期内）"""
        h = self.compute_hash(data)
        now = datetime.datetime.utcnow().timestamp()
        if h in self._seen_hashes:
            age = (now - self._seen_hashes[h]) / 60
            if age < window_minutes:
                return True
        self._seen_hashes[h] = now
        self._save_state()
        return False

    def normalize_enterprise(self, raw: dict) -> dict:
        """标准化企业数据"""
        return {
            "name": raw.get("name", raw.get("company", "")),
            "industry": raw.get("industry", raw.get("行业", "")),
            "description": raw.get("description", raw.get("简介", "")),
            "tags": raw.get("tags", raw.get("标签", [])),
            "url": raw.get("url", ""),
            "contacts": raw.get("contacts", raw.get("联系方式", {})),
            "source": raw.get("source", "web"),
            "collected_at": datetime.datetime.utcnow().isoformat(),
            "confidence": raw.get("confidence", 0.5),
        }

    def normalize_user_behavior(self, raw: dict) -> dict:
        """标准化用户行为数据"""
        return {
            "user_id": raw.get("user_id", ""),
            "target_id": raw.get("target_id", raw.get("item_id", "")),
            "event_type": raw.get("event_type", raw.get("feedback_type", "rating")),
            "value": float(raw.get("value", raw.get("score", 0))),
            "timestamp": raw.get("timestamp", datetime.datetime.utcnow().isoformat()),
            "source": raw.get("source", "feedback"),
        }

    def batch_process(self, items: List[dict], source_type: str = "enterprise") -> tuple:
        """
        批量处理数据
        返回: (valid_items, duplicates_count, error_count)
        """
        valid = []
        dup_count = 0
        err_count = 0

        normalizer = {
            "enterprise": self.normalize_enterprise,
            "user_behavior": self.normalize_user_behavior,
        }.get(source_type, lambda x: x)

        for item in items:
            try:
                normalized = normalizer(item)
                if not self.is_duplicate(normalized):
                    valid.append(normalized)
                else:
                    dup_count += 1
            except Exception:
                err_count += 1

        return valid, dup_count, err_count

    def get_stats(self) -> dict:
        """获取治理统计"""
        return {
            "total_unique_records": len(self._seen_hashes),
            "oldest_record_hours": self._get_oldest_age(),
        }

    def _get_oldest_age(self) -> float:
        if not self._seen_hashes:
            return 0
        now = datetime.datetime.utcnow().timestamp()
        oldest = min(self._seen_hashes.values())
        return (now - oldest) / 3600


# 单例
_curator_instance: Optional[DataCurator] = None


def get_curator() -> DataCurator:
    global _curator_instance
    if _curator_instance is None:
        _curator_instance = DataCurator()
    return _curator_instance
