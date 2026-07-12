# 战狼红队安全攻击报告

**项目**: AI数智名片 - 微信小程序 + FastAPI后端
**日期**: 2026-07-12
**范围**: D:\AI数智名片\miniapp\ (前端) + D:\AI数智名片\backend\ (后端FastAPI)
**严重度分级**: P0=紧急, P1=高危, P2=中危

---

## WR-009 敏感信息泄露

### [P1] 硬编码内网IP地址和端口
**文件**: `utils/request.js:20-21`
```
const DEV_IP = '192.168.7.48'   // 后端服务器IP
const DEV_PORT = '8201'          // AI数智名片后端端口
```
同时在 `README.md:31-33` 和 `docs/环境切换指南.md:46、55-57` 中重复暴露。
**修复建议**: 将服务器IP/端口移至环境变量或配置文件，不在源码中硬编码；README文档中使用占位符如 `{SERVER_IP}`。

### [P2] 硬编码测试用户PII信息
**文件**: `utils/test-data.js:6-51`（多处）
硬编码了3个测试用户的姓名、手机号（`13800138000`、`13900139000`、`13700137000`）、邮箱（`zhangwei@example.com`等）、微信号。
同样出现在 `utils/preview.test.js:84-86` 和 `pages/brochure/preview/index.js:111-113`。
**修复建议**: 测试数据从环境变量或配置文件加载，不在源码中硬编码真实格式的PII数据。

### [P2] 硬编码字节跳动内网API地址
**文件**: `utils/test-data.js`（89处引用）
```
avatar: 'https://neeko-copilot.bytedance.net/api/text2image?prompt=...'
```
**修复建议**: 替换为占位URL或本地资源，删除对内部API的引用。

### [P2] .env.bak 包含敏感配置模板
**文件**: `backend/.env.bak`
```
DEEPSEEK_API_KEY=your-deepseek-api-key
JWT_SECRET=change-this-to-a-secure-random-secret-key-ai-digital-card
```
**修复建议**: 从版本控制中移除 `.env.bak`，添加到 `.gitignore`；生产环境密钥使用密钥管理服务。

---

## WR-015 小程序存储安全

### [P1] Token明文持久化到Storage
**文件**: `utils/store.js:75`
```javascript
wx.setStorageSync('token', token)
```
Token通过 `wx.setStorageSync` 以明文持久化到微信本地存储。如果设备被root/越狱或有恶意应用，Token可被提取并进行会话劫持。
**修复建议**: 
- Token仅在内存中持有，小程序冷启动时通过 `wx.login()` 重新获取
- 或使用微信 `wx.setStorage` 的加密存储（配合自定义加密）
- 设置Token过期时间，后端实现Token轮换

### [P2] userInfo包含PII明文持久化
**文件**: `utils/store.js:77`
```javascript
wx.setStorageSync('userInfo', userInfo)
```
用户信息（含手机号、邮箱、公司等）明文存储在本地。
**修复建议**: 限制持久化的userInfo字段，仅存储非敏感信息（如头像、昵称），手机号/邮箱等敏感字段每次从API获取。

### [P2] 聊天记录明文持久化
**文件**: `pages/ai/chat/index.js:51`
```javascript
wx.setStorageSync(CHAT_STORAGE_KEY, this.data.messages)
```
AI对话历史明文存储在本地。
**修复建议**: 对聊天记录进行加密后再持久化，或提供自动清除机制（如24小时后自动清除）。

---

## WR-016 认证绕过

### [P1] 游客模式可绕过登录访问核心功能
**文件**: `pages/login/index.js:122-124`
```javascript
skipLogin() {
    wx.switchTab({ url: '/pages/index/index' })
}
```
用户点击"暂不登录，先看看"可直接跳过登录进入首页。首页 `pages/index/index.js:40-46` 的 `onShow` 虽然检查 `isLoggedIn`，但**不进行重定向**——仅在有登录态时加载数据，未登录时显示空页面。
**影响**: 未登录用户可以浏览所有tab页面（首页、名片、我的），虽然数据为空但页面结构暴露。
**修复建议**: 
- 在 `app.js` 的 `onShow` 中添加全局登录态检查，未登录跳转到登录页
- 或明确设计"游客模式"并限制游客可访问的功能

### [P2] checkLogin()可被绕过
**文件**: `utils/store.js:93-99`
```javascript
checkLogin() {
    if (!this._state.isLoggedIn) {
        wx.navigateTo({ url: '/pages/login/index' })
        return false
    }
    return true
}
```
`checkLogin` 仅在页面代码主动调用时才生效。多数页面在 `onLoad`/`onShow` 中未调用此方法。
**修复建议**: 在基类Page或 `app.js` 的页面路由钩子中统一进行登录态检查。

---

