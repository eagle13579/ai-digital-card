# AI 数智名片 — Design Tokens

> 基于 Tailwind CSS v4 `@theme` 定义的标准设计令牌。
> 所有令牌值对应项目 `src/index.css` 中的 `@theme` 配置。

---

## 1. 色彩系统 (Color System)

### 主色 (Primary)

| Token | Tailwind Value | Hex | 用途 |
|-------|---------------|-----|------|
| `primary` | `sky-600` | `#0284c7` | 主要按钮、链接、激活态、品牌色 |
| `primary-container` | `sky-500` | `#0ea5e9` | 按钮 hover、渐变主色 |
| `primary-light` | `sky-100` | `#e0f2fe` | 背景色、标签、轻量高亮 |

### 次要色 (Secondary)

| Token | Tailwind Value | Hex | 用途 |
|-------|---------------|-----|------|
| `secondary` | `slate-600` | `#475569` | 次要按钮、辅助文字 |

### 强调色 (Accent)

| Token | Tailwind Value | Hex | 用途 |
|-------|---------------|-----|------|
| `--gradient-accent` | — | `#2563eb → #7c3aed` | 品牌渐变 (`brand-gradient`) |
| `--glow-primary` | — | `rgba(14,165,233,0.15)` | 脉冲发光效果 (`pulse-glow`) |

### 中性色 (Neutral)

| Token | Tailwind Value | Hex | 用途 |
|-------|---------------|-----|------|
| `neutral-bg` | `slate-50` | `#f8fafc` | 页面背景 |
| `surface` | `white` | `#ffffff` | 卡片/面板/弹窗背景 |
| `on-surface` | `slate-800` | `#1e293b` | 主要内容文字 |
| `text-muted` | `slate-400` | `#94a3b8` | 次要说明文字、占位符 |
| `border-light` | `slate-200` | `#e2e8f0` | 边框、分割线 |

### 语义色 (Semantic)

| Token | Tailwind Value | Hex | 用途 |
|-------|---------------|-----|------|
| `success` | `emerald-500` | `#10b981` | 成功状态、完成指示 |
| `warning` | `amber-500` | `#f59e0b` | 警告提示、中等评分 |
| `error` | `rose-600` | `#e11d48` | 错误提示、高风险评分 |

### 暗黑模式 (Dark Mode)

| Token | Value | 用途 |
|-------|-------|------|
| `dark-bg` | `#0f172a` | 暗色页面背景 |
| `dark-surface` | `#1e293b` | 暗色卡片/弹窗背景 |
| `dark-border` | `#334155` | 暗色边框 |
| `dark-text` | `#f1f5f9` | 暗色主要文字 |
| `dark-muted` | `#94a3b8` | 暗色次要文字 |

---

## 2. 排版 (Typography)

### 字体家族 (Font Families)

| Token | Font Stack | 用途 |
|-------|-----------|------|
| `font-sans` | `"Noto Sans SC", "Inter", ui-sans-serif, system-ui, sans-serif` | 正文/界面文本 |
| `font-manrope` | `"Manrope", "Noto Sans SC", sans-serif` | 标题/品牌文本 |
| `font-inter` | `"Inter", ui-sans-serif, system-ui, sans-serif` | 英文数字文本 |

### 字号层级 (Type Scale)

| 级别 | Tailwind Class | Size | Weight | 用途 |
|------|---------------|------|--------|------|
| h1 | `text-2xl lg:text-3xl` | `1.5rem → 1.875rem` | `700-800` | 页面大标题 |
| h2 | `text-xl lg:text-2xl` | `1.25rem → 1.5rem` | `700` | 区块标题 |
| h3 | `text-lg lg:text-xl` | `1.125rem → 1.25rem` | `600-700` | 卡片标题 |
| h4 | `text-base` | `1rem` | `600` | 小标题/导航 |
| h5 | `text-sm` | `0.875rem` | `600` | 分组标题 |
| h6 | `text-xs` | `0.75rem` | `600` | 微型标题 |
| body | `text-sm` | `0.875rem` | `400-500` | 正文内容 |
| caption | `text-xs` | `0.75rem` | `400` | 说明文字 |
| overline | `text-[10px]` | `0.625rem` | `500` | 上标标签 |

### 修饰类 (Utilities)

| Class | 用途 |
|-------|------|
| `font-bold` | 加粗 (700) |
| `font-medium` | 中等 (500) |
| `font-normal` | 常规 (400) |
| `tracking-tight` | 紧凑字间距（标题） |
| `leading-relaxed` | 宽松行高（正文） |
| `antialiased` | 抗锯齿渲染 |

---

## 3. 间距 (Spacing)

### 基础间距尺 (Base Scale)

