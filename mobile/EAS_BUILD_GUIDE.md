# AI数智名片 — EAS云构建指南

> 不需要mac，在Windows上直接构建iOS应用

---

## 前置准备

### 1. 注册两个账号（免费）

| 账号 | 用途 | 注册地址 | 费用 |
|:-----|:------|:---------|:----:|
| **Expo账号** | 云构建服务 | https://expo.dev/signup | 免费 |
| **Apple Developer** | iOS签名 | https://developer.apple.com | $99/年 |

### 2. 登录EAS

```bash
cd D:/AI数智名片/mobile
eas login
# 输入Expo账号密码
```

### 3. 配置Apple凭证

```bash
eas credentials
# 按提示上传Apple Developer证书
```

---

## 一键构建

### 🔵 开发版（装iPhone上调试）
```bash
eas build --platform ios --profile development
```
构建完成后会生成二维码和链接，用iPhone Safari打开即可安装。

### 🟢 预览版（给测试人员）
```bash
eas build --platform ios --profile preview
```

### 🔴 生产版（提交App Store）
```bash
eas build --platform ios --profile production

# 提交到TestFlight
eas submit --platform ios --profile production
```

---

## 构建完成后

1. 手机会收到通知
2. 打开链接安装描述文件
3. 设置 → 通用 → VPN与设备管理 → 信任开发者证书
4. 打开App → 🚀

---

## 常见问题

| 问题 | 解决 |
|:-----|:------|
| `Apple Developeraccount required` | 在 developer.apple.com 注册($99/年) |
| `No build credentials found` | 运行 `eas credentials` 上传证书 |
| `Build timeout` | 重新运行，EAS免费版有2小时限制 |
| 应用闪退 | 检查 `src/api/client.ts` 中的API地址 |

---

## 不需要mac的完整流程

```
Windows电脑                    Expo云服务器                  iPhone
    │                              │                         │
    ├─ eas build --platform ios ───→│                         │
    │                              ├─ 拉代码                  │
    │                              ├─ 安装依赖                │
    │                              ├─ 编译IPA (30分钟)        │
    │                              ├─ 签名                    │
    │                              ├─ 生成二维码 ←────────────┤
    │                              │                         ├─ Safari扫码
    │                              │                         ├─ 安装App
    │                              │                         └─ 🎉 使用
    └─ eas submit → App Store ────→│                         │
                                  └─────────────────────────┘
```