## WR-017 开放API/服务发现

### [P1] 多个敏感端点无需认证即可访问
**文件**: `backend/app/__init__.py:266-292`

后端暴露了以下未认证端点：

| 端点 | 路径 | 风险 |
|------|------|------|
| 健康检查 | `GET /health` | 服务状态信息泄露 |
| API健康检查 | `GET /api/health` | 服务状态信息泄露 |
| Prometheus指标 | `GET /metrics` | 泄露请求量、延迟、业务指标等运营数据 |
| Swagger文档 | `GET /docs` | 完整API文档，包含所有端点、参数、数据模型 |
| OpenAPI规范 | `GET /api/openapi.yaml` | 完整API规范文件 |
| 变更日志 | `GET /api/changelog` | 版本历史暴露 |
| GraphQL | `/graphql` | GraphQL API端点（如果启用） |
| 公开画册查看 | `GET /view/{share_token}` | 公开页面 |
| 公开用户主页 | `GET /u/{username}` | 公开用户页面 |

**修复建议**:
- `/metrics` 应限制为内网访问或使用API密钥认证
- `/docs` 在生产环境禁用（设置 `docs_url=None`）
- `/api/openapi.yaml` 和 `/api/changelog` 需要认证
- 在生产环境文档端点上添加IP白名单

### [P2] admin端点路径暴露
**文件**: `backend/app/routers/admin.py:31-101`
```
GET /admin/users
GET /admin/users/{user_id}
PATCH /admin/users/{user_id}
GET /admin/brochures
GET /admin/stats
GET /admin/audit-log
```
虽然使用AdminDep依赖进行权限控制，但端点路径暴露了管理后台API结构。
**修复建议**: 管理端点使用独立域名或路径前缀混淆；增加登录尝试限制和异常告警。

---

## WR-018 前端安全反模式

### [P2] 用户可控数据直接用于image src属性
**文件**: 
- `pages/brochure/preview/index.wxml:35` — `<image src="{{page.avatar}}"`
- `pages/brochure/preview/index.wxml:117` — `<image src="{{item}}">`（公司图片）
- `pages/brochure/preview/index.wxml:127` — `<image src="{{item}}">`（案例图片）
- `components/network-mini-map/index.wxml:9、21` — `src="{{item.avatar}}"`
- `pages/ai/chat/index.wxml:10` — `src="{{userAvatar}}"`

如果API返回恶意URL（如 `javascript:` 协议或SSRF目标），可能导致XSS（虽然微信小程序对`image`标签有保护）或SSRF攻击。
**修复建议**: 
- 对用户上传/可控的图片URL进行协议和白名单验证（仅允许 `https://`）
- 后端对图片URL进行代理中转，不直接返回用户URL

### [P2] 用户输入内容直接渲染到WXML
**文件**: 
- `pages/brochure/preview/index.wxml:40-41` — `{{page.title}}` `{{page.subtitle}}`
- `pages/brochure/preview/index.wxml:56-58` — `{{page.name}}` `{{page.title}}` `{{page.company}}`
- `pages/ai/chat/index.wxml:12` — `{{item.content}}`
- `pages/card/card.wxml:15-17` — `{{card.user_name}}` `{{card.user_company}}` `{{card.title}}`

微信小程序WXML的 `{{}}` 插值会进行HTML实体转义，降低了传统XSS风险。但微信小程序支持 `rich-text` 组件，如果未来迁移到 `rich-text` 且未正确处理，可能导致XSS。
**修复建议**: 避免使用 `rich-text` 渲染用户输入；如需富文本渲染，使用消毒库清理HTML。

### [P2] BFS路径搜索接受用户ID输入无校验
**文件**: `pages/network/graph/index.js:362-364`
```javascript
onTargetInput(e) {
    this.setData({ targetUserId: e.detail.value })
}
```
`searchPath()` (index.js:374) 直接将用户输入的ID传给后端 `findPath` 调用。
**修复建议**: 前端添加输入校验（格式/长度），后端实现速率限制和用户存在性检查。

---

## 汇总统计

| 漏洞编号 | 严重度 | 发现数量 |
|----------|--------|----------|
| WR-009 敏感信息泄露 | P1(1), P2(3) | 4 |
| WR-015 存储安全 | P1(1), P2(2) | 3 |
| WR-016 认证绕过 | P1(1), P2(1) | 2 |
| WR-017 开放API | P1(1), P2(1) | 2 |
| WR-018 前端安全 | P2(3) | 3 |

**总计**: P0=0, P1=3, P2=10

**最高优先级修复**:
1. Token明文存储 → 改为内存持有
2. 游客模式可跳过登录 → 添加全局登录检查
3. 后端敏感端点（/metrics, /docs）→ 生产环境禁用/加认证
