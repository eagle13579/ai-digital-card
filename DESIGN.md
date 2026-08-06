# AI数字名片 — 设计Token体系文档 (v1.0)

> **作者**: 山膏 (P8视觉设计师)  
> **方向**: AI原生暗色 · 冷峻轻奢  
> **基底**: AI数字名片微信小程序 · 首页  
> **日期**: 2026-07-08

---

## 1. 设计方向说明

### 方向锁定：AI原生暗色

基于蜂巢PRD的方向决策，首页采用**AI原生暗色方向**，设计哲学如下：

| 维度 | 原则 | 描述 |
|------|------|------|
| **调性** | 冷峻轻奢 | 非纯黑，非高饱和，克制留白 |
| **光源** | 自发光 | 光晕(Orb)替代传统阴影，内容自带微光 |
| **质感** | 玻璃三层 | 磨砂玻璃 + 光晕透射 + 边缘高光 |
| **色彩** | 三重渐变 | 青→紫→粉 (cyan→purple→pink)，低饱和扩散 |
| **字体** | 几何 + 人文 | Geist (英文数字) + Noto Sans SC (中文) |
| **动效** | 弹簧物理 | `cubic-bezier(0.34, 1.56, 0.64, 1)` 弹性出轴 |

### AI原生方向参考

- **Replicate**: 暗色基底 + 霓虹光晕 + 极简信息层级
- **ElevenLabs**: 深色毛玻璃 + 声波动效 + 高对比字体
- **RunwayML**: 暗色调色板 + 光晕悬浮 + 卡片无边框设计

---

## 2. 色彩Token体系

### 2.1 基底色（Surface/BG）

| CSS变量 | HEX值 | 角色说明 |
|---------|-------|----------|
| `--bg-page` | `#0A0A18` | 页面最底层，深邃夜空 |
| `--bg-elevated` | `#0F0F13` | 卡片/面板承载面 |
| `--bg-overlay` | `#141418` | 弹出层/模态背景 |
| `--bg-glass-1` | `rgba(255,255,255,0.04)` | 玻璃层1-超薄 |
| `--bg-glass-2` | `rgba(255,255,255,0.07)` | 玻璃层2-薄 |
| `--bg-glass-3` | `rgba(255,255,255,0.12)` | 玻璃层3-中厚 |
| `--bg-hover` | `rgba(255,255,255,0.06)` | 悬浮态底纹 |
| `--bg-active` | `rgba(255,255,255,0.10)` | 按下态底纹 |

### 2.2 渐变系统（三重渐变）

| CSS变量 | 渐变值 | 角色说明 |
|---------|--------|----------|
| `--gradient-primary` | `linear-gradient(135deg, #06b6d4, #8b5cf6, #ec4899)` | 主品牌渐变 */
| `--gradient-cyan-purple` | `linear-gradient(135deg, #06b6d4, #8b5cf6)` | AI卡片头部/按钮 */
| `--gradient-purple-pink` | `linear-gradient(135deg, #8b5cf6, #ec4899)` | 高亮/强调入口 */
| `--gradient-cyan-only` | `linear-gradient(135deg, #06b6d4, #22d3ee)` | 数字/统计数据 */
| `--gradient-glow` | `radial-gradient(ellipse at center, rgba(139,92,246,0.3), rgba(6,182,212,0.1), transparent)` | 光晕Orb扩散 */

### 2.3 单色系统

| CSS变量 | HEX值 | 角色说明 |
|---------|-------|----------|
| `--cyan` | `#06b6d4` | 主色-青色（科技感） |
| `--cyan-light` | `#22d3ee` | 主色-青淡 |
| `--cyan-dark` | `#0891b2` | 主色-青深 |
| `--purple` | `#8b5cf6` | 主色-紫色（AI感） |
| `--purple-light` | `#a78bfa` | 主色-紫淡 |
| `--purple-dark` | `#7c3aed` | 主色-紫深 |
| `--pink` | `#ec4899` | 主色-粉色（温度感） |
| `--pink-light` | `#f472b6` | 主色-粉淡 |
| `--success` | `#10b981` | 成功/匹配 |
| `--warning` | `#f59e0b` | 警告/升级提示 |
| `--danger` | `#ef4444` | 错误/危险 |

### 2.4 文字色

