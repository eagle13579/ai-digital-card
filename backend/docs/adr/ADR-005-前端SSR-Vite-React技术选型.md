# ADR-005: 前端 SSR + Vite + React 技术选型

**状态**: Accepted
**日期**: 2026-06-26
**决策者**: 前端组、架构组

## 上下文

链客宝前端需要支持三类用户场景：

1. **企业用户浏览 B2B 匹配页面** — SEO 敏感，需要搜索引擎可索引企业简介和匹配结果
2. **企业管理后台** — 登录后操作，对 SEO 无要求，但对交互复杂度和性能要求高
3. **移动端 H5 访问** — 首屏加载速度直接影响转化率

前端技术选型需要在以下方案中选择：
- **纯 CSR** (Create React App / Vite SPA)
- **SSR** (Next.js / Remix / 自研)
- **SSG** (Gatsby / Astro)

## 决策

采用 **SSR + Vite + React 18** 技术栈，自研 SSR 渲染层（不使用 Next.js）。

具体技术组合：

| 层 | 技术 | 理由 |
|----|------|------|
| 框架 | React 18 + TypeScript | 团队最熟悉，生态最成熟 |
| 构建 | Vite 6 | HMR 速度快，ESM 原生支持 |
| SSR 渲染 | 自研基于 Vite 的 SSR 中间件 | 轻量，无 Next.js 重量级约束 |
| 路由 | React Router v7 | SPA 与 SSR 兼容，支持 loader/action |
| 数据获取 | TanStack Query (React Query) v5 | 服务端预取 + 客户端缓存 |
| CSS | Tailwind CSS v4 | 原子化 CSS，构建产物小 |

SSR 策略：
- **公开页面**（首页、企业黄页、搜索结果）→ 服务端渲染，返回完整 HTML
- **登录后页面**（管理后台、消息中心）→ 客户端渲染 SPA 模式，SSR 仅返回壳
- **混合模式**：在 React Router 的 `loader` 中判断是否需要服务端预取数据

## 理由

1. **SEO 是刚需** — B2B 匹配平台的获客渠道高度依赖搜索引擎（百度、Google），纯 CSR 页面搜索引擎无法抓取企业列表和简介内容。SSR 确保每页都有完整的 `<meta>` 和内容。
2. **首屏性能** — 企业用户在移动端访问时，CSR 需要先下载 1-2MB JS 再渲染，首屏耗时 3-5s；SSR 可以在 1s 内展示内容，转化率提升约 30%（基于行业数据）。
3. **不选 Next.js 的原因**：
   - Next.js 13+ App Router 锁定文件结构，与现有项目组织方式不兼容
   - 团队需要灵活控制渲染逻辑（部分页面 SSR，部分页面 CSR），自研 SSR 中间件更可控
   - Next.js 的 Bundle Size 较大，且升级频繁 break change
4. **Vite 的优势**：HMR 几乎是即时的（<50ms），SSR 构建配置透明，调试方便。

## 后果

**正面**:
- 搜索引擎可完整索引企业信息和匹配结果，提升自然流量
- 首屏加载速度提升 2-3 倍，移动端转化率预期提升
- 自研 SSR 无框架锁定，未来可灵活切换渲染策略（如部分页面 SSG）

**负面**:
- 自研 SSR 渲染层需要维护约 800 行 Node.js 中间件代码
- SSR 服务器 CPU 消耗增加，需要额外部署 Node.js 服务（非静态文件）
- 同构开发需要处理 `window` / `document` 不可用的问题
- 团队需要同时掌握前端和后端 Node.js 知识

## 替代方案

| 方案 | 否决理由 |
|------|---------|
| 纯 CSR (Vite SPA) | SEO 差，首屏加载慢，B2B 匹配业务不可接受 |
| Next.js 14 App Router | 框架锁定，文件结构约束强，升级成本高 |
| Nuxt 3 (Vue) | 团队主要技术栈是 React，迁移成本高 |
| SSG (Gatsby/Astro) | 平台数据动态变化（匹配结果每天更新），SSG 不适合频繁变动的数据 |
| Remix | 社区生态不如 React Router + TanStack Query 成熟，学习曲线陡 |
