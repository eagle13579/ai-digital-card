# AI数智名片 — 移动App构建与安装指南

> 版本: v1.0 | 日期: 2026-07-10

---

## 一、构建APK（安卓手机安装）

### 前提条件
- **Java JDK 11+** → `java -version` 确认
- **Android SDK** → 需安装 Android Studio 或单独下载
- **ANDROID_HOME 环境变量** → 指向 SDK 路径

### Step 1: 配置Android SDK路径
编辑 `D:/AI数智名片/mobile/android/local.properties`:
```
# Windows
sdk.dir=C:\\Users\\你的用户名\\AppData\\Local\\Android\\Sdk

# Mac
sdk.dir=/Users/你的用户名/Library/Android/sdk

# Linux
sdk.dir=/home/用户名/Android/Sdk
```

### Step 2: 构建APK
```bash
cd D:/AI数智名片/mobile/android
./gradlew assembleRelease
```

### Step 3: 安装到手机
构建完成后APK在:
```
D:/AI数智名片/mobile/android/app/build/outputs/apk/release/app-release.apk
```
方式1: 用数据线连接手机 → 把APK拷到手机 → 点击安装
方式2: 用adb安装:
```bash
adb install android/app/build/outputs/apk/release/app-release.apk
```

### 签名(发布到应用商店需要)
```bash
# 生成签名密钥(仅首次)
keytool -genkey -v -keystore release.keystore -alias my-key-alias -keyalg RSA -keysize 2048 -validity 10000

# 配置签名到 android/app/build.gradle:
# signingConfigs { release { storeFile file('release.keystore') ... } }
```

---

## 二、构建IPA（苹果手机安装）

### 前提条件
- **macOS** + **Xcode 15+**
- **CocoaPods** → `sudo gem install cocoapods`

### Step 1: 安装iOS依赖
```bash
cd D:/AI数智名片/mobile/ios
pod install
```

### Step 2: 用Xcode打开项目
```bash
open AIDigitalCard.xcworkspace   # 注意是 .xcworkspace 不是 .xcodeproj
```

### Step 3: 签名配置
在 Xcode 中:
1. 选择 Team (Apple Developer账号)
2. 修改 Bundle Identifier 为你的标识
3. 选择真机或模拟器

### Step 4: 构建运行
- **模拟器**: Xcode → Product → Run (⌘R)
- **真机**: 连接iPhone → Xcode选择设备 → Run

### 导出IPA(给测试人员):
Xcode → Product → Archive → Distribute App → TestFlight / Ad Hoc

---

## 三、快速开发调试

### 启动开发服务器
```bash
cd D:/AI数智名片/mobile
npx react-native start
```

### 在模拟器上运行
```bash
# Android模拟器
npx react-native run-android

# iOS模拟器(仅Mac)
npx react-native run-ios
```

### 修改API地址
所有API请求指向 `mobile/src/api/client.ts`:
- 开发: `http://localhost:8002`
- 生产: `https://api.liankebao.top`

---

## 四、常见问题

| 问题 | 解决 |
|:-----|:-----|
| `SDK location not found` | 配置 local.properties 的 sdk.dir |
| `No compatible devices` | 确认USB调试已开启(安卓) |
| `Code Signing Error` | Xcode中配置Apple Developer Team |
| `metro bundler` 无法连接 | 确认手机和电脑在同一WiFi下 |
