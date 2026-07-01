# AI数智名片 - 微信小程序

## 目录结构

```
miniapp/
├── app.js                     # 小程序入口
├── app.json                   # 全局配置（页面注册、tabBar、组件声明）
├── app.wxss                   # 全局样式
├── sitemap.json               # 搜索索引配置
├── components/                # 公共组件
│   ├── card-item/             # 名片卡片组件
│   ├── empty-state/           # 空状态占位组件
│   └── loading/               # 加载动画组件
├── pages/                     # 页面
│   ├── index/index.js         # 首页（tabBar）
│   ├── card/card.js           # 名片页（tabBar）
│   ├── profile/profile.js     # 我的页（tabBar）
│   └── login/index.js         # 登录页（未在 app.json 注册）
├── images/                    # 图片资源（tabBar图标需手动添加）
└── utils/                     # 工具
    ├── api.js                 # API 接口封装
    ├── request.js             # HTTP 请求封装
    └── util.js                # 通用工具函数
```

## 后端 API 配置

API 基础地址配置在 `utils/request.js` 中：

- **服务器 IP**: `192.168.7.48`
- **端口**: `8201`
- **基础 URL**: `http://192.168.7.48:8201`

如需修改，请编辑 `utils/request.js` 中的 `DEV_IP` 和 `DEV_PORT` 变量。

## 注意事项

1. **页面注册**：`app.json` 中 `pages` 数组注册了 3 个页面：
   - `pages/index/index`
   - `pages/card/card`
   - `pages/profile/profile`

   ⚠️ `pages/login/index` 页面目录存在于磁盘，但**未在 `app.json` 中注册**。如需使用登录页，请在 `app.json` 的 `pages` 数组中添加 `"pages/login/index"`。

2. **tabBar 图标**：`app.json` 中配置了 tabBar 图标路径（如 `images/tab-home.png`），但 `images/` 目录当前为空，需自行添加图标文件。

3. **组件注册**：全局 `usingComponents` 中已注册以下自定义组件：
   - `card-item` → `/components/card-item/index`
   - `loading` → `/components/loading/index`
   - `empty-state` → `/components/empty-state/index`

4. **登录态**：请求封装（`utils/request.js`）从 `app.globalData.token` 获取 token，使用 `Authorization: Bearer <token>` 头进行认证。

## 开发调试

在微信开发者工具中导入 `D:\AI数智名片\miniapp\` 目录即可运行。