| CSS变量 | 值 | 角色说明 |
|---------|------|----------|
| `--text-primary` | `rgba(255,255,255,0.92)` | 主标题/重要内容 |
| `--text-secondary` | `rgba(255,255,255,0.65)` | 正文/副标题 |
| `--text-tertiary` | `rgba(255,255,255,0.40)` | 辅助说明/时间 |
| `--text-quaternary` | `rgba(255,255,255,0.20)` | 禁用态/占位符 |
| `--text-inverse` | `#0A0A18` | 在渐变/高亮背景上的文字 |
| `--text-accent` | `#a78bfa` | 高亮强调文字 |

### 2.5 边框/分割线

| CSS变量 | 值 | 角色说明 |
|---------|------|----------|
| `--border-subtle` | `rgba(255,255,255,0.06)` | 最细分割线 |
| `--border-default` | `rgba(255,255,255,0.10)` | 默认边框 |
| `--border-accent` | `rgba(139,92,246,0.25)` | 强调边框（紫光） |
| `--border-cyan` | `rgba(6,182,212,0.25)` | 强调边框（青光） |

---

## 3. 字体Token

### 3.1 字族

| CSS变量 | 值 | 角色说明 |
|---------|------|----------|
| `--font-sans` | `'Geist', -apple-system, BlinkMacSystemFont, sans-serif` | 英文/数字默认 |
| `--font-mono` | `'Geist Mono', 'SF Mono', 'Fira Code', monospace` | 代码/数据/数字 |
| `--font-sc` | `'Noto Sans SC', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif` | 中文正文 |
| `--font-system` | `var(--font-sans), var(--font-sc)` | 系统堆叠 |

### 3.2 字号与字重

| Token名 | 字号 | 行高 | 字重 | 使用场景 |
|---------|------|------|------|----------|
| `--text-xs` | 20rpx | 1.4 | 400 | 标签/附加信息 |
| `--text-sm` | 24rpx | 1.5 | 400 | 辅助文字/时间 |
| `--text-base` | 28rpx | 1.6 | 400 | 正文 |
| `--text-lg` | 32rpx | 1.5 | 500 | 卡片标题/列表项 |
| `--text-xl` | 36rpx | 1.4 | 600 | 小标题/统计数字 |
| `--text-2xl` | 40rpx | 1.3 | 700 | 用户名/大标题 |
| `--text-3xl` | 48rpx | 1.2 | 700 | 数字突出/首页主标 |
| `--text-4xl` | 56rpx | 1.1 | 800 | 特大数字/分数 |

### 3.3 字距

| CSS变量 | 值 | 使用场景 |
|---------|------|----------|
| `--tracking-tight` | `-0.01em` | 标题（紧凑） |
| `--tracking-normal` | `0` | 正文 |
| `--tracking-wide` | `0.02em` | 辅助文字/按钮 |
| `--tracking-wider` | `0.05em` | 标签/徽章 |

---

## 4. 玻璃质感三层体系

AI数字名片的卡片系统采用"三层玻璃"结构，从底部到顶部依次为：

### 层1：基底玻璃（Glass Base）
```
background: rgba(255, 255, 255, 0.04);
backdrop-filter: blur(20px);
border: 0.5px solid rgba(255, 255, 255, 0.06);
```
- 用于页面背景区、大面板

### 层2：表面玻璃（Glass Surface）  
```
background: rgba(255, 255, 255, 0.07);
backdrop-filter: blur(30px);
border: 0.5px solid rgba(255, 255, 255, 0.10);
```
- 用于卡片容器、操作栏

### 层3：强调玻璃（Glass Accent）
```
background: rgba(139, 92, 246, 0.12);
backdrop-filter: blur(40px);
border: 0.5px solid rgba(139, 92, 246, 0.20);
box-shadow: 0 0 20px rgba(139, 92, 246, 0.15);
```
- 用于AI入口卡、高亮卡片

### 层外：毛边微光（Edge Glow）
所有玻璃层在顶部边缘有微光：
```
box-shadow: inset 0 0.5px 0 rgba(255, 255, 255, 0.08);
```

### Token化参数

