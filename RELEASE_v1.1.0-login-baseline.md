# 登录模块基线 v1.1.0

## 基线信息

| 项目 | 值 |
|:-----|:----|
| 基线标签 | `v1.1.0-login-baseline` |
| 父仓库commit | `b959bee` |
| 子仓库commit | `a2e8062` |
| 基于 | `1d84b4e` (v1.0.0 登录模块基线) |
| 冻结日期 | 2026-07-16 |

## 包含的修复

| # | 修复 | 原因 |
|:--|:-----|:------|
| 1 | `open-type=getUserInfo` → `bindtap=wxLogin` | 废弃API，3.x基础库不触发 |
| 2 | 头像: view+button open-type=chooseAvatar 覆盖模式 | button默认样式不可完全覆盖 |
| 3 | 头像/跳过按钮文字居中 (flex) | 用户体验 |
| 4 | WXSS清理BOM | PowerShell写入残留 |
| 5 | 跳过标记 `_onboardingDone` | 防止被首页守卫再次拉回 |
| 6 | 首页移除"微信用户"→redirect守卫 | 跳过→首页→又被踢回登录页的死循环 |

## 当前已知限制

- 一键登录后，微信返回脱敏数据(昵称=微信用户,头像=空)
- 需用户主动点头像/点昵称输入框获取真实信息
- `wx.chooseAvatar()` 和 `<input type="nickname">` 仅在真机有效
- 支持跳过，后续可在"我的"页补充

## 保护范围

```
miniapp/pages/login/    ← 完整保护
miniapp/app.js          ← 启动路由(登录页onLaunch重定向)不受保护
miniapp/pages/index/    ← 首页onLoad守卫(仅保留isLoggedIn检查)
```

## 基线恢复命令

```bash
# 子仓库
cd D:/AI数智名片/miniapp
git checkout v1.1.0-login-baseline -- pages/login/

# 父仓库
cd D:/AI数智名片
git checkout v1.1.0-login-baseline -- miniapp/pages/login/
```
