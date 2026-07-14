# 登录认证模块 · 问题诊断与最佳实践

> **日期**: 2026-07-14
> **分支**: feature/fix-login-auth-20260714
> **扫描范围**: 6个子模块 (小程序登录页/后端auth路由/Token存储/请求拦截器/游客模式/微信填充)
> **分析人**: 烛龙P8(后端) + 乘黄P9(前端) + 鲲鹏P9(架构)

---

## 一、架构总览

```
┌──────────────────────────────────────────────────┐
│                 小程序登录页                         │
│          pages/login/index.js + .wxml              │
│                                                    │
│   wx.getUserProfile() → 获取头像/昵称               │
│   wx.login() → 获取临时 code                        │
│   POST /api/auth/wx-mini-login { code, user_info }  │
└──────────────┬───────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────┐
│              request.js (统一请求层)                │
│  自动带 Bearer Token                              │
│  401 自动清除登录态 + 跳转登录页                    │
│  非0 code 自动 Toast 错误信息                       │
└──────────────┬───────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────┐
│              store.js (状态管理)                    │
│  setAuth(token, userInfo) → 持久化到Storage        │
│  checkLogin() → 检查+跳转                         │
│  logout() → 清除                                  │
└──────────────┬───────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────┐
│          后端 auth.py + auth_jwt.py                │
│                                                    │
│  POST /api/auth/register     手机号注册             │
│  POST /api/auth/login        手机号密码登录          │
│  POST /api/auth/wx-login     微信登录(Mock)         │
│  POST /api/auth/wx-mini-login 小程序登录             │
│  POST /api/auth/logout       登出                  │
│  GET /api/auth/me            当前用户信息            │
└──────────────────────────────────────────────────┘
```

---

## 二、已发现的问题（共7项）

### 问题1: 游客模式可绕过登录访问核心页面 [P1 - 安全]

| 维度 | 详情 |
|:-----|:------|
| **涉及的代码** | `login/index.js:216-218` + `index/index.js:69-78` |
| **根因分析** | `skipLogin()` 直接 `wx.switchTab` 到首页；首页 `onShow` 检查 `isLoggedIn` 为 false **但不重定向**，只不加载数据 |
| **影响范围** | 未登录用户可浏览首页/名片(我的)三个tab页面，虽然数据为空但页面结构暴露 |
| **攻击路径** | 打开小程序 → 点「暂不登录，先看看」→ 看到全UI界面 → 尝试访问未授权API |
| **修复方案** | ① 在 `app.js` 的 `onShow` 中添加全局登录守卫；② 或在首页 `onShow` 中添加 `!isLoggedIn → redirect to login` |
| **最佳实践** | **全局守卫优于页面级守卫** — 不要依赖每个页面自己检查登录态 |

### 问题2: Token明文持久化到微信Storage [P1 - 安全]

| 维度 | 详情 |
|:-----|:------|
| **涉及的代码** | `store.js:78` — `wx.setStorageSync('token', token)` |
| **风险** | 设备root/越狱后可提取Token进行会话劫持 |
| **影响范围** | 所有已登录用户 |
| **修复方案** | ① Token仅在内存中持有，冷启动时通过 `wx.login()` 重新获取；② 或使用微信加密存储；③ 设置Token短期过期 + 刷新机制 |
| **最佳实践** | **Token = 密码，不应明文持久化**。替代: 只存 `refresh_token` 在Storage，access_token 在内存 |

### 问题3: userInfo含PII明文持久化 [P2 - 安全]

| 维度 | 详情 |
|:-----|:------|
| **涉及的代码** | `store.js:79-81` — `wx.setStorageSync('userInfo', userInfo)` |
| **根因** | 用户信息(含手机号/邮箱/公司)完整对象明文存储在本地 |
| **修复方案** | 仅持久化非敏感字段(头像/昵称)，手机号/邮箱每次从API获取 |

### 问题4: 微信userInfo未传递给后端 [P1 - 功能Bug]

| 维度 | 详情 |
|:-----|:------|
| **涉及的代码** | `login/index.js:100-102` → `authApi.wxMiniLogin(code)` — 只传code不传userInfo |
| **根因** | `_handleLoginWithProfile(code, userInfo)` 获取了微信用户信息，但调用 `authApi.wxMiniLogin(code)` 时只传了code。后端 `WeChatMiniLogin` schema有 `user_info: Optional[dict] = None`，但因为从未传值，新用户创建时 `nickName` 和 `avatarUrl` 始终为空 |
| **影响** | 微信一键登录后，用户的头像和昵称不会被后端保存 → 新名片无头像/昵称 |
| **修复方案** | 登录页 + api.js 两处联合修复 |

**修复方案详情**:

```javascript
// login/index.js:101 — 将userInfo传给API
_handleLoginWithProfile(code, userInfo) {
    if (this.data.useRealApi) {
      authApi.wxMiniLogin(code, userInfo)  // ← 加上userInfo参数
      // ...
    }
}

// api.js:15-17 — 支持userInfo参数
wxMiniLogin(code, userInfo) {
    return post('/api/auth/wx-mini-login', { 
      code, 
      user_info: userInfo  // ← 将userInfo传给后端
    }, { noAuth: true })
},
```

### 问题5: 登录页用户协议/隐私政策仍是Toast占位 [P2 - 功能]