| CSS变量 | 值 | 说明 |
|---------|------|------|
| `--glass-bg-1` | `rgba(255,255,255,0.04)` | 玻璃层1背景 |
| `--glass-bg-2` | `rgba(255,255,255,0.07)` | 玻璃层2背景 |
| `--glass-bg-3` | `rgba(139,92,246,0.12)` | 玻璃层3背景 |
| `--glass-blur-1` | `20px` | 玻璃层1模糊 |
| `--glass-blur-2` | `30px` | 玻璃层2模糊 |
| `--glass-blur-3` | `40px` | 玻璃层3模糊 |
| `--glass-border-1` | `0.5px solid rgba(255,255,255,0.06)` | 玻璃层1边框 |
| `--glass-border-2` | `0.5px solid rgba(255,255,255,0.10)` | 玻璃层2边框 |
| `--glass-border-3` | `0.5px solid rgba(139,92,246,0.20)` | 玻璃层3边框 |
| `--glass-glow-edge` | `inset 0 0.5px 0 rgba(255,255,255,0.08)` | 边缘高光 |

---

## 5. 光晕Orb系统

光晕(Orb)替代传统CSS阴影，制造"自发光"的AI原生质感。

### 5.1 标准Orb Tokens

| CSS变量 | 值 | 说明 |
|---------|------|------|
| `--orb-sm` | `0 0 12px rgba(139,92,246,0.15)` | 小光晕（按钮/标签） |
| `--orb-md` | `0 0 24px rgba(139,92,246,0.20)` | 中光晕（卡片） |
| `--orb-lg` | `0 0 40px rgba(139,92,246,0.25)` | 大光晕（AI入口） |
| `--orb-xl` | `0 0 60px rgba(6,182,212,0.20)` | 特大光晕（页面头部） |
| `--orb-cyan` | `0 0 20px rgba(6,182,212,0.20)` | 青色光晕 |
| `--orb-pink` | `0 0 20px rgba(236,72,153,0.20)` | 粉色光晕 |
| `--orb-hover` | `0 0 30px rgba(139,92,246,0.35)` | 悬浮态增强光晕 |

### 5.2 动态Orb动画

首页背景使用`radial-gradient`制造Orb扩散效果：

```css
/* 背景Orb */
.orb-bg {
  background: 
    radial-gradient(ellipse 600rpx 400rpx at 20% 30%, rgba(6,182,212,0.12), transparent),
    radial-gradient(ellipse 500rpx 500rpx at 70% 60%, rgba(139,92,246,0.10), transparent),
    radial-gradient(ellipse 400rpx 300rpx at 50% 80%, rgba(236,72,153,0.08), transparent);
}

/* 浮动Orb动画 */
@keyframes orb-float {
  0%, 100% { transform: translateY(0) scale(1); opacity: 0.6; }
  50% { transform: translateY(-15rpx) scale(1.05); opacity: 1; }
}
```

---

## 6. 间距/圆角/阴影Token

### 6.1 间距 (Spacing)

| CSS变量 | rpx值 | px值(750设计稿) | 场景 |
|---------|-------|-----------------|------|
| `--space-1` | 4rpx | 2px | 微间距 |
| `--space-2` | 8rpx | 4px | 紧凑间距 |
| `--space-3` | 12rpx | 6px | 元素间距 |
| `--space-4` | 16rpx | 8px | 内边距xs |
| `--space-5` | 20rpx | 10px | 内边距sm |
| `--space-6` | 24rpx | 12px | 内边距md |
| `--space-8` | 32rpx | 16px | 内边距lg |
| `--space-10` | 40rpx | 20px | 内边距xl |
| `--space-12` | 48rpx | 24px | 卡片间距 |
| `--space-16` | 64rpx | 32px | 区块间距 |
| `--space-20` | 80rpx | 40px | 大区块间距 |

### 6.2 圆角 (Border Radius)

| CSS变量 | rpx值 | 场景 |
|---------|-------|------|
| `--radius-xs` | 8rpx | 标签/徽章 |
| `--radius-sm` | 12rpx | 按钮/输入框 |
| `--radius-md` | 16rpx | 普通卡片 |
| `--radius-lg` | 24rpx | 大卡片/AI入口 |
| `--radius-xl` | 32rpx | 操作栏/弹窗 |
| `--radius-full` | 9999rpx | 圆形/药丸形 |

### 6.3 阴影 → 已由Orb取代

AI原生暗色方向**不**使用传统CSS阴影（`box-shadow`），统一由Orb光晕系统替代。唯一保留的传统阴影是毛玻璃的内阴影微光：

| CSS变量 | 值 | 场景 |
|---------|------|------|
| `--shadow-glass-edge` | `inset 0 0.5px 0 rgba(255,255,255,0.08)` | 玻璃层边缘高光 |
| `--shadow-glass-inner` | `inset 0 1px 0 rgba(255,255,255,0.04)` | 玻璃层内反射 |

