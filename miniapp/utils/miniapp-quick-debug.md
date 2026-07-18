---
name: miniapp-quick-debug
version: 1.0.0
author: 白泽 (Bai Ze) — 向海容签署
category: software-development
description: '微信小程序极简Debug自查流程 — 三问定位 + MECE四层排查 + 三板斧修复。
  遇到Bug不知道从哪入手时，先走这个流程，再决定要不要上报。
  触发条件: 用户说「出bug了」「报错了」「不知道怎么办」「白屏」「404」「打不开」'
tags:
- debug
- miniapp
- troubleshooting
- quick-fix
- mece
trigger_phrases:
- 出bug了
- 报错了
- 不知道怎么办
- 该怎么办
- 怎么检查
- 如何排查
- 白屏
- 打不开
- 卡住了
- 报错
- 不知道怎么修
- debug
- 排查
- 控制台报错
- 页面空白
- 网络连接失败
- 请求失败
- 404
- 500
- reach the max redirect count
- redirectTo循环
iron_law_ref: 向海容签署 · 2026-07-16 · 九步法引擎Step 2 RAG自动匹配
---

# 🕵️ 小程序 Debug 极简自查流程

> **九步法引擎集成说明**：每次用户报告Bug时，九步法引擎Step 2（三通道）的RAG
> 会匹配本skill。加载后按此流程排查。如果已知道根因，直接修复并跳至Step 5。
> 如果不知道根因，按第3节「MECE四层排查」逐步排除。

---

## 1️⃣ Debug 三问（第1步：定位「在哪断的」）

无论什么Bug，先回答这3个问题。回答完80%能定位方向：

| # | 问题 | 目的 |
|:-:|:-----|:-----|
| ① | **在哪个页面发生的？** | 缩小到单个文件 |
| ② | **做了什么操作之后发生的？** | 缩小到单个事件处理函数 |
| ③ | **控制台有没有红字？** | 缩小到单个报错行 |

如果用户说不上来 → 告诉他打开 DevTools → Console 看一眼。

**禁止替代**：不要跳过这三问直接猜根因。除非用户已明确告诉了你①②③。

---

## 2️⃣ 常见 Bug 模式速查（第2步：模式匹配）

Bug报告来了，先匹配已知模式。匹配上了直接修，不用走完整排查。

### 模式A：「reach the max redirect count」

**症状**: 切 Tab/跳转时报错，点几次就崩
**根因**: Tab页 `onShow` 中有 `redirectTo`，每次切Tab累积一次，超过10次触发微信限制
**修复**: 移除 Tab页 `onShow` 中的 `redirectTo`。`onLoad` 守卫保留

```javascript
// ❌ 错误 — 每次onShow都redirectTo
onShow() {
  if (!isLoggedIn) {
    wx.redirectTo({ url: '/pages/login/index' })  // 每次切Tab触发！
  }
}

// ✅ 正确 — onLoad守卫就够了
onLoad() {
  if (!isLoggedIn) {
    wx.redirectTo({ url: '/pages/login/index' })
    return
  }
}
```

### 模式B：「页面白屏/无内容」

**症状**: 页面打开后一片空白，无JS报错
**根因**:
- B1: API 返回 401 → request.js 自动跳登录页 → 登录页无数据处理
- B2: MockService 返回空但 useRealApi=false → 桥接层没调真实API
- B3: USE_MOCK=true 阻塞真实API → 数据全是Mock空值

**修复**:
```javascript
// 检查USE_MOCK
grep -n "USE_MOCK" utils/mockService.js

// 检查useRealApi
grep -n "useRealApi" pages/xxx/index.js
```

### 模式C：「API 返回 403/401」

**症状**: 请求报 401/403
**根因**:
- C1: token 过期/不存在 → 重新登录
- C2: post请求没传 Authorization header → 检查 request.js
- C3: 后端 auth middleware 拦截了无需认证的接口 → 确认路由是否需 auth

**排查**:
```bash
# 检查接口是否需要auth
curl -s http://localhost:8201/api/xxx | python -c "import sys,json;print(json.load(sys.stdin))"
# 复现: 加上Bearer token再试
curl -s -H "Authorization: Bearer TOKEN" http://localhost:8201/api/xxx
```

### 模式D：「编译后页面没变化」

**症状**: 改了代码，编译后和之前一样
**根因**:
- D1: 只改了后端没上传小程序
- D2: 改了文件但 DevTools 缓存没清（工具→清除缓存→全部）
- D3: compileHotReLoad=true → 新增页面不识别

**修复**:
```bash
# 先确认：改的是 miniapp/ 还是 backend/？
# miniapp/ → 必须上传小程序代码
# backend/ → 只改后端，前端没变化是正常的
```

### 模式E：「打开页面跳到不该去的页面」

**症状**: 打开页面A，自动跳到页面B
**根因**:
- E1: 目标页的 `onLoad` 中有条件跳转
- E2: request.js 收到 401 → store.logout() → redirectTo(login)
- E3: app.js onShow 中守卫跳转

**排查**:
```bash
# 搜索目标页的所有跳转API
grep -n "redirectTo\|navigateTo\|switchTab\|reLaunch" pages/target/index.js
```

---

## 3️⃣ MECE 四层排查（第3步：系统化排除）

三问+模式匹配后还不知道根因，按此顺序逐层排除。**严禁跳层**。

```
Layer A: 网络层 (30秒)
  → DevTools → Network → 看哪个请求红了
  → 或: curl http://localhost:8201/api/xxx

Layer B: 前端层 (1分钟)
  → DevTools → Console → 看红字报错
  → 看报错的文件名、行号、错误信息

Layer C: 后端层 (1分钟)
  → curl http://localhost:8201/health  (服务活着吗？)
  → curl http://localhost:8201/api/xxx (接口能调通吗？)

Layer D: 数据层 (2分钟)
  → curl 返回的数据结构对不对？
  → 数据库里有数据吗？
  → 前端WXML绑定字段匹配吗？
```

### 排查戒律

```text
□ 不猜：每个排查步骤必须能验证
□ 不跳：A→B→C→D顺序排，不能跳过A直接D
□ 不假设：验证前不要下结论
□ 不安排用户干活：能自己查的就自己查，只留「点一下编译」这类操作给用户
```

---

## 4️⃣ 三板斧修复（第4步：常见修复操作）

定位到根因后，90%的场景用这三招：

| 招数 | 适用场景 | 操作 |
|:----|:---------|:-----|
| 1️⃣ 改一行配置 | USE_MOCK阻塞/超时太短/URL不对 | `patch` 改配置值 |
| 2️⃣ 加/删一个守卫 | onShow重复redirect/登录态误判 | `patch` 改js逻辑 |
| 3️⃣ 补一个API路由 | 前端调了后端没有 | 后端加 `@router.get/post` |

---

## 5️⃣ 上报格式（用户不知道怎么查时）

如果用户完全不知道怎么操作，让他直接说这3句：

```
1. 哪个页面：______
2. 做了什么：______
3. 看到了什么：______
```

收到后执行`skill_view('miniapp-quick-debug')` → 按第2节匹配模式 → 匹配则直修复 → 不匹配走第3节逐层排查。

---

## 关联

- `jiu-bu-fa-san-tong-dao-pitfall` — 九步法引擎（Step 2 自动匹配本skill）
- `wechat-miniprogram-frontend` — 微信小程序前端开发全链路
- `baseline-restore-protocol` — 基线恢复协议（基线优先）
