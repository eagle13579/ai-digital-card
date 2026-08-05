"""
模型注册表 — 每个模型需要的训练管道配置
P0-P3优先级分层，与数据源双向索引
"""
import os
import json
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional

MODEL_REGISTRY_PATH = os.path.join(os.path.dirname(__file__), "model_registry.json")


@dataclass
class ModelTrainingConfig:
    """单个模型的训练管道配置"""
    model_id: str                                 # 唯一ID
    name: str                                     # 中文名
    priority: str                                 # P0/P1/P2/P3
    training_type: str                            # online/offline_batch/self_supervised/evolution
    data_sources: List[str]                       # 依赖的数据源ID（对应data_source_registry）
    train_script: str                             # 训练脚本路径
    model_file: str                               # 产出模型文件路径
    frequency_min: int                            # 训练频率（分钟）
    max_staleness_hours: int                      # 最大数据陈旧容忍
    auto_mode: str = "full_auto"                  # full_auto / semi_auto / manual
    enabled: bool = True
    last_trained: Optional[str] = None
    observability: Dict = field(default_factory=lambda: {
        "health_check": "",
        "alert_on_failure": True,
        "metrics_export": True
    })


class ModelRegistry:
    """统一模型注册表 — 管理所有需要真实数据训练的模型"""

    def __init__(self, path: Optional[str] = None):
        self.path = path or MODEL_REGISTRY_PATH
        self._models: Dict[str, ModelTrainingConfig] = {}
        self._load()

    def _load(self):
        """从JSON加载注册表"""
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for mid, cfg in data.get("models", {}).items():
                self._models[mid] = ModelTrainingConfig(**cfg)

    def save(self):
        """持久化到JSON"""
        data = {
            "_meta": {
                "version": "1.0.0",
                "description": "模型训练管道注册表 — 每个模型与数据源/训练脚本的映射",
                "last_updated": "2026-07-25"
            },
            "models": {mid: asdict(cfg) for mid, cfg in self._models.items()}
        }
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def register(self, cfg: ModelTrainingConfig):
        """注册一个模型"""
        self._models[cfg.model_id] = cfg
        self.save()

    def get(self, model_id: str) -> Optional[ModelTrainingConfig]:
        return self._models.get(model_id)

    def list_by_priority(self, priority: str) -> List[ModelTrainingConfig]:
        """按优先级列出"""
        return [m for m in self._models.values() if m.priority == priority]

    def list_by_source(self, source_id: str) -> List[ModelTrainingConfig]:
        """列出依赖某个数据源的所有模型"""
        return [m for m in self._models.values() if source_id in m.data_sources]

    def all(self) -> List[ModelTrainingConfig]:
        return list(self._models.values())

    def get_priority_order(self) -> List[ModelTrainingConfig]:
        """按P0→P3排序"""
        order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
        return sorted(self._models.values(), key=lambda m: order.get(m.priority, 99))