| Token | Rem | Pixels | 常用场景 |
|-------|-----|--------|---------|
| `1` | `0.25rem` | 4px | 图标与文字间、标签内边距 |
| `2` | `0.5rem` | 8px | 小元素间距、紧凑卡片内边距 |
| `3` | `0.75rem` | 12px | 元素间间距、输入框内边距 |
| `4` | `1rem` | 16px | 标准间距、卡片内边距 |
| `5` | `1.25rem` | 20px | 大卡片内边距 |
| `6` | `1.5rem` | 24px | 区块间距、表单间距 |
| `8` | `2rem` | 32px | 大区块间距 |
| `10` | `2.5rem` | 40px | 页面内边距 |
| `12` | `3rem` | 48px | 页面节间距 |

### 响应式间距

```css
/* 移动端紧凑，桌面端宽松 */
.responsive-section { @apply space-y-4 sm:space-y-6 lg:space-y-8; }
.responsive-padding { @apply p-4 sm:p-6 lg:p-8; }
.responsive-card   { @apply p-4 sm:p-5 lg:p-6; }
```

---

## 4. 圆角 (Border Radius)

| Token | Value | 用途 |
|-------|-------|------|
| `rounded-lg` | `0.5rem` (8px) | 按钮、输入框、标签 |
| `rounded-xl` | `0.75rem` (12px) | 卡片、弹窗、面板 |
| `rounded-2xl` | `1rem` (16px) | 大卡片、页面容器 |
| `rounded-full` | `9999px` | 头像、圆点指示器 |

---

## 5. 阴影 (Shadows)

| Token | Value | 用途 |
|-------|-------|------|
| `shadow-sm` | `0 1px 2px 0 rgb(0 0 0 / 0.05)` | 卡片悬浮轻阴影 |
| `shadow-md` | `0 4px 6px -1px rgb(0 0 0 / 0.1)` | 卡片悬浮（hover） |
| `shadow-lg` | `0 10px 15px -3px rgb(0 0 0 / 0.1)` | 弹窗、下拉菜单 |
| `shadow-2xl` | `0 25px 50px -12px rgb(0 0 0 / 0.25)` | 模态框、分享面板 |
| `glow-pulse` | `0 0 20px rgba(14,165,233,0.15)` | 品牌脉冲发光 |

---

## 6. 动画 (Animations)

### 关键帧 (Keyframes)

| Name | Duration | Easing | 用途 |
|------|----------|--------|------|
| `slide-up` | `0.3s` | `ease-out` | 弹窗/面板从底部滑入 |
| `shimmer` | `1.5s` | `ease-in-out infinite` | 骨架屏加载闪烁 |
| `pulse-glow` | `3s` | `ease-in-out infinite` | 品牌元素发光脉冲 |
| `fadeIn` | `0.2s` | `ease-out` | 遮罩层淡入 |
| `spin` | `1s` | `linear infinite` | 加载旋转图标 |
| `slideInRight` | `0.3s` | `ease-out` | 抽屉从右侧滑入 |

### 过渡 (Transitions)

| Property | Duration | Easing | 用途 |
|----------|----------|--------|------|
| `all` | `200ms` | `ease` | 通用过渡（hover/active） |
| `colors` | `150ms` | `ease` | 颜色变化（文字/背景） |
| `transform` | `300ms` | `ease` | 侧边栏展开收起 |
| `opacity` | `200ms` | `ease` | 显示/隐藏 |
| `shadow` | `200ms` | `ease` | 卡片悬浮阴影过渡 |

---

## 7. 渐变 (Gradients)

| Name | 值 | 用途 |
|------|-----|------|
| `sky-gradient` | `linear-gradient(135deg, #0ea5e9 → #0369a1)` | 按钮/强调背景 |
| `brand-gradient` | `linear-gradient(135deg, #0ea5e9 → #2563eb → #7c3aed)` | 品牌渐变（Logo/图标） |
| `sky-gradient-light` | `linear-gradient(135deg, #f0f9ff → #e0f2fe)` | 轻量背景 |
| `login-mesh` | 多径向渐变组合 | 登录页网格背景 |
| `home-mesh` | 多径向渐变组合 | 首页网格背景 |

---

## 8. 响应式断点 (Breakpoints)

| Breakpoint | Min Width | 目标设备 |
|-----------|-----------|---------|
| `sm` | `640px` | 大屏手机/平板竖屏 |
| `md` | `768px` | 平板横屏 |
| `lg` | `1024px` | 小屏笔记本 |
| `xl` | `1280px` | 桌面显示器 |
| `2xl` | `1536px` | 大屏桌面 |

---

## 9. Z-Index 层级

| Value | 用途 |
|-------|------|
| `10` | 固定头部 (sticky header) |
| `40` | 下拉菜单、工具提示 |
| `50` | 模态框、弹窗 (modals) |
| `auto` | 默认层叠顺序 |

---

> 文档版本: v1.0
> 最后更新: 2026-07-01
> 维护人: Frontend Team
