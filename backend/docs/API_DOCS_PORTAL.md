# 链客宝 API 文档门户维护说明

> 最后更新: 2026-07-04
> 版本: 1.0

---

## 概述

链客宝 API 文档门户是一个**独立、静态**的开发者文档站点，使用纯 HTML + CSS + JavaScript 构建，**不依赖任何前端框架或构建工具**。

### 访问方式

| 路径 | 说明 |
|------|------|
| `GET /docs/portal` | 文档门户首页 |
| `GET /docs/{section}` | 指定章节（如 `/docs/auth`） |
| `/docs` | FastAPI 自动 Swagger UI（已存在） |
| `/redoc` | FastAPI 自动 ReDoc（已存在） |

---

## 文件结构

```
backend/
├── templates/
│   └── docs_portal.html          ← 文档门户 HTML（核心文件）
├── app/routers/
│   └── docs_portal_router.py     ← 文档门户路由（FastAPI 端点）
├── scripts/
│   └── export_openapi.py         ← OpenAPI schema 导出脚本
├── data/
│   └── openapi/
│       ├── openapi.json          ← 最新 OpenAPI schema
│       └── openapi_20260704_120000.json  ← 历史快照
└── docs/
    └── API_DOCS_PORTAL.md        ← 本文档
```

---

## 如何新增 API 文档章节

### 步骤

1. **在 `templates/docs_portal.html` 中添加内容块**

```html
<section id="api-new-module">
<h2>新模块</h2>
<p>描述...</p>
<!-- 端点表格、代码示例等 -->
</section>
```

2. **在侧边导航中添加链接**

在 `sidebar-nav` 中找到对应的分组（如 `API 参考`），添加：

```html
<a href="#api-new-module">新模块</a>
```

3. **在路由章节映射表中注册**

编辑 `app/routers/docs_portal_router.py` 中的 `section_map` 字典：

```python
section_map = {
    ...
    "new-module": "api-new-module",
}
```

### 注意事项

- HTML 文件是**静态自包含**的，所有样式和脚本都已内联
- 不要引入外部 CDN 资源（需离线可用）
- 代码示例统一使用 `<pre>` 标签
- 端点表格统一使用 `.method` + `.endpoint-row` 样式类
- 保持总代码量 ≤ 1000 行

---

## 如何更新 OpenAPI 导出

### 方式一：从代码生成（推荐）

```bash
cd backend
python scripts/export_openapi.py
```

输出: `data/openapi/openapi.json`

### 方式二：从运行中的服务获取

```bash
cd backend
python scripts/export_openapi.py --server --base-url http://127.0.0.1:8001
```

### 方式三：自定义输出路径

```bash
python scripts/export_openapi.py --output /tmp/my_openapi.json
```

### 部署钩子集成

在部署脚本中添加（服务启动后）：

```bash
cd /path/to/backend
python scripts/export_openapi.py --server --base-url http://127.0.0.1:8001
```

---

## 文档门户设计原则

1. **Stripe 风格 UI**：左侧固定导航 + 右侧滚动内容
2. **移动端适配**：768px 以下隐藏侧边栏
3. **零外部依赖**：无 CDN、无 npm、无 Webpack
4. **内容驱动**：所有文档内容在 HTML 中直接编写
5. **版本化感知**：URL 带版本号、版本标签显示
6. **自给自足**：FastAPI router 将 HTML 作为静态字符串服务

---

## 常见问题

### Q: 更新 HTML 后需要重启服务吗？

**需要。** 文档门户路由在首次请求时缓存 HTML 内容。重启服务或调用 `reload_portal_cache()` 可刷新缓存。

### Q: 如何添加多语言支持？

当前版本仅支持中文。如需多语言，建议创建多个 `docs_portal_{lang}.html` 文件，在不同路径下分别服务。

### Q: 文档门户和 Swagger UI 是什么关系？

- **Swagger UI** (`/docs`)：自动生成的交互式 API 调试界面
- **文档门户** (`/docs/portal`)：手写的开发者文档站，包含教程、SDK 使用、定价等
- 两者互补，Swagger 用于调试，门户用于学习

---

## 相关文档

- [API 版本化方案](api/VERSIONING.md)
- [Webhook 系统文档](WEBHOOKS.md)
- [定价引擎文档](PRICING_ENGINE.md)
- [OpenAPI V1 参考](OPEN_API_V1.md)