| 维度 | 详情 |
|:-----|:------|
| **涉及的代码** | `login/index.js:220-225` — `goAgreement()` / `goPrivacy()` 只弹Toast |
| **说明** | 之前在 `feature/fix-all-20260713` 分支上修复过创建了 `agreement/` 页面并改为 `wx.navigateTo`，但 **该分支未合并到 develop**，所以当前 develop 派生出的本分支仍是Toast占位 |
| **修复方案** | ① 创建 `pages/agreement/user/index.*` 和 `pages/agreement/privacy/index.*` 页面；② 将 `goAgreement`/`goPrivacy` 改为 `wx.navigateTo`；③ 在 `app.json` 注册页面路径 |

### 问题6: 模拟微信登录按钮仍存在 [P2 - 残留]

| 维度 | 详情 |
|:-----|:------|
| **涉及的代码** | `login/index.js:228-253` — `mockWechatLogin()` 函数 + WXML第27行按钮 |
| **说明** | 用户之前要求删除「模拟微信登录」按钮。但 develop 分支仍然保留。该按钮在真实小程序上线时是安全隐患——用户可能误点 |
| **修复方案** | 删除 `mockWechatLogin()` 函数体和WXML中的模拟按钮 |

### 问题7: checkLogin() 未被多数页面调用 [P2 - 架构]

| 维度 | 详情 |
|:-----|:------|
| **涉及的代码** | `store.js:96-102` — `checkLogin()` 仅在页面主动调用时才生效 |
| **根因** | 多数页面(platform/brochure/ai等)在 `onLoad`/`onShow` 中未调用 `checkLogin()` |
| **修复方案** | 通过 `app.js` 的页面路由钩子统一调用，或创建Page基类混入 |

---

## 三、修复优先级

### 🔴 Phase 1: 立即修复

| 优先级 | 问题 | 文件 | 预估工作量 |
|:------:|:-----|:-----|:----------:|
| **1** | [P1-Bug] userInfo未传递给后端 | `login/index.js` + `api.js` | 2行代码改 |
| **2** | [P1-安全] Token明文持久化 | `store.js` | 需重构Token策略 |
| **3** | [P2] 登录页协议/政策跳转 | `login/index.js` + 新建页面 | 4个文件创建 |

### 🟡 Phase 2: 两周内

| 优先级 | 问题 | 文件 | 预估工作量 |
|:------:|:-----|:-----|:----------:|
| **4** | [P1-安全] 游客模式绕过登录 | `app.js` / `index/index.js` | 1文件改 |
| **5** | [P2] 删除模拟登录按钮 | `login/index.js` + `.wxml` | 2处删 |
| **6** | [P2] userInfo含PII | `store.js` | 字段过滤 |
| **7** | [P2] checkLogin全局化 | `app.js` | 架构调整 |

---

## 四、最佳实践总结

### 4.1 小程序登录Token安全架构

```
冷启动：
  ┌──────────┐    ┌─────────────┐    ┌────────────┐
  │ 检测Storage │──→│ refresh_token │──→│ 调wx.login  │
  │ refresh_token│   │ 存在?        │    │ 换新token    │
  └──────────┘    └──────┬──────┘    └──────┬─────┘
                         │ 不存在             │
                         ▼                   ▼
                    ┌──────────┐       ┌──────────┐
                    │ 跳转登录页 │       │ 更新内存  │
                    └──────────┘       │ access_token│
                                       └──────────┘
```

### 4.2 三层登录守卫架构

```javascript
// 第1层: app.js 全局守卫（推荐）
// 在 app.onShow 或每个页面路由前检查
App({
  onShow() {
    this.checkGlobalAuth()
  },
  checkGlobalAuth() {
    const { isLoggedIn } = store.getState()
    const currentPage = getCurrentPages().pop()
    const publicPages = ['login']
    if (!isLoggedIn && !publicPages.includes(currentPage.route?.split('/')[1])) {
      wx.navigateTo({ url: '/pages/login/index' })
    }
  }
})

// 第2层: request.js 请求级守卫（已有）
// 401自动清除Token并跳转 —— 这层已实现 ✅

// 第3层: 后端JWT验证（已有）
// FastAPI Depends(get_current_user) —— 这层已实现 ✅
```

### 4.3 微信一键登录 → 自动填充名片的完整链路

```
用户点击「微信一键登录」
    ↓
wx.getUserProfile() → 获取 nickname + avatarUrl
    ↓
wx.login() → 获取 temp code
    ↓
POST /api/auth/wx-mini-login {
  code: "...",
  user_info: { nickName: "...", avatarUrl: "..." }  ← 关键：传user_info
}
    ↓
后端：查找或创建用户 ← 用 user_info.nickName 填充 name
    ↓
返回 JWT token + userInfo
    ↓
store.setAuth(token, userInfo)
    ↓
首页 onShow → loadPageData → GET /api/users/me
    ↓
显示用户头像 + 昵称 ✅
```

### 4.4 演进路线：从开发到生产

| 阶段 | 登录认证策略 | 说明 |
|:----:|:------------|:------|
| 开发 | Mock登录 + wx.login降级 | 现在已实现 |
| 演示 | useRealApi=true + userInfo传递 | Phase 1修复后 |
| 上线 | 真实微信AppID + Token内存持有 | Phase 2安全加固后 |
| 成熟 | refresh_token + 加密Storage | 架构优化 |

---

## 五、后续分步执行计划

完成本分析后，若您同意修复方案：

1. **修复 Phase 1 (3项)** — 我并行派出烛龙P8(后端) + 乘黄P9(前端)
2. **验收** — 您走查每个修复
3. **进入 Phase 2** — 安全加固

**每次修复提交到分支**: `feature/fix-login-auth-20260714`
**完成后合并到**: `develop`
