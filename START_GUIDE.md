# AI数智名片 — 启动指南 v3.3.0

## 快速启动（Windows）
```bash
cd D:\AI数智名片
start.bat
```

## 手动启动
```bash
cd D:\AI数智名片\backend
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

## 小程序开发
用微信开发者工具打开 D:\AI数智名片\miniapp\
本地开发: apiBaseUrl = http://localhost:8001
生产环境: apiBaseUrl = https://api.liankebao.top

## 版本历史
v3.3.0 - 公开画册查看页 + 图片校验 + 匹配池触发
v3.2.0 - 画册创建/预览/平台创建 + AI询赋代码收割
v3.1.0 - 小程序6个页面连通后端API
v3.0.0 - 1亿用户级基建（API版本化+异步队列+API客户端）
v2.2.0 - 基线
