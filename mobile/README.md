# AI数智名片 — React Native 移动端

> 基于 React Native 0.73 构建的 iOS/Android 原生 App，作为 [AI数智名片](https://github.com/your-org/ai-digital-business-card) 产品的移动端入口。

---

## 目录结构

```
mobile/
├── package.json              # 依赖配置
├── tsconfig.json             # TypeScript 配置
├── App.tsx                   # 根组件（SafeAreaProvider + 导航容器）
├── src/
│   ├── api/
│   │   └── client.ts         # Axios API 客户端（指向 http://localhost:8002 / https://api.liankebao.top）
│   ├── screens/
│   │   ├── LoginScreen.tsx   # 登录页
│   │   ├── HomeScreen.tsx    # 名片列表页（主 Tab）
│   │   ├── CardDetailScreen.tsx  # 名片详情页（Stack）
│   │   ├── ProfileScreen.tsx # 个人中心（Tab）
│   │   └── SettingsScreen.tsx    # 设置页（Tab）
│   ├── components/
│   │   ├── CardItem.tsx      # 名片列表项组件
│   │   └── LoadingSpinner.tsx # 通用加载指示器
│   ├── navigation/
│   │   └── AppNavigator.tsx  # Tab + Stack 导航配置
│   ├── hooks/
│   │   └── useAuth.ts        # 认证状态管理 Hook
│   └── utils/
│       └── storage.ts        # AsyncStorage 封装
├── android/                  # Android 原生工程（占位，待 `npx react-native init` 生成）
└── ios/                      # iOS 原生工程（占位，待 `npx react-native init` 生成）
```

---

## 环境要求

| 工具       | 版本要求     |
| ---------- | ------------ |
| Node.js    | >= 18        |
| npm / yarn | 任意         |
| Xcode      | >= 15 (iOS)  |
| Android Studio | Hedgehog 2023.1+ (Android) |
| CocoaPods  | >= 1.14 (iOS) |

---

## 快速开始

### 1. 安装依赖

```bash
# 在 mobile/ 目录下
cd mobile
npm install

# iOS 还需要安装 CocoaPods（如果使用 iOS）
cd ios && pod install && cd ..
```

### 2. 启动开发服务器

```bash
npx react-native start
```

### 3. 运行 App

```bash
# Android
npx react-native run-android

# iOS
npx react-native run-ios
```

---

## 开发说明

### API 地址

- **开发环境**: `http://localhost:8002`
- **生产环境**: `https://api.liankebao.top`

通过 `src/api/client.ts` 中的 `__DEV__` 标志自动切换。

### 认证流程

1. 打开 App → 未登录 → 显示 `LoginScreen`
2. 用户输入邮箱/密码 → 调用 `POST /api/v1/auth/login`
3. 成功后 Token 和 UserProfile 存入 AsyncStorage
4. 下次启动自动恢复登录态（`useAuth` 的 hydrate 逻辑）

### 主题系统

当前使用硬编码样式（参考 DESIGN.md 的 Token 体系），主要颜色：

| Token    | 值       | 用途           |
| -------- | -------- | -------------- |
| `--primary`   | `#4a90d9` | 主色调、按钮、Tab 激活态 |
| `--bg`        | `#f5f5f5` | 背景色         |
| `--text`      | `#1a1a1a` | 主要文字色     |
| `--text-secondary` | `#888`  | 次要文字色     |
| `--danger`    | `#e53935` | 危险/退出操作  |

后续可迁移至 `ThemeContext` 实现动态主题。

### 导航结构

```
NavigationContainer
└── NativeStackNavigator (根)
    ├── [未登录] AuthStack
    │   └── LoginScreen
    └── [已登录]
        ├── MainTabs (BottomTabNavigator)
        │   ├── Home → HomeScreen
        │   ├── Profile → ProfileScreen
        │   └── Settings → SettingsScreen
        └── CardDetail → CardDetailScreen (Stack, 从 Home push)
```

---

## 脚本

| 命令           | 说明                     |
| -------------- | ------------------------ |
| `npm start`    | 启动 Metro bundler       |
| `npm run android` | 构建并运行 Android App |
| `npm run ios`  | 构建并运行 iOS App       |
| `npm test`     | 运行 Jest 测试           |
| `npm run lint` | ESLint 代码检查          |

---

## 与 Web/WeApp 复用说明

- **`src/hooks/useAuth.ts`** — 延续 Web 前端 `useAuth` 的接口设计（`login` / `logout` / `user` / `token`），但使用 AsyncStorage 替代 localStorage。
- **`src/api/client.ts`** — 基于 Axios，与 Web 前端 API 层保持相同的请求/响应格式。
- 组件层未直接复用（RN 使用 React Native 原生组件而非 HTML），但业务逻辑可提取为 shared 库。

---

## 常见问题

**Q: Android 构建提示 "SDK location not found"?**
A: 在项目根或 `android/` 下创建 `local.properties`，添加：
```
sdk.dir=/path/to/Android/sdk
```

**Q: iOS pod install 失败？**
A: 确保已安装 CocoaPods：`sudo gem install cocoapods`，然后 `cd ios && pod install --repo-update`。
