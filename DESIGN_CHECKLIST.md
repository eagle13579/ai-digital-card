# AI 数字名片 · 设计清单 (DS-11)

> 三点检验标准：确保每个页面的设计质量达到 Bai Ze Legion P8 工程规范。

---

## □ 1. 重点突出 — 用户 3 秒内说出核心价值

| # | 检查项 | 状态 |
|---|--------|------|
| 1.1 | 页面标题（`<h1>`）直接表达页面用途，不绕弯、不堆砌术语 | [x] |
| 1.2 | 首屏（above the fold）仅包含 **1 个**主要行动号召（CTA），无干扰按钮 | [x] |
| 1.3 | 视觉层级清晰：标题 → 副标题 → CTA，间距和字号按 `--font-h1` / `--font-h2` / `--font-h3` 递减 | [x] |
| 1.4 | 如果页面面向"AI 名片曝光/匹配/转化"，3 秒内能让新访客说清"这个页面能帮我做什么" | [x] |
| 1.5 | 无冗余装饰元素分散注意力（纯装饰性 SVG/图标不超过 2 个） | [x] |

---

## □ 2. 场景分组 — 卡片标题用用户语言，不按技术类型

| # | 检查项 | 状态 |
|---|--------|------|
| 2.1 | 卡片/功能区的标题使用**用户场景语言**，例如"快速创建名片"而非"CardCreateModule"、"展示我的作品"而非"PortfolioGrid" | [x] |
| 2.2 | 分组逻辑按用户旅程组织（如：创建 → 展示 → 社交 → 分析），而非按技术架构（前端/后端/API） | [x] |
| 2.3 | 每个卡片组不超过 5 项，超出则用"查看更多"折叠 | [x] |
| 2.4 | 卡片组标题带 `aria-label` 或可读标识，支持屏幕阅读导航 | [~] |
| 2.5 | 国际化友好：标题文本全部外置于 `i18n` 字典（`utils/i18n.js`），页面内不硬编码中文/英文 | [~] |

---

## □ 3. Token 一致 — 新页面用 `_design_tokens.css` 变量，无硬编码

| # | 检查项 | 状态 |
|---|--------|------|
| 3.1 | 所有颜色使用 CSS 变量（`var(--color-*)` / `var(--bg-*)` / `var(--text-*)`），零硬编码 hex/rgb | [x] |
| 3.2 | 间距使用 `var(--spacing-*)` 层级（xs/sm/md/lg/xl/2xl），禁止随意 px 值 | [x] |
| 3.3 | 圆角统一使用 `var(--radius-*)`（sm/md/lg），字体层级使用 `var(--font-*)` | [~] |
| 3.4 | 阴影统一使用 `var(--shadow-*)`（sm/md/lg），禁止手写 `box-shadow` 值 | [x] |
| 3.5 | `<head>` 内通过 `<link rel="stylesheet" href="/_design_tokens.css">` 引入设计令牌文件 | [x] |

---

### 快速自检命令

```bash
# 扫描硬编码颜色（应返回空）
grep -rnP '#[0-9a-fA-F]{6}' pages/ --include='*.html' --include='*.wxss' \
  | grep -v '_design_tokens.css' \
  | grep -v 'node_modules'

# 扫描硬编码圆角
grep -rnP 'border-radius:\s*\d+px' pages/ --include='*.html' --include='*.wxss'

# 扫描硬编码阴影
grep -rnP 'box-shadow:\s*\d+' pages/ --include='*.html' --include='*.wxss'
```

---

> **状态标记**: `[-]` 未检 / `[x]` 通过 / `[~]` 部分通过需修复
>
> 最后更新: 2026-07-17 · 维护人: 烛龙 (Bai Ze Legion P8)