---

## 7. 动效Token

### 7.1 曲线定义

| CSS变量 | cubic-bezier值 | 命名 | 感觉 |
|---------|---------------|------|------|
| `--ease-spring` | `cubic-bezier(0.34, 1.56, 0.64, 1)` | 弹簧 | 弹性回弹 |
| `--ease-out` | `cubic-bezier(0, 0, 0.2, 1)` | 缓出 | 自然消退 |
| `--ease-in` | `cubic-bezier(0.4, 0, 1, 1)` | 缓入 | 加速进入 |
| `--ease-in-out` | `cubic-bezier(0.4, 0, 0.2, 1)` | 缓入缓出 | 标准过渡 |

### 7.2 时长定义

| CSS变量 | ms值 | 场景 |
|---------|------|------|
| `--duration-fast` | 150ms | 悬浮/按下态 |
| `--duration-normal` | 250ms | 按钮点击反馈 |
| `--duration-slow` | 400ms | 卡片展开/页面切换 |
| `--duration-orb` | 4000ms | Orb光晕呼吸动画 |
| `--duration-shimmer` | 2000ms | 骨架屏/加载动效 |

### 7.3 组合过渡Token

```css
--transition-fade: opacity var(--duration-normal) var(--ease-out);
--transition-scale: transform var(--duration-normal) var(--ease-spring);
--transition-glass: all var(--duration-normal) var(--ease-out);
--transition-spring: transform var(--duration-slow) var(--ease-spring);
```

---

## 8. 组件Token

### 8.1 卡片 (Card)

| Token | 标准值 | 说明 |
|-------|--------|------|
| `--card-bg` | var(--bg-glass-2) | 卡片背景 |
| `--card-radius` | var(--radius-md) | 卡片圆角 |
| `--card-padding` | var(--space-8) var(--space-6) | 卡片内边距 |
| `--card-orb` | var(--orb-md) | 卡片光晕 |
| `--card-border` | var(--glass-border-2) | 卡片边框 |
| `--card-glow-edge` | var(--shadow-glass-edge) | 边缘光 |
| `--card-hover-scale` | scale(1.02) | 悬浮放大 |
| `--card-active-scale` | scale(0.98) | 按下缩小 |

### 8.2 按钮 (Button)

| Token | 标准值 | 说明 |
|-------|--------|------|
| `--btn-primary-bg` | var(--gradient-cyan-purple) | 主按钮渐变 |
| `--btn-primary-color` | var(--text-inverse) | 主按钮文字色 |
| `--btn-primary-height` | 88rpx | 主按钮高度 |
| `--btn-primary-radius` | var(--radius-sm) | 主按钮圆角 |
| `--btn-primary-orb` | var(--orb-sm) | 主按钮光晕 |
| `--btn-primary-hover-orb` | var(--orb-hover) | 悬浮增强光晕 |
| `--btn-outline-border` | var(--glass-border-2) | 线框按钮边框 |
| `--btn-outline-color` | var(--text-primary) | 线框按钮文字 |
| `--btn-outline-bg` | var(--bg-glass-1) | 线框按钮背景 |
| `--btn-sm-height` | 64rpx | 小按钮高度 |
| `--btn-sm-radius` | var(--radius-xs) | 小按钮圆角 |

### 8.3 输入框 (Input)

| Token | 标准值 | 说明 |
|-------|--------|------|
| `--input-bg` | var(--bg-glass-1) | 输入框背景 |
| `--input-border` | var(--border-subtle) | 输入框边框 |
| `--input-radius` | var(--radius-sm) | 输入框圆角 |
| `--input-height` | 88rpx | 输入框高度 |
| `--input-padding` | var(--space-6) | 输入框水平内边距 |
| `--input-color` | var(--text-primary) | 输入文字色 |
| `--input-placeholder` | var(--text-tertiary) | 占位符色 |
| `--input-focus-border` | var(--border-accent) | 聚焦边框色 |
| `--input-error-border` | var(--danger) | 错误边框色 |

### 8.4 导航 (Navigation)

| Token | 标准值 | 说明 |
|-------|--------|------|
| `--nav-bg` | var(--bg-glass-2) | 导航栏背景 |
| `--nav-blur` | var(--glass-blur-2) | 导航栏模糊 |
| `--nav-title-color` | var(--text-primary) | 标题色 |
| `--nav-title-size` | var(--text-xl) | 标题字号 |
| `--nav-height` | 88rpx | 导航栏高度 |

