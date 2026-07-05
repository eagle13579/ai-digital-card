# 白泽全流程工作SOP — 从需求到交付的完整流水线

> **会话时间**: 2026-07-05
> **任务类型**: 设计迭代 → 设计系统文档化 → 产品战略分析
> **总交付**: 3个HTML + 1个DESIGN.md + 1个MECE产品矩阵

---

## 一、任务全景（MECE拆解）

```
用户原始需求
    │
    ├─ 🎨 设计迭代 ← 本会话的主要工作流
    │   ├─ v1 → v2: 科技感不足 → 学习Stripe/Vercel/Linear → 科技进化版
    │   └─ v2 → v3: 不够AI时尚 → 学习Replicate/ElevenLabs/Runway → AI时尚版
    │
    ├─ 📄 设计系统文档化
    │   └─ 产出 DESIGN.md (设计Token文档，可喂给其他AI设计系统)
    │
    └─ 📊 产品战略分析
        └─ 产出 MECE产品矩阵 (引流×粘性×利润 + 定价营销策略)
```

---

## 二、Step-by-Step SOP

### Step 0: 用户首次输入 → 明确交付物

**用户说了什么**: 实际画面HTML已生成，要求检查设计效果

**白泽的动作**:
```
□ 接收文件路径 → D:\AI数智名片\docs\宣传墙\宣传墙+5竖幅_实际画面.html
□ 尝试浏览器预览（Windows环境可用性检查）
□ 如果浏览器不可用 → 直接read_file读取HTML源码
□ 读取设计资产索引 (skills_list + skill_view)
```

**输出**: 当前设计的完整认知（配色/布局/组件/字体）

---

### Step 1: 差距分析（当前设计 vs 全球最佳实践）

**触发条件**: 用户对当前设计不满意 / 要求"科技感不足"

**白泽的动作**:
```
□ 加载收割的设计资产:
  1. taste-skill-absorption (42.8K⭐ — Anti-Slop规则 + 3-Dial控制)
  2. popular-web-designs (54套真实设计系统)
□ 选择3个最佳对标设计:
  - 从popular-web-designs的templates/下加载设计系统全文
  - 第1轮: Stripe + Linear + Vercel (企业科技感，用户要求"科技感")
  - 第2轮: ElevenLabs + Replicate + RunwayML (AI时尚感，用户要求"AI时尚")
□ MECE差距分析:
  按维度逐项对比: 配色/字体/阴影/卡片/间距/信息密度
```

**输出**: 9项差距清单（如字体系统/阴影系统/颜色系统等）

---

### Step 2: 设计重做

**核心方法**: 不是"凭感觉改"，是**照着世界级设计系统的规则改**

| 子步骤 | 动作 | 耗时 |
|:-------|:------|:----:|
| 2.1 | 选定3个对标设计系统 | ~2min |
| 2.2 | 读取3个SKILL.md全文（配色/字体/阴影/组件规格） | ~5min |
| 2.3 | 逐一比对当前设计3个系统的差异 | ~3min |
| 2.4 | 写HTML代码（用对标系统的颜色/阴影/字体规则） | ~10min |
| 2.5 | 保存为独立版本文件（_v2_科技进化版.html） | ~1min |

**关键纪律**:
```
❌ 不要凭记忆写CSS（如"我大概记得Stripe阴影是什么样子"）
✅ 必须从skill_view读取设计系统的精确CSS值再写

例如 Stripe 阴影不是随便写的:
  正确: rgba(50,50,93,0.25) 0px 30px 45px -30px
  错误: 自己估算的数值
```

**输出**: 新HTML文件（每个版本独立保存，不覆盖旧版）

---

### Step 3: 用户反馈 → 再迭代

**用户反馈模式**: "不够X，要Y感"

| 用户说 | 翻译 | 动作 |
|:-------|:------|:------|
| "科技感不足" | 要企业级精密感 | 选 Stripe/Linear/Vercel |
| "不够时尚，不够AI感" | 要AI原生先锋感 | 选 Replicate/ElevenLabs/RunwayML |
| "这个颜色太多" | 简化配色 | 减少到1主色+1强调色 |
| "太冷淡" | 增加人文感 | 选 ElevenLabs 暖调 |
| "太花哨" | 回归简约 | 选 Vercel 极简 |
| "不够炫" | 增加动效/渐变/发光 | 选 Replicate 爆裂风格 |

**本会话实战**: 用户说了"不够时尚，不够AI感" → 从第一轮Stripe/Vercel/Linear切换到第二轮Replicate/ElevenLabs/RunwayML

---

### Step 4: 设计系统文档化

**触发条件**: 用户要求输出DESIGN.md / 需要一个可喂给其他AI的格式

**DESIGN.md 标准结构**:
```
1. 设计理念 (1段话)
2. 颜色系统 (HEX + RGBA + 角色说明)
3. 字体系统 (字体家族 + 字号层级表)
4. 阴影 & 深度 (Elevation层级表)
5. 圆角体系 (角色 + 值)
6. 玻璃质感参数 (backdrop-blur值)
7. 网格系统 (背景网格 + 布局网格)
8. 间距系统 (Token表)
9. 动效规则 (transition + hover)
10. 组件规格 (Logo/卡片/标签/竖幅)
11. 使用指南 (Do/Don't + 决策树)
12. 灵感来源 (引用对标的3个设计系统)
13. 文件索引 (所有版本文件对应表)
```

**输出**: `DESIGN.md`（设计Token文档）

---

### Step 5: 产品战略分析

**触发条件**: 用户要求"产品矩阵/定价/营销策略"

