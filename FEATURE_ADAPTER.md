# AI数字名片 · 芯森态Feature适配说明

## 已注入的Feature

| Feature | 源文件 | 适配状态 |
|---------|--------|----------|
| BGE嵌入引擎 | services/embedding_service.py | ✅ 可直接调用 |
| RBAC权限系统 | services/rbac_service.py + routers/rbac_router.py | ✅ 路由已注册(/api/admin/roles) |
| 支付订阅骨架 | services/payment_service.py | ✅ 可对接已有wechat.py/alipay.py |
| 定价跟踪埋点 | services/pricing_service.py | ✅ 需注册路由 |
| 飞书告警通道 | services/monitor.py | ✅ 环境变量FEISHU_WEBHOOK |
| 完整认证系统 | Feature/完整认证系统.md | 📌 项目已有auth_jwt.py, 参考增强 |
| 数据质量检查 | scripts/data_quality_check.py | ✅ 定时任务 |
| 盖娅双向桥接 | scripts/gaia_to_xst_bridge.py | ✅ cron每6h |
| 前端模板系统 | Feature/前端模板系统.md | 📌 参考base.html重构 |

## 使用方式
```python
# 在任意路由中调用
from services.embedding_service import get_embedding_service
svc = get_embedding_service()
emb = svc.embed("客户名片描述")
```
