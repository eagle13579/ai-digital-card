# 🎨 AI数智名片 — 设计系统规范 (MASTER)

> **版本**: v2.0  
> **设计语言**: Dark Minimal · Glassmorphism · Purple Accent  
> **参考**: Linear.app (ultra-minimal dark), Stripe (purple gradients), Vercel (black/white precision)  
> **改造日期**: 2026-07-12

---

## 1. 设计原则

| 原则 | 说明 |
|------|------|
| **少即是多** | 每屏只聚焦一个核心任务，去除冗余装饰 |
| **暗色基调** | #0f0f1a 为主背景，减少视觉眩光，聚焦内容 |
| **玻璃质感** | 统一 backdrop-filter: blur(20px) 磨砂玻璃层 |
| **紫色点睛** | #8b5cf6 为主色调，克制使用，强调交互区域 |
| **信息分层** | 通过透明度(tier-1/2/3)区分信息层级，而非颜色 |

---

## 2. 色彩系统 (Color Tokens)

### 2.1 语义色板

```css
/* ===== Surface / Background ===== */
--surface-primary:   #0f0f1a;   /* 主背景 */
--surface-secondary: #1a1a2e;   /* 卡片/区块背景 */
--surface-tertiary:  #252540;   /* 浮层/模态背景 */
--surface-glass:     rgba(30, 30, 50, 0.6);   /* 磨砂玻璃 */
--surface-glass-strong: rgba(30, 30, 50, 0.95); /* 强磨砂 */

/* ===== Accent (紫色主色调) ===== */
--accent:           #8b5cf6;    /* 交互主色 */
--accent-light:     #a78bfa;    /* 悬停/轻量强调 */
--accent-dark:      #6d28d9;    /* 深紫(极少使用) */
--accent-gradient:  linear-gradient(135deg, #8b5cf6, #06b6d4);
--accent-gradient-warm: linear-gradient(135deg, #a78bfa, #8b5cf6);

/* ===== Text ===== */
--text-primary:     #ffffff;
--text-secondary:   rgba(255, 255, 255, 0.72);
--text-tertiary:    rgba(255, 255, 255, 0.45);
--text-disabled:    rgba(255, 255, 255, 0.2);

/* ===== Border ===== */
--border-subtle:    rgba(255, 255, 255, 0.06);
--border-default:   rgba(255, 255, 255, 0.1);
--border-strong:    rgba(255, 255, 255, 0.18);

/* ===== Semantic ===== */
--success:          #22c55e;
--warning:          #f59e0b;
--danger:           #ef4444;
--info:             #06b6d4;

/* ===== Elevation / Shadow ===== */
--shadow-sm:  0 2px 8px  rgba(0, 0, 0, 0.2);
--shadow-md:  0 4px 16px rgba(0, 0, 0, 0.25);
--shadow-lg:  0 8px 32px rgba(0, 0, 0, 0.35);
--shadow-glow: 0 0 20px rgba(139, 92, 246, 0.3);
```

### 2.2 渐变预设

```css
--gradient-accent:    linear-gradient(135deg, #8b5cf6 0%, #06b6d4 100%);
--gradient-warm:      linear-gradient(135deg, #a78bfa 0%, #8b5cf6 100%);
--gradient-success:   linear-gradient(135deg, #22c55e 0%, #10b981 100%);
--gradient-danger:    linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
--gradient-card:      linear-gradient(135deg, rgba(139,92,246,0.12), rgba(6,182,212,0.08));
--gradient-header:    linear-gradient(135deg, rgba(139,92,246,0.08), rgba(6,182,212,0.04));
```

---

## 3. 字体系统 (Typography)

### 3.1 字号梯级

| Token | Size | Weight | 用途 |
|-------|------|--------|------|
| --text-xs | 11px | 400/500 | 辅助文字/标签 |
| --text-sm | 13px | 400/500 | 副信息/说明 |
| --text-base | 15px | 400 | 正文内容 |
| --text-lg | 18px | 600 | 卡片标题/列表项 |
| --text-xl | 24px | 700 | 页面大标题 |
| --text-2xl | 32px | 700 | 品牌/数字强调 |

### 3.2 字重

```css
--weight-regular: 400;
--weight-medium: 500;
--weight-semibold: 600;
--weight-bold: 700;
```

### 3.3 字体栈

```css
font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display',
  'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei',
  'Helvetica Neue', sans-serif;
```

---

## 4. 间距系统 (Spacing)

基于 4px 递进的原子化间距：

| Token | Value |
|-------|-------|
| --space-1 | 4px |
| --space-2 | 8px |
| --space-3 | 12px |
| --space-4 | 16px |
| --space-5 | 20px |
| --space-6 | 24px |
| --space-8 | 32px |
| --space-10 | 40px |
| --space-12 | 48px |

---

## 5. 圆角系统 (Radius)

| Token | Value | 用途 |
|-------|-------|------|
| --radius-sm | 8px | 按钮/输入框 |
| --radius-md | 12px | 常规卡片 |
| --radius-lg | 16px | 高级卡片/弹窗 |
| --radius-xl | 20px | 特殊容器 |
| --radius-full | 999px | 头像/胶囊标签 |

---

## 6. 组件规范

### 6.1 磨砂玻璃卡片 (.glass-card)

```css
.glass-card {
  background: var(--surface-glass);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
}
```

### 6.2 主按钮 (.btn-primary)

