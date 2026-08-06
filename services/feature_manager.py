"""
芯森态 Feature管理中心
自动扫描Feature/目录 + 健康检查 + API路由
用法: from feature_manager import FeatureRegistry
"""
import json, logging, os, sys
from datetime import datetime

logger = logging.getLogger("feature_manager")

class FeatureRegistry:
    """全局Feature注册表 - 自动发现+健康检查"""

    def __init__(self, features_dir=None):
        self.features = {}
        self._scan(features_dir)

    def _scan(self, features_dir):
        """扫描Feature/目录注册所有Feature"""
        if not features_dir:
            # 自动从调用栈找项目根
            frame = sys._getframe(2)
            f_back = frame.f_back
            proj = os.path.dirname(os.path.dirname(os.path.abspath(f_back.f_code.co_filename)))
            features_dir = os.path.join(proj, "Feature")
        
        if not os.path.exists(features_dir):
            logger.warning("Feature目录不存在: %s", features_dir)
            return
        
        for f in sorted(os.listdir(features_dir)):
            if not f.endswith('.md'): continue
            fpath = os.path.join(features_dir, f)
            name = f.replace('.md', '')
            try:
                with open(fpath, 'r', encoding='utf-8') as fh:
                    content = fh.read()
                # Parse YAML frontmatter
                import re
                m = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
                meta = {}
                if m:
                    for line in m.group(1).split('\n'):
                        if ':' in line:
                            k, v = line.split(':', 1)
                            meta[k.strip()] = v.strip()
                
                self.features[name] = {
                    "name": meta.get("name", name),
                    "version": meta.get("version", "0.0.0"),
                    "status": meta.get("status", "unknown"),
                    "file": fpath,
                    "size": os.path.getsize(fpath),
                    "loaded": True,
                }
            except Exception as e:
                self.features[name] = {"name": name, "status": "error", "error": str(e)}
        
        logger.info("FeatureRegistry: %d features loaded from %s", len(self.features), features_dir)

    def list(self):
        """列出所有Feature"""
        return [{"id": k, **v} for k, v in self.features.items()]

    def get(self, name):
        return self.features.get(name)

    def check_dependencies(self, name):
        """检查Feature的依赖是否可用"""
        feature = self.features.get(name)
        if not feature: return {"available": False, "reason": "not_found"}
        
        # 检查对应的Python模块是否可导入
        svc_name = feature.get("name", "")
        module_map = {
            "BGE嵌入引擎": "embedding_service",
            "RBAC权限系统": "rbac_service",
            "支付订阅骨架": "payment_service",
            "定价跟踪埋点": "pricing_service",
            "飞书告警通道": "monitor",
            "数据质量检查": "data_quality_check",
        }
        mod_name = None
        for k, v in module_map.items():
            if k in svc_name or svc_name in k:
                mod_name = v
                break
        
        if mod_name:
            try:
                __import__(mod_name)
                return {"available": True, "module": mod_name}
            except ImportError:
                return {"available": False, "reason": f"module {mod_name} not importable"}
        
        return {"available": True, "reason": "documentation_only"}

# 单例
_registry = None

def get_registry(features_dir=None):
    global _registry
    if _registry is None:
        _registry = FeatureRegistry(features_dir)
    return _registry