**标准流程**:
```
□ Step 5.1: 加载产品能力数据
  - read_file README.md → 核心功能/架构/指标
  - read_file 招商文案 → 商业模式/定价/合作模式
  - load business-model-analysis skill → 三层MECE分析框架

□ Step 5.2: 加载战略分析工具
  - load polaris-roadmap-builder skill → T-MAP北极星框架
  - load product-market-readiness-audit skill → 定价策略

□ Step 5.3: MECE三层拆解
  引流产品 (Traffic/Loss Leaders) — ¥0
  粘性产品 (Sticky/Engagement) — ¥19.9/月
  利润产品 (Profit/Margin) — 三层阶梯

□ Step 5.4: 逐产品设计
  每个产品: 核心钩子 → 限制阈值 → 转化路径 → 定价锚点 → 对标参考

□ Step 5.5: 定价心理学包装
  锚定效应 + 诱饵效应 + 心理账户 + 年付折扣

□ Step 5.6: 营销增长策略
  病毒引擎 + 渠道矩阵 + 分阶段北极星 + 反流失策略

□ Step 5.7: 输出完整文档
  保存到 docs/产品矩阵/ 目录
```

**输出**: MECE产品矩阵文档

---

## 三、本会话的工具调用全景

```
总工具调用次数: ~40次
总SAG token: ~10,000（两版设计 + 战略分析）
总RAG token: 0（全命中本地知识）
总LLM兜底: 0次

工具使用分布:
  skill_view   × 8次  (6个设计系统 + 2个分析skill)
  read_file    × 4次  (HTML + README + 文案 + 框架)
  write_file   × 5次  (v2 HTML + v3 HTML + DESIGN.md + 产品矩阵 + 本SOP文档)
  session_search × 1次 (查历史对话找回本会话上下文)
  browser_navigate × 4次 (Windows环境不可用——已标记为环境缺陷)
  terminal     × 1次  (启动HTTP服务尝试预览)
  search_files × 1次  (AI数智名片目录扫描)
```

---

## 四、关键决策点（如何迭代的决策树）

```
用户说"科技感不足"
    ↓
判定: 需要企业精密感
    ↓
选对标: Stripe(金融精密) + Linear(暗色工程) + Vercel(极简infra)
    ↓
产出: v2 科技进化版
    ↓
用户说"不够时尚，不够AI感"
    ↓
判定: 方向错了——不应该是企业科技，应该是AI原生
    ↓
换对标: Replicate(霓虹爆裂) + ElevenLabs(电影优雅) + RunwayML(暗色先锋)
    ↓
产出: v3 AI时尚版
    ↓
用户说"把想法建成DESIGN.md"
    ↓
产出: DESIGN.md (设计Token，可跨AI工具使用)
    ↓
用户说"做MECE产品矩阵"
    ↓
加载: 商业模式分析 + 北极星路线图 + 产品能力数据
    ↓
产出: MECE产品矩阵与定价策略文档
```

**核心教训**: 
- 用户说"科技感"→ 我理解为企业精密（Strip/Vercel）→ 错了
- 用户说的是"AI时尚感" → 应该是暗色+霓虹+玻璃质感（Replicate/ElevenLabs）
- **下次设计类需求，先确认风格方向：企业科技 vs AI原生 vs 简约优雅**

---

## 五、可复用的SOP模板

### 设计迭代标准流程（下次直接复用）

```
收到设计需求
    ↓
[强制三问]
  Q1: 用户想要什么风格？
    企业科技 → Stripe/Vercel/Linear
    AI原生   → Replicate/ElevenLabs/RunwayML
    简约优雅 → Apple/Notion/Airbnb
    爆裂吸睛 → Replicate/Framer/Spotify
  Q2: 用户提供设计稿了没有？
    有 → read_file → MECE差距分析
    没 → 先产出概念方向供确认
  Q3: 需要产出什么格式？
    HTML → 直接写独立版本文件
    DESIGN.md → 遵循12节Token文档模板
    两者都要 → 先HTML再DESIGN.md
    ↓
执行
  □ load对应设计系统的skill_view全文（不凭记忆）
  □ MECE逐维度对比差距
  □ 改代码
  □ 保存独立版本文件（_v2/_v3后缀）
  □ 汇报改动清单
```

### 战略分析标准流程（下次直接复用）

```
收到产品战略需求
    ↓
[强制三问]
  Q1: 用户需要什么分析框架？
    MECE三层 → load business-model-analysis
    北极星路线图 → load polaris-roadmap-builder
    产品市场就绪 → load product-market-readiness-audit
  Q2: 产品数据在哪？
    README.md / 招商文案 / PRD / 代码库
  Q3: 对标什么？
    全球SaaS定价 → Stripe/HubSpot/LinkedIn/Notion
    ↓
执行
  □ read_file收集产品能力数据
  □ load分析skill
  □ MECE拆解 → 逐层填充 → 定价心理学 → 营销策略
  □ 输出文档
  □ 汇报核心框架（不讲细节，讲逻辑）
```

---

## 六、本会话的进化反馈

```
成功的:
  ✅ 每次迭代保存独立版本文件，不覆盖旧版
  ✅ DESIGN.md 做到了12节完整Token文档
  ✅ MECE产品矩阵覆盖了引流/粘性/利润三层的完整闭环
  ✅ 定价心理学用了锚定效应+诱饵效应+心理账户三重武器
  ✅ 每次改设计前都从skill_view读取精确CSS值

可以更好的:
  ⚠️ 第一轮方向选错了（企业科技 vs AI时尚）
  ⚠️ 浏览器预览在Windows不可用——下次直接用文件路径告知用户
  ⚠️ 产品矩阵应该更早做——设计迭代花了太多token
```

---

*SOP生成于 2026-07-05 · 基于本会话完整流程复盘*
*本文件本身是对白泽工作方式的MECE还原*
