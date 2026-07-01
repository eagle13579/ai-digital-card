# 性能预算门禁 — AI数智名片

| 状态 | 最后更新 |
|------|----------|
| ✅ 已生效 | 2026-07-01 |

> **本文件定义 AI 数智名片前端的性能预算指标、当前基线、超预算处理流程。**
> 所有指标由 Lighthouse CI 在 CI 流水线中自动审核（参见 `.github/workflows/performance.yml`）。

---

## 1. 性能指标定义

### 1.1 Core Web Vitals（核心网页指标）

| 指标 | 全称 | 含义 | 良好 | 待改善 | 差 |
|------|------|------|------|--------|----|
| **FCP** | First Contentful Paint | 首屏首次内容绘制时间 | ≤1.8s | ≤3.0s | >3.0s |
| **LCP** | Largest Contentful Paint | 最大内容绘制时间 | ≤2.5s | ≤4.0s | >4.0s |
| **TBT** | Total Blocking Time | 总阻塞时间（主线程） | ≤200ms | ≤600ms | >600ms |
| **CLS** | Cumulative Layout Shift | 累积布局偏移 | ≤0.1 | ≤0.25 | >0.25 |
| **SI** | Speed Index | 速度指数（内容可见速度） | ≤3.4s | ≤5.8s | >5.8s |
| **FID / TTI** | First Input Delay / Time to Interactive | 首次输入延迟 / 可交互时间 | ≤100ms / ≤3.8s | — | — |

### 1.2 详细说明

#### FCP — First Contentful Paint
浏览器首次渲染任何文本、图片、SVG 或非白色 `<canvas>` 的时间点。

**优化方向**:
- 减少首屏 CSS/JS 阻塞
- 启用字体预加载 `<link rel="preload">`
- 使用 HTTP/2 Server Push 或 103 Early Hints
- 最小化关键渲染路径长度

#### LCP — Largest Contentful Paint
视口内最大可见元素（图片、视频、背景图、文本块）的渲染时间。

**优化方向**:
- 优化图片加载（压缩、WebP/AVIF、懒加载除外）
- 移除大型渲染阻塞资源
- 优化服务器响应时间（TTFB < 800ms）
- 使用 CDN 和缓存策略

#### TBT — Total Blocking Time
FCP 与 TTI 之间，主线程被长任务（>50ms）阻塞的总时间。

**优化方向**:
- 代码分割和懒加载
- 减小 JavaScript bundle 体积
- 移除未使用的 polyfill
- 使用 Web Workers 处理 CPU 密集型任务

#### CLS — Cumulative Layout Shift
页面整个生命周期内所有意外布局偏移的累计分数。

**优化方向**:
- 为图片和视频显式设置宽高 (`width` / `height` / `aspect-ratio`)
- 避免在现有内容上方插入动态内容
- 使用 `min-height` 为动态内容预留空间
- 使用 `transform` 动画代替布局触发动画

#### SI — Speed Index
页面可见部分在视口中填充的速度（越低越快）。

**优化方向**:
- 结合 FCP + LCP 优化策略
- 优化首屏图片加载优先级
- 减少初始 DOM 节点数量

---

## 2. 预算基线 & 目标

### 2.1 当前预算（门禁值）

> Lighthouse CI 断言级别:
> - `error` — 超限即阻断 CI 流水线
> - `warn` — 超限仅警告，不阻断

| 指标 | 预算值 | 断言级别 | 说明 |
|------|--------|----------|------|
| **FCP** | ≤ **2.0s** | `warn` | 首屏内容响应 |
| **LCP** | ≤ **3.0s** | `warn` | 最大内容加载 |
| **TBT** | ≤ **300ms** | `warn` | 主线程阻塞 |
| **CLS** | ≤ **0.1** | `warn` | 布局稳定性 |
| **SI** | ≤ **3.5s** | `warn` | 内容可见速度 |
| **TTI** | ≤ **4.0s** | `warn` | 可交互时间 |
| **Max FID** | ≤ **100ms** | `warn` | 首次输入延迟 |
| **控制台错误** | **0** | `error` | 阻断 CI |
| **被动事件监听** | **0** | `error` | 阻断 CI |
| **文档 title** | **存在** | `error` | 阻断 CI |
| **meta viewport** | **存在** | `error` | 阻断 CI |
| **总字节量** | ≤ **500 KB** | `warn` | JS 包体积 |
| **未使用 JS** | ≤ **100 KB** | `warn` | 代码冗余 |
| **未使用 CSS** | ≤ **50 KB** | `warn` | 样式冗余 |

