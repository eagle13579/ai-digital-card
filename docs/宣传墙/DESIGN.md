# AI 数智名片 · 宣传墙设计系统 v3.0

> 设计系统版本: v3.0 · AI时尚版
> 创建日期: 2026-07-05
> 设计来源: Replicate × ElevenLabs × RunwayML 融合
> 风格定位: AI-native Dark · 霓虹渐变 · 玻璃质感

---

## 1. 设计理念

不再做"企业科技"风格（Stripe/Vercel那套），而是真正的AI原生审美：
- **暗色为画布** — 不是节省墨水，是让内容从黑暗中发光
- **霓虹三重奏** — 青→紫→粉 三色渐变系统贯穿全场
- **玻璃质感** — backdrop-filter blur 让卡片有深度和呼吸感
- **扫描线/网格** — 数字化基底的可见质感
- **发光文字** — 核心数据用gradient text + drop-shadow glow

---

## 2. 颜色系统

### 2.1 背景色板

| Token | HEX | 角色 |
|:------|:----|:------|
| `--bg-deep` | `#0a0a18` | 最深的画布底色 |
| `--bg-mid` | `#0d0d24` | 中间过渡色 |
| `--bg-surface` | `rgba(255,255,255,0.02)` | 玻璃卡片基底 |
| `--bg-glass` | `rgba(255,255,255,0.03)` | 标准玻璃卡片 |
| `--bg-glass-hover` | `rgba(255,255,255,0.05)` | 悬停玻璃卡片 |
| `--bg-card-cyan` | `rgba(6,182,212,0.04)` | 青色调玻璃卡片 |
| `--bg-card-purple` | `rgba(139,92,246,0.06)` | 紫色调玻璃悬停 |

### 2.2 霓虹渐变系统

| Token | 渐变方向 | 色值 |
|:------|:---------|:------|
| `--gradient-primary` | 135deg | `#06b6d4` (Cyan) → `#8b5cf6` (Purple) |
| `--gradient-triple` | 135deg | `#06b6d4` → `#8b5cf6` → `#ec4899` |
| `--gradient-text` | 135deg | `#f4f4f5` → `#22d3ee` → `#c084fc` (白色→青→紫渐变文字) |
| `--gradient-revenue` | 135deg | `#06b6d4` → `#22d3ee` → `#8b5cf6` (营收数字) |
| `--gradient-badge-A` | 135deg | `#ec4899` → `#8b5cf6` (合作伙伴标签) |
| `--gradient-badge-B` | 135deg | `#f59e0b` → `#fbbf24` (招商B标签) |

### 2.3 光晕系统

| Token | 颜色 | 模糊 | 大小 | 位置 |
|:------|:-----|:-----|:------|:------|
| `--orb-1` | `rgba(6,182,212,0.10)` → `rgba(139,92,246,0.05)` | 40px | 700×700px | 左上 25%,20% |
| `--orb-2` | `rgba(236,72,153,0.08)` → `rgba(139,92,246,0.04)` | 60px | 500×500px | 右下 60%,15% |
| `--orb-3` | `rgba(6,182,212,0.06)` → transparent | 50px | 400×400px | 底部中间 |

### 2.4 文字颜色

| Token | HEX | 角色 |
|:------|:----|:------|
| `--text-primary` | `#f4f4f5` or `rgba(255,255,255,0.95)` | 主要文字（接近纯白） |
| `--text-secondary` | `#a1a1aa` / `#d4d4d8` | 次要文字（灰色） |
| `--text-tertiary` | `#71717a` | 第三级文字 |
| `--text-muted` | `#52525b` | 最淡文字（元数据/版本号） |
| `--text-cyan` | `#22d3ee` | 青色强调 |
| `--text-purple` | `#c084fc` / `#a78bfa` | 紫色强调 |
| `--text-pink` | `#f472b6` | 粉色强调 |
| `--text-amber` | `#fbbf24` | 琥珀色强调 |

### 2.5 边框颜色

| Token | 值 |
|:------|:----|
| `--border-glass` | `rgba(255,255,255,0.04)` |
| `--border-glass-mid` | `rgba(255,255,255,0.06)` |
| `--border-cyan` | `rgba(6,182,212,0.12)` |
| `--border-purple` | `rgba(139,92,246,0.08)` |
| `--border-pink` | `rgba(236,72,153,0.15)` |

### 2.6 横幅头部色条（5色区分）

| 横幅 | 渐变 | 含义 |
|:-----|:------|:------|
| B1 品牌 | `#06b6d4` → `#22d3ee` | 青色 · 品牌信任 |
| B2 AI引擎 | `#8b5cf6` → `#a78bfa` | 紫色 · 技术智能 |
| B3 营收 | `#ec4899` → `#f472b6` | 粉色 · 商业变现 |
| B4 招商 | `#f59e0b` → `#fbbf24` | 琥珀 · 合作机会 |
| B5 壁垒 | `#06b6d4` → `#8b5cf6` | 青紫 · 技术护城河 |

---

## 3. 字体系统

### 3.1 字体家族