# ===== 默认注册表 =====
_DEFAULT_MODELS = [
    # ─── P0: 爬虫直驱，最快见效 ───
    ModelTrainingConfig(
        model_id="matching_model_v2",
        name="名片匹配模型v2",
        priority="P0",
        training_type="offline_batch",
        data_sources=["enterprise_websites", "url_batch_crawler", "crm_matching_data"],
        train_script="scripts/train_matching_model_v2.py",
        model_file="models/matching_model_v2.pt",
        frequency_min=360,
        max_staleness_hours=24,
    ),
    ModelTrainingConfig(
        model_id="matching_model_v2_mac",
        name="名片匹配模型v2 (Mac MPS)",
        priority="P0",
        training_type="offline_batch",
        data_sources=["enterprise_websites", "url_batch_crawler", "crm_matching_data"],
        train_script="scripts/train_matching_model_v2_mac_mps.py",
        model_file="models/matching_model_v2_mac.pt",
        frequency_min=360,
        max_staleness_hours=24,
    ),
    ModelTrainingConfig(
        model_id="prepare_v2_training_data",
        name="V2训练数据准备",
        priority="P0",
        training_type="offline_batch",
        data_sources=["enterprise_websites", "url_batch_crawler", "xiaohongshu"],
        train_script="scripts/prepare_v2_training_data.py",
        model_file="data/v2_training_data.json",
        frequency_min=120,
        max_staleness_hours=12,
    ),
    ModelTrainingConfig(
        model_id="user_tower_pretrained",
        name="用户塔预训练",
        priority="P0",
        training_type="offline_batch",
        data_sources=["enterprise_websites", "qichacha", "crm_matching_data"],
        train_script="scripts/pretrain_user_tower.py",
        model_file="data/models/user_tower_pretrained.pt",
        frequency_min=720,
        max_staleness_hours=72,
    ),
    ModelTrainingConfig(
        model_id="data_augmentation",
        name="数据增强管道",
        priority="P0",
        training_type="offline_batch",
        data_sources=["enterprise_websites", "qichacha", "xiaohongshu"],
        train_script="scripts/data_augmentation.py",
        model_file="data/augmented_dataset.json",
        frequency_min=240,
        max_staleness_hours=48,
    ),
    ModelTrainingConfig(
        model_id="enhance_user_data",
        name="用户数据增强",
        priority="P0",
        training_type="offline_batch",
        data_sources=["enterprise_websites", "qichacha", "url_batch_crawler"],
        train_script="scripts/enhance_user_data.py",
        model_file="data/enhanced_user_data.json",
        frequency_min=240,
        max_staleness_hours=48,
    ),
    ModelTrainingConfig(
        model_id="training_data_generator",
        name="训练数据生成器",
        priority="P0",
        training_type="offline_batch",
        data_sources=["url_batch_crawler", "baidu_search"],
        train_script="app/services/training_data_generator.py",
        model_file="data/training_data.json",
        frequency_min=120,
        max_staleness_hours=12,
    ),

    # ─── P1: 用户行为+爬虫混合 ───
    ModelTrainingConfig(
        model_id="online_learning",
        name="在线学习引擎",
        priority="P1",
        training_type="online",
        data_sources=["user_behavior_feedback", "crm_matching_data", "xiaohongshu"],
        train_script="app/ai/online_learning.py",
        model_file="data/online_weights.json",
        frequency_min=30,
        max_staleness_hours=2,
    ),
    ModelTrainingConfig(
        model_id="gaia_trainer",
        name="Gaia训练器",
        priority="P1",
        training_type="offline_batch",
        data_sources=["user_behavior_feedback", "knowledge_base", "baidu_search"],
        train_script="app/ai/gaia_trainer.py",
        model_file="data/models/gaia_weights.json",
        frequency_min=360,
        max_staleness_hours=24,
    ),
    ModelTrainingConfig(
        model_id="gaia_evolution_brain",
        name="Gaia进化脑",
        priority="P1",
        training_type="evolution",
        data_sources=["user_behavior_feedback", "baidu_search", "crm_matching_data"],
        train_script="app/ai/gaia_evolution_brain.py",
        model_file="data/evolution_state.json",
        frequency_min=60,
        max_staleness_hours=6,
    ),
    ModelTrainingConfig(
        model_id="recommendation",
        name="推荐引擎",
        priority="P1",
        training_type="online",
        data_sources=["user_behavior_feedback", "xiaohongshu", "baidu_search"],
        train_script="app/ai/recommendation.py",
        model_file="data/recommendation_weights.json",
        frequency_min=30,
        max_staleness_hours=2,
    ),
    ModelTrainingConfig(
        model_id="bandit_engine",
        name="多臂赌博机引擎",
        priority="P1",
        training_type="online",
        data_sources=["user_behavior_feedback", "crm_matching_data"],
        train_script="app/ai/bandit_engine.py",
        model_file="data/bandit_state.json",
        frequency_min=15,
        max_staleness_hours=1,
    ),

    # ─── P2: 知识/关系/批量训练 ───
    ModelTrainingConfig(
        model_id="sales_prediction",
        name="销售预测模型",
        priority="P2",
        training_type="offline_batch",
        data_sources=["crm_matching_data", "qichacha", "enterprise_websites"],
        train_script="app/services/sales_prediction.py",
        model_file="data/sales_prediction_model.json",
        frequency_min=1440,
        max_staleness_hours=168,
    ),
    ModelTrainingConfig(
        model_id="model_absorb_daemon",
        name="模型吸收守护进程",
        priority="P2",
        training_type="self_supervised",
        data_sources=["web_pages_rag", "knowledge_base"],
        train_script="../gaia-commercial/scripts/model_absorb_daemon.py",
        model_file="../gaia-commercial/data/absorbed_models/",
        frequency_min=1440,
        max_staleness_hours=168,
    ),
    ModelTrainingConfig(
        model_id="rag_pipeline",
        name="RAG知识管道",
        priority="P2",
        training_type="self_supervised",
        data_sources=["web_pages_rag", "xiaohongshu", "knowledge_base"],
        train_script="app/ai/rag_pipeline.py",
        model_file="data/rag_index/",
        frequency_min=120,
        max_staleness_hours=24,
    ),

    # ─── P3: 支撑性/架构级 ───
    ModelTrainingConfig(
        model_id="embedding_service",
        name="向量嵌入服务",
        priority="P3",
        training_type="self_supervised",
        data_sources=["web_pages_rag", "knowledge_base"],
        train_script="app/ai/embedding_service.py",
        model_file="data/embeddings/",
        frequency_min=720,
        max_staleness_hours=168,
    ),
    ModelTrainingConfig(
        model_id="knowledge_graph",
        name="知识图谱引擎",
        priority="P3",
        training_type="self_supervised",
        data_sources=["knowledge_base", "enterprise_websites", "web_pages_rag"],
        train_script="app/ai/knowledge_graph.py",
        model_file="data/knowledge_graph/",
        frequency_min=1440,
        max_staleness_hours=336,
    ),
]


def init_default_registry(path: Optional[str] = None):
    """初始化默认注册表"""
    reg = ModelRegistry(path)
    for model in _DEFAULT_MODELS:
        reg.register(model)
    return reg


if __name__ == "__main__":
    reg = init_default_registry()
    print(f"✅ 模型注册表已初始化: {len(reg.all())} 个模型")
    for p in ["P0", "P1", "P2", "P3"]:
        models = reg.list_by_priority(p)
        print(f"  {p}: {len(models)} 个模型")
        for m in models:
            print(f"    - {m.model_id} ({m.name}) 频率:{m.frequency_min}min 数据源:{len(m.data_sources)}个")