### 2.2 目标值（下季度）

| 指标 | 当前 | 目标 | 预期达成 |
|------|------|------|----------|
| FCP | ≤ 2.0s | ≤ **1.5s** | Q3 2026 |
| LCP | ≤ 3.0s | ≤ **2.0s** | Q3 2026 |
| TBT | ≤ 300ms | ≤ **150ms** | Q3 2026 |
| CLS | ≤ 0.1 | ≤ **0.05** | Q3 2026 |
| SI | ≤ 3.5s | ≤ **2.5s** | Q3 2026 |
| Lighthouse Performance Score | ≥ 85 | ≥ **95** | Q3 2026 |

---

## 3. 测量配置

### 3.1 测试环境

| 参数 | 值 |
|------|----|
| 工具 | Lighthouse CI (`@lhci/cli@0.14.x`) |
| 浏览器 | Headless Chrome |
| 设备模拟 | **Desktop** (1350×940, DPR=1) |
| 网络节流 | 40ms RTT, 10 Mbps (有线宽带) |
| CPU 节流 | 1× (无降速) |
| 运行次数 | 每 URL **3 次**，取中位数 |
| 测试页面 | `/`, `/cards`, `/matching`, `/network` |

### 3.2 CI 触发策略

| 触发事件 | 行为 |
|----------|------|
| `push` → `main` | 全量审计，阻断合并 |
| `pull_request` → `main` | 全量审计，PR 评论 + 阻断合并 |
| `workflow_dispatch` | 手动触发 |

---

## 4. 超预算处理流程

### 4.1 响应矩阵

| 断言级别 | 触发条件 | 效果 | 处理人 |
|----------|----------|------|--------|
| `error` | 控制台错误 / 被动事件 / SEO | ❌ **CI 阻断**，无法合并 | 开发者 |
| `warn` | Core Web Vitals / 资源体积 | ⚠️ PR 评论警告，不阻断 | 开发者/性能负责人 |
| `warn` | 图片优化 / 未使用代码 | ℹ️ 注释性警告 | 开发者/性能负责人 |

### 4.2 处理步骤

```
1. 发现超预算
   ├─ PR 评论行: "❌ Lighthouse CI 性能审计未通过"
   └─ 前往 Actions → lhci-reports-{sha} 下载报告

2. 分析报告
   ├─ 打开 HTML 报告 → Diagnostics
   ├─ 定位具体指标和优化建议
   └─ 使用 Lighthouse Opportunity 估算优化收益

3. 修复性能问题
   ├─ 按指标优化方向（见第 1 节）修改代码
   ├─ 本地运行 npx lhci autorun 验证
   └─ 提交新 commit → 重新触发 CI

4. 确认通过
   ├─ PR 评论变更为 "✅ Lighthouse CI 性能审计通过"
   └─ 合并 PR
```

### 4.3 豁免流程

> 仅在以下情景可申请豁免:
> - **功能上线紧急** — 性能问题已知但非阻塞，且已创建修复 Issue
> - **第三方依赖** — 性能退化由外部库导致，已提上游 PR
> - **基础设施变更** — 迁移 CDN / 升级浏览器等，需重新校准基线

**申请步骤**:
1. 在 PR 中评论 `/perf-exempt` 并附理由
2. 性能负责人 24h 内审批
3. 审批通过后，工作流维护者可在 `assert.assertions` 中将对应指标临时改为 `off`
4. 豁免有效期 **7 天**，到期自动恢复

---

## 5. 相关文件

| 文件 | 用途 |
|------|------|
| `frontend/.lighthouserc.js` | Lighthouse CI 配置 + 预算定义 |
| `.github/workflows/performance.yml` | CI 流水线实现 |
| `frontend/vite.config.ts` | 构建配置 |
| `docs/ops/PERFORMANCE_BUDGET.md` | **本文件 — 性能预算文档** |
| `docs/testing/BENCHMARKS.md` | 性能基准测试记录（如存在） |

---

## 6. 参考资源

- [Lighthouse CI 官方文档](https://github.com/GoogleChrome/lighthouse-ci)
- [Core Web Vitals — web.dev](https://web.dev/vitals/)
- [Lighthouse 评分计算](https://developer.chrome.com/docs/lighthouse/performance/performance-scoring)
- [webpack 性能优化](https://webpack.js.org/guides/build-performance/)
- [Vite 构建优化](https://vite.dev/guide/build.html)

---

_维护团队: AI 数智名片前端组_
_文件创建: 2026-07-01 | 下次审核: 2026-10-01_