| 角色 | 字体 | 后备 |
|:-----|:------|:------|
| 英文标题/数据 | Geist | system-ui, sans-serif |
| 技术标签/代码 | Geist Mono | ui-monospace, monospace |
| 中文正文 | Noto Sans SC | 系统黑体 |
| 数字/金额 | Geist (权重700-900) | — |

### 3.2 字号层级

| 角色 | 大小 | 字重 | 行高 | 字距 | 备注 |
|:-----|:-----|:-----|:-----|:------|:------|
| 主墙标题 | 17-22px | 700-800 | 1.3 | -0.88px | Geist + Noto Sans SC |
| 引擎网格名称 | 7-7.5px | 600 | — | -0.1px | 极小但清晰 |
| 营收数字 | 13-20px | 800-900 | 1 | -1px | Geist weight 900 |
| 数据指标(10亿/200+) | 26px | 800 | 1 | -1.3px | Geist |
| 竖幅标题 | 11-12px | 700 | — | -0.24px | Geist |
| 竖幅数据 | 8-15px | 700-900 | — | -0.7px | Geist weight 800+ |
| 元数据标签 | 5.5-6.5px | 400-500 | — | 0.3-0.5px | Geist Mono uppercase |
| 区段标签 | 7px | 500 | — | 2px | Geist Mono uppercase |

### 3.3 Geist权重表

| 权重 | CSS值 | 用途 |
|:-----|:------|:------|
| Light | 300 | 极少数超大字重场合 |
| Regular | 400 | 小字/元数据 |
| Medium | 500 | 标签/标签强调 |
| Semibold | 600 | 次要数据/强调 |
| Bold | 700 | 标题/区域标题 |
| Extrabold | 800 | 核心数据/大标题 |
| Black | 900 | 仅营收数字 ¥7.25B |

---

## 4. 阴影 & 深度

| 层级 | CSS | 用途 |
|:-----|:-----|:------|
| 外框阴影 | `rgba(6,182,212,0.1) 0px 30px 60px -20px` | Wall主容器 |
| 玻璃卡片 | 无阴影，靠border + backdrop-blur | 所有卡片 |
| 玻璃悬停 | `0 0 30px rgba(6,182,212,0.05)` + 微升 -3px | 5个竖幅 hover |
| 发光文字 | `filter: drop-shadow(0 0 12px rgba(6,182,212,0.2))` | 营收总金额 ¥7.25B |
| Logo发光 | `box-shadow: 0 0 16px rgba(6,182,212,0.2)` | 品牌logo |
| Logo外层辉光 | `filter: blur(8px)` on ::before | logo光晕 |

**核心理念**: 不使用传统CSS阴影（如Stripe的实体阴影）。AI时尚版用**发光代替阴影**——glow over shadow。

---

## 5. 圆角体系

| 角色 | 值 | 用途 |
|:-----|:----|:------|
| 主容器 | 24px | Wall外框 |
| 区段卡片 | 10-12px | 收入卡片/Z2卡片 |
| 引擎网格项 | 10px | 8个引擎网格 |
| 竖幅 | 16px | 5个宣传横幅 |
| 头像/标签 | 9999px (pill) | 标签/徽章 |
| Logo | 18px | 品牌logo |
| 圆图标 | 6-8px | 小图标/指标点 |
| 分割线渐变 | 2px | 装饰用细线 |

---

## 6. 玻璃质感（Glass Morphism）

### 6.1 标准玻璃卡片

```css
backdrop-filter: blur(12px);
-webkit-backdrop-filter: blur(12px);
background: rgba(255,255,255,0.03);
border: 1px solid rgba(255,255,255,0.06);
border-radius: 12px;
```

### 6.2 薄玻璃（用于网格项/小元素）

```css
backdrop-filter: blur(8px);
-webkit-backdrop-filter: blur(8px);
background: rgba(255,255,255,0.03);
border: 1px solid rgba(255,255,255,0.05);
```

### 6.3 极薄玻璃（用于列表项/标签）

```css
backdrop-filter: blur(6px);
background: rgba(255,255,255,0.02);
border: 1px solid rgba(255,255,255,0.04);
```

---

## 7. 网格系统

### 7.1 背景科技网格

```css
background-image:
  linear-gradient(rgba(6,182,212,0.04) 1px, transparent 1px),
  linear-gradient(90deg, rgba(6,182,212,0.04) 1px, transparent 1px);
background-size: 72px 72px;
```

### 7.2 扫描线

```css
background: repeating-linear-gradient(
  0deg,
  transparent,
  transparent 2px,
  rgba(6,182,212,0.015) 2px,
  rgba(6,182,212,0.015) 4px
);
```

### 7.3 布局网格（5区分布）

| 区段 | 宽度 | 内容 |
|:-----|:-----|:------|
| Z1 品牌 | 16% | Logo + 品牌名 |
| Z2 核心信息 | 24% | 纸片→AI升级叙事 |
| Z3 AI引擎群 | 32% | 8引擎网格 + 营收三卡 |
| Z4 数据+招商 | 20% | 10亿/200+数据 + ABCD合作 |
| Z5 竖排slogan | 8% | "让10亿人的名片活过来" |

