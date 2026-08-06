# API版本规范

## 版本前缀
- `/api/v1/` — 当前稳定版本（全部路由使用）
- 新路由必须注册在 `/api/v1/` 下
- 历史路由 `/api/xxx` 由APIVersionRedirectMiddleware自动重写

## 废弃策略
1. 标记 deprecated header
2. 保留兼容6个月
3. 移除后返回410 Gone