### 8.5 TabBar

| Token | 标准值 | 说明 |
|-------|--------|------|
| `--tabbar-bg` | var(--bg-elevated) | TabBar背景 |
| `--tabbar-border` | var(--border-subtle) | TabBar顶部分割线 |
| `--tabbar-color` | var(--text-tertiary) | 未选中色 |
| `--tabbar-color-active` | var(--cyan) | 选中色 |
| `--tabbar-font-size` | var(--text-xs) | 标签字号 |
| `--tabbar-icon-size` | 48rpx | 图标尺寸 |
| `--tabbar-height` | 100rpx | TabBar高度 |
| `--tabbar-safe-bottom` | env(safe-area-inset-bottom) | 安全区域 |

### 8.6 统计数字 (Stat)

| Token | 标准值 | 说明 |
|-------|--------|------|
| `--stat-number-size` | var(--text-2xl) | 数字字号 |
| `--stat-number-weight` | 700 | 字重 |
| `--stat-number-color` | var(--text-primary) | 数字色 |
| `--stat-label-size` | var(--text-xs) | 标签字号 |
| `--stat-label-color` | var(--text-secondary) | 标签色 |
| `--stat-gap` | var(--space-8) | 间距 |

### 8.7 用户头部 (UserHeader)

| Token | 标准值 | 说明 |
|-------|--------|------|
| `--user-header-avatar-size` | 120rpx | 头像大小 |
| `--user-header-avatar-border` | 2px solid rgba(255,255,255,0.15) | 头像边框 |
| `--user-header-avatar-orb` | var(--orb-md) | 头像光晕 |
| `--user-header-name-size` | var(--text-2xl) | 姓名字号 |
| `--user-header-pos-size` | var(--text-sm) | 职位字号 |
| `--user-header-padding` | var(--space-10) var(--space-6) | 头部内边距 |

### 8.8 信任头像堆叠 (AvatarStack)

| Token | 标准值 | 说明 |
|-------|--------|------|
| `--avatar-stack-size` | 72rpx | 头像尺寸 |
| `--avatar-stack-border` | 2px solid var(--bg-page) | 头像重叠边框 |
| `--avatar-stack-overlap` | -16rpx | 重叠偏移 |

---

## 9. 首页专属Token

| Token | 标准值 | 说明 |
|-------|--------|------|
| `--home-orb-bg` | (参见5.2节Orb背景) | 首页Orb背景 |
| `--home-action-bar-bg` | var(--bg-glass-2) | 操作栏背景 |
| `--home-action-bar-margin` | var(--space-6) | 操作栏外边距 |
| `--home-action-bar-radius` | var(--radius-xl) | 操作栏大圆角 |
| `--home-ai-entry-orb` | var(--orb-lg) | AI入口大光晕 |
| `--home-ai-entry-radius` | var(--radius-lg) | AI入口圆角 |
| `--home-recommend-gap` | var(--space-6) | 推荐列表间距 |
| `--home-upgrade-bg` | var(--gradient-purple-pink) | 升级提示渐变 |

---

## 10. 暗色适配说明

AI数智名片**仅支持暗色模式**（AI原生暗色方向），不提供浅色模式切换。所有Token默认即为暗色值，无需dark media query包裹。

---

## 附录：CSS变量一览（完整列表）

```
--bg-*              (4个)  基底色
--gradient-*        (5个)  渐变系统
--cyan / --purple / --pink / --success / --warning / --danger  (9个) 单色
--text-*            (6个)  文字色
--border-*          (4个)  边框色
--font-*            (4个)  字族
--text-size-*       (9个)  字号
--tracking-*        (4个)  字距
--glass-*           (9个)  玻璃参数
--orb-*             (8个)  光晕参数
--space-*           (11个) 间距
--radius-*          (6个)  圆角
--shadow-*          (2个)  保留阴影
--ease-*            (4个)  动效曲线
--duration-*        (5个)  动效时长
--transition-*      (4个)  组合过渡
--card-*            (8个)  卡片组件
--btn-*             (9个)  按钮组件
--input-*           (8个)  输入框组件
--nav-*             (4个)  导航组件
--tabbar-*          (7个)  TabBar组件
--stat-*            (5个)  统计组件
--user-header-*     (5个)  用户头部组件
--avatar-stack-*    (3个)  头像堆叠组件
--home-*            (6个)  首页专属
```
