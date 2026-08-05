# AI 数字名片 · 组件库文档 (DS-09)

> 本文件列举可复用的 UI 组件模式，每个组件附带 HTML 结构 + Token 引用对照表。
>
> 基于 `_design_tokens.css` 构建，所有样式引用 CSS 变量，禁止硬编码。

---

## 目录

1. [导航栏 (Navbar)](#1-导航栏-navbar)
2. [卡片组件 (Card)](#2-卡片组件-card)
3. [按钮系统 (Button)](#3-按钮系统-button)
4. [表单输入 (Form Input)](#4-表单输入-form-input)
5. [定价卡 (Pricing Card)](#5-定价卡-pricing-card)
6. [Footer (页脚)](#6-footer-页脚)

---

## 1. 导航栏 (Navbar)

### HTML 结构

```html
<nav class="navbar">
  <div class="logo">
    <span class="logo-icon">🪪</span>
    <span class="logo-text">AI数智名片</span>
  </div>
  <ul class="nav-links">
    <li><a href="/">首页</a></li>
    <li><a href="/#features">功能</a></li>
    <li><a href="/#about">关于</a></li>
  </ul>
</nav>
```

### Token 引用表

| 元素 | 属性 | Token |
|------|------|-------|
| `.navbar` 背景 | `background` | `var(--bg-card, #1a1f3a)` |
| `.navbar` 下边框 | `border-bottom` | `1px solid rgba(255,255,255,0.06)` |
| `.navbar` 内边距 | `padding` | `var(--spacing-md) var(--spacing-lg)` |
| `.logo-text` | `background` | `var(--color-primary-gradient)` |
| `.logo-text` | `font` | `18px` + `font-weight: 700` |
| `.nav-links a` | `color` | `var(--text-secondary, #94a3b8)` |
| `.nav-links a:hover` | `color` | `var(--color-primary, #06b6d4)` |
| `.nav-links a` | `font-size` | `14px` (≈ `--font-small`) |

### 变体

- **透明导航栏**：移除 `background`，仅保留 `border-bottom`
- **固定导航栏**：加 `position: fixed; top: 0; width: 100%; z-index: 100;`

---

## 2. 卡片组件 (Card)

### HTML 结构

```html
<div class="card">
  <!-- 可选：卡片头部 -->
  <div class="card-header">
    <h3 class="card-title">卡片标题</h3>
    <span class="card-badge">标签</span>
  </div>
  <!-- 卡片内容 -->
  <div class="card-body">
    <p>这里是卡片描述文本。</p>
  </div>
  <!-- 可选：卡片操作区 -->
  <div class="card-footer">
    <a href="#" class="btn btn-primary">了解更多</a>
  </div>
</div>
```

### Token 引用表

| 元素 | 属性 | Token |
|------|------|-------|
| `.card` 背景 | `background` | `var(--bg-card, #1a1f3a)` |
| `.card` 圆角 | `border-radius` | `var(--radius-md, 8px)` |
| `.card` 阴影 | `box-shadow` | `var(--shadow-md, 0 4px 12px rgba(0,0,0,0.4))` |
| `.card` 内边距 | `padding` | `var(--spacing-lg, 24px)` |
| `.card-title` 字号 | `font-size` | `var(--font-h3)` |
| `.card-title` 颜色 | `color` | `var(--text-primary, #e2e8f0)` |
| `.card-body` 颜色 | `color` | `var(--text-secondary, #94a3b8)` |
| `.card-body` 行距 | `line-height` | `var(--font-body)` 的 1.6 |
| `.card-footer` 上边距 | `margin-top` | `var(--spacing-md, 16px)` |
| `.card-header` 下边距 | `margin-bottom` | `var(--spacing-sm, 8px)` |

### 变体

- **错误卡片 (Error Card)**：内容居中，无 `.card-header`/`.card-footer`
- **悬浮动效卡片**：`:hover` 时 `transform: translateY(-4px)` + `var(--shadow-lg)`
- **点击整卡**：整个卡片为 `<a>` 或加 `cursor: pointer;`

---

## 3. 按钮系统 (Button)

### 3.1 主要按钮 (Primary)

```html
<button class="btn btn-primary">创建名片</button>
<!-- 或作为链接 -->
<a href="/create" class="btn btn-primary">创建名片</a>
```

### 3.2 次要按钮 (Secondary)

```html
<button class="btn btn-secondary">取消</button>
```

### 3.3 文字按钮 (Text)

```html
<button class="btn btn-text">查看详情 →</button>
```

### 3.4 禁用状态 (Disabled)

```html
<button class="btn btn-primary" disabled>提交中…</button>
```

### Token & 样式对照表

| 属性 | `.btn-primary` | `.btn-secondary` | `.btn-text` | `.btn:disabled` |
|------|----------------|------------------|-------------|-----------------|
| 背景 | `var(--color-primary-gradient)` | `var(--bg-elevated)` | `transparent` | `var(--bg-card)` |
| 颜色 | `#fff` | `var(--text-primary)` | `var(--color-primary)` | `var(--text-secondary)` |
| 内边距 | `var(--spacing-md, 14px 36px)` | 同上 | `var(--spacing-sm) var(--spacing-md)` | 同上 |
| 圆角 | `var(--radius-md, 8px)` | 同上 | `var(--radius-sm, 4px)` | 同上 |
| 边框 | `none` | `1px solid rgba(255,255,255,0.1)` | `none` | `none` |
| 光标 | `pointer` | `pointer` | `pointer` | `not-allowed` |

### 公共样式

```css
.btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  text-decoration: none;
  transition: transform 0.2s, box-shadow 0.2s;
  cursor: pointer;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(6, 182, 212, 0.35);
}
```

---

## 4. 表单输入 (Form Input)

### HTML 结构

```html
<div class="form-field">
  <label class="form-label" for="name">姓名</label>
  <input
    type="text"
    id="name"
    class="form-input"
    placeholder="请输入您的姓名"
    required
  />
  <span class="form-hint">请输入真实姓名，用于名片展示</span>
  <span class="form-error">姓名不能为空</span>
</div>
```

### Token 引用表

| 元素 | 属性 | Token |
|------|------|-------|
| `.form-label` | `color` | `var(--text-primary, #e2e8f0)` |
| `.form-label` | `font` | `var(--font-small, 0.875rem)` |
| `.form-label` | 下边距 | `var(--spacing-xs, 4px)` |
| `.form-input` | 背景 | `var(--bg-elevated, #232850)` |
| `.form-input` | 文字颜色 | `var(--text-primary, #e2e8f0)` |
| `.form-input` | 边框 | `1px solid rgba(255,255,255,0.1)` |
| `.form-input` | 圆角 | `var(--radius-md, 8px)` |
| `.form-input` | 内边距 | `var(--spacing-sm, 8px) var(--spacing-md, 16px)` |
| `.form-input:focus` 边框 | `border-color` | `var(--color-primary, #06b6d4)` |
| `.form-hint` | `color` | `var(--text-secondary, #94a3b8)` |
| `.form-error` | `color` | `var(--color-error, #EF4444)` |
| `.form-field` 下边距 | `margin-bottom` | `var(--spacing-md, 16px)` |

### 状态变体

- **错误状态**：`.form-input.error` — 边框 `var(--color-error)`
- **成功状态**：`.form-input.success` — 边框 `var(--color-success)`
- **禁用状态**：`.form-input:disabled` — 透明度 0.5

---

## 5. 定价卡 (Pricing Card)

### HTML 结构

```html
<div class="pricing-card">
  <div class="pricing-header">
    <h3 class="pricing-plan">专业版</h3>
    <div class="pricing-price">
      <span class="price-amount">¥99</span>
      <span class="price-period">/月</span>
    </div>
    <p class="pricing-desc">适合个人创业者</p>
  </div>
  <ul class="pricing-features">
    <li class="feature-item">✓ 无限名片创建</li>
    <li class="feature-item">✓ AI 智能匹配</li>
    <li class="feature-item">✓ 数据分析看板</li>
    <li class="feature-item">✗ 团队协作</li>
  </ul>
  <div class="pricing-footer">
    <a href="/subscribe" class="btn btn-primary">立即开通</a>
  </div>
</div>

<!-- 推荐/高亮版 -->
<div class="pricing-card featured">
  <div class="pricing-badge">最受欢迎</div>
  <!-- … 其余结构同上 … -->
</div>
```

### Token 引用表

| 元素 | 属性 | Token |
|------|------|-------|
| `.pricing-card` 背景 | `background` | `var(--bg-card, #1a1f3a)` |
| `.pricing-card` 圆角 | `border-radius` | `var(--radius-lg, 16px)` |
| `.pricing-card` 内边距 | `padding` | `var(--spacing-xl, 48px)` |
| `.pricing-card.featured` 边框 | `border` | `1px solid var(--color-primary, #06b6d4)` |
| `.pricing-plan` | `font` | `var(--font-h3)` |
| `.price-amount` | `font` | `var(--font-h1)` |
| `.price-amount` | `color` | `var(--color-primary, #06b6d4)` |
| `.price-period` | `color` | `var(--text-secondary, #94a3b8)` |
| `.pricing-desc` | `color` | `var(--text-secondary, #94a3b8)` |
| `.pricing-badge` 背景 | `background` | `var(--color-primary-gradient)` |
| `.feature-item` | `color` | `var(--text-primary, #e2e8f0)` |
| `.pricing-footer` 上边距 | `margin-top` | `var(--spacing-lg, 24px)` |

### 布局

- 使用 CSS Grid：`grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: var(--spacing-lg)`
- 推荐版使用 `transform: scale(1.05)` 略微放大

---

## 6. Footer (页脚)

### HTML 结构

```html
<footer class="footer">
  <p>
    &copy; 2025-2026 <a href="/">AI数智名片</a>. All rights reserved. &nbsp;|&nbsp;
    Powered by Bai Ze Legion
  </p>
</footer>
```

### Token 引用表

| 元素 | 属性 | Token |
|------|------|-------|
| `.footer` 背景 | `background` | `var(--bg-card, #1a1f3a)` |
| `.footer` 上边框 | `border-top` | `1px solid rgba(255,255,255,0.06)` |
| `.footer` 内边距 | `padding` | `var(--spacing-lg, 24px)` |
| `.footer p` | `color` | `var(--text-secondary, #94a3b8)` |
| `.footer p` | `font-size` | `13px` |
| `.footer a` | `color` | `var(--color-primary, #06b6d4)` |

---

## 组件依赖图

```
Navbar
  ├── Logo (logo-icon + logo-text)
  └── NavLinks (link items)

Page
  ├── Navbar
  ├── Card (通用容器)
  │   ├── CardHeader + CardBody + CardFooter
  │   ├── PricingCard (extends Card)
  │   └── ErrorCard (centered variant)
  ├── FormInput (field + label + input + hint/error)
  ├── Button
  │   ├── Primary
  │   ├── Secondary
  │   ├── Text
  │   └── Disabled
  └── Footer
```

---

> **维护人**: 烛龙 (Bai Ze Legion P8) · **最后更新**: 2026-07-17
>
> 新组件使用前请在本文档追加条目，并标注 Token 引用关系。