```css
.btn-primary {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 48px;
  background: var(--gradient-accent);
  color: #fff;
  font-size: var(--text-base);
  font-weight: var(--weight-semibold);
  border-radius: var(--radius-sm);
  border: none;
  width: 100%;
}
.btn-primary:active {
  opacity: 0.85;
  transform: scale(0.98);
}
```

### 6.3 次要按钮 (.btn-secondary)

```css
.btn-secondary {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid var(--border-default);
  color: var(--text-primary);
  border-radius: var(--radius-sm);
  height: 48px;
}
```

### 6.4 信息行 / 菜单行

```css
.info-row, .menu-item {
  padding: 14px 16px;
  border-bottom: 1px solid var(--border-subtle);
}
```

### 6.5 图标系统

**所有 emoji 图标必须替换**为以下方式之一：
1. **SVG 内联图标** — 用于关键操作图标（编辑、分享、扫码等）
2. **Unicode 符号** — 用于通用符号（箭头 › ✓ ✕）
3. **纯 CSS 图标** — 用于简单指示器（圆点、线条）

---

## 7. 页面布局规范

### 7.1 页面容器

```css
.page-container {
  min-height: 100vh;
  background: var(--surface-primary);
  color: var(--text-primary);
}
```

### 7.2 滚动容器

```css
.page-scroll {
  height: 100vh;
}
```

### 7.3 头部导航

```css
.page-header {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-subtle);
}
```

### 7.4 列表项

```css
.list-item {
  display: flex;
  align-items: center;
  padding: 14px 16px;
  background: var(--surface-glass);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  margin-bottom: 8px;
}
```

---

## 8. 组件清单

| 组件 | 状态 | 改造要点 |
|------|------|----------|
| loading | ✅ 改造完成 | 紫色调 spinner，适配暗色 |
| empty-state | ✅ 改造完成 | 适配暗色背景 |
| card-item | ✅ 改造完成 | 暗色卡片 + 磨砂玻璃 |
| network-mini-map | ✅ 改造完成 | 暗色图谱容器 |
| path-display | ✅ 改造完成 | 暗色弹窗 + 紫调 |
| visibility-selector | ✅ 改造完成 | 暗色选择器 |

---

## 9. 页面状态矩阵

| 页面 | 状态 | 主要改动 |
|------|------|----------|
| 登录页 (login) | ✅ 已暗色 | 保持原来暗色设计，优化间距 |
| 首页 (index) | ✅ 改造 | 亮→暗，替换emoji，玻璃卡片 |
| 名片 (card) | ✅ 改造 | 亮→暗，替换emoji，磨砂英雄区 |
| 我的 (profile) | ✅ 改造 | 亮→暗，替换emoji，菜单统一 |
| AI中心 (ai/index) | ✅ 改造 | 亮→暗，网格卡片优化 |
| AI聊天 (ai/chat) | ✅ 保持 | 已暗色，优化间距 |
| AI匹配 (ai/match) | ✅ 改造 | 亮→暗，过滤栏磨砂 |
| AI洞察 (ai/insight) | ✅ 改造 | 亮→暗，数据卡片玻璃化 |
| AI扫码 (ai/scan) | ✅ 保持 | 已暗色，微调 |
| AI生成 (ai/generate) | ✅ 改造 | 亮→暗，表单适配 |
| AI配置 (ai/config) | ✅ 改造 | 亮→暗，开关适配 |
| 盖娅大脑 (ai/gaia) | ✅ 改造 | 亮→暗，统一设计语言 |
| 画册创建 (brochure/create) | ✅ 改造 | 亮→暗，表单重设计 |
| 画册预览 (brochure/preview) | ✅ 保持 | 已有暗色感 |
| 平台创建 (platform/create) | ✅ 保持 | 已有暗色 |
| 平台管理 (platform/manage) | ✅ 保持 | 已有暗色 |
| 信任图谱 (network/graph) | ✅ 保持 | 已有暗色 |
| 二维码 (qrcode) | ✅ 改造 | 亮→暗 |
| 会员中心 (membership) | ✅ 改造 | 亮→暗 |
| 隐私协议 (agreement) | ✅ 改造 | 亮→暗 |

---

## 10. 迁移指南

### 10.1 替换模式

```
❌ emoji 图标 (✏️ 👁️ 📱 🤖 📤)
✅ 统一使用 SVG / Unicode 符号 / CSS 图标
```

### 10.2 颜色迁移

```
❌ 旧: #1657ff, #1a1a1a, #666, #999, #f5f6fa
✅ 新: var(--accent), var(--text-primary), var(--text-secondary), var(--text-tertiary), var(--surface-primary)
```

### 10.3 卡片迁移

```
❌ 旧: .card { background: #fff; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
✅ 新: .glass-card { background: var(--surface-glass); backdrop-filter: blur(20px); border: 1px solid var(--border-subtle); }
```

---

## 11. 设计决策记录 (ADR)

| ADR | 决策 | 理由 |
|-----|------|------|
| 001 | 统一暗色主题 | 商务社交产品适合沉浸式暗色体验，减少视觉噪音 |
| 002 | 紫色为主色调 | 代表信任/智慧/高端，契合AI赋能社交场景 |
| 003 | 玻璃态卡片 | 增加层次感而不增加重量，Linear.app 验证有效 |
| 004 | 不再使用emoji做图标 | 专业产品应使用语义化图标系统 |
| 005 | 全局CSS变量 | 方便未来主题切换（如用户自定义颜色） |
| 006 | 克制使用渐变 | 只在关键CTA和品牌区域使用，避免过度装饰 |