---

## 8. 间距系统

| Token | 值 | 用途 |
|:------|:----|:------|
| --space-unit | 4px | 最小粒度 |
| --space-xs | 8px | 小间距 |
| --space-sm | 12px | 元素间距 |
| --space-md | 16px | 区段间间距 |
| --space-lg | 24px | 大间距 |
| --space-xl | 40px | 容器外边距 |

---

## 9. 动效规则

| 元素 | 属性 | 时长 | 缓动 |
|:-----|:------|:-----|:------|
| 卡片 hover | transform: translateY(-3px) + box-shadow | 0.35s | ease |
| 引擎网格 hover | background + border-color + box-shadow | 0.25s | ease |
| 竖幅 hover | transform + box-shadow | 0.35s | ease |

---

## 10. 组件规格

### 10.1 品牌Logo

```
尺寸: 64×64px
圆角: 18px
背景: linear-gradient(135deg, #06b6d4, #8b5cf6)
外层辉光: 4px扩散滤镜模糊
内部高光: rgba(255,255,255,0.15)
文字: "AI" · Geist weight 800 · 20px · 白色
```

### 10.2 营收卡片（3列）

```
背景: rgba(6,182,212,0.04) + 1px border
顶部色条: 2px · cyan→purple→pink渐变
数字: Geist weight 800 · 渐变cyan→purple→pink
标签: Geist Mono · 6px · #71717a · uppercase
```

### 10.3 合作伙伴标签（ABCD）

```
圆角: 9999px (pill)
背景: linear-gradient(135deg, #ec4899, #8b5cf6)
文字: white · 5.5px · Geist Mono weight 700
间距: 1px 4px
```

### 10.4 竖幅规格（×5）

```
尺寸比例: 1/3 (宽:高)
圆角: 16px
底色: rgba(255,255,255,0.03) · backdrop-blur(16px)
头部色条: 3px · 5色区分
悬停: translateY(-3px) · 30px glow box-shadow
```

---

## 11. 使用指南

### 11.1 不要做的事（Anti-Slop规则）

| ❌ 禁止 | 原因 |
|:--------|:------|
| 浅色/白色背景 | 不是AI公司的语言 |
| 使用默认AI紫色渐变 (#7c3aed) | 太普通 |
| 在暗色上使用纯白文字 (#ffffff) | 太刺眼，用 #f4f4f5 |
| 使用传统CSS阴影 | 用 glow 代替 shadow |
| 使用emoji做图标 | 用几何符号 ◈◇◆✦ 代替 |
| 在深色上使用柔和pastel色 | AI时尚版用饱和色 |
| 扁平设计（无玻璃质感） | 必须有 backdrop-filter blur |
| 正字距大标题 | Geist必须用负字距 |

### 11.2 场景决策树

```
这个元素是：
├─ 品牌标识 → 用渐变cyan→purple + 辉光
├─ 核心数据 → 用Geist weight 800+ + 渐变文字 + drop-shadow glow
├─ 技术标签 → 用Geist Mono uppercase + 极小字号 + 有色强调
├─ 卡片容器 → 用玻璃质感 backdrop-blur(12px)
├─ 分隔装饰 → 用透明到渐变色的细线
└─ 数字/金额 → 用Geist + 负字距 + 渐变文字
```

### 11.3 字号关系

- 大字号越大越好（20px的¥7.25B）
- 小字号越小越好（5.5px的元数据）
- 数据用最重字重（800-900）
- 标签用最轻字重（400-500）

---

## 12. 文件索引

| 版本 | 文件名 | 说明 |
|:-----|:-------|:------|
| v1.0 | `宣传墙+5竖幅_实际画面.html` | 原始版本（浅色） |
| v2.0 | `宣传墙+5竖幅_v2_科技进化版.html` | 科技版（Stripe×Vercel×Linear） |
| v3.0 | `宣传墙+5竖幅_v3_AI时尚版.html` | AI时尚版（当前·推荐用于印刷） |
| — | `DESIGN.md` | 本文件 — 设计Token文档 |

---

## 13. 灵感来源

| 来源 | 应用到 |
|:------|:--------|
| **Replicate** (±43k GitHub) | 霓虹渐变hero能量、pill形状标签、developer能量感、爆裂渐变 |
| **ElevenLabs** (±31k) | 温和的暗色处理、精细的视觉层次、品牌logo处理方式 |
| **RunwayML** (±38k) | 电影感暗色基底、界面隐形化、让视觉内容成为主角 |
| **Taste-Skill** (±42.8k) | Anti-Slop规则、3-Dial控制(拒绝默认模式) |
| **Geist** (Vercel设计系统) | 字体系统、极端负字距压缩 |

---

> 设计Token文档完毕 · 可喂给任何AI设计系统使用
> 推荐用于: Midjourney/SD提示词生成 · Cursor Copilot · GPT-4V设计分析 · Figma Tokens Studio
