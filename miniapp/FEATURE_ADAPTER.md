# FEATURE_ADAPTER.md — AI数智名片 Feature 注入适配文档

> **注入日期**: 2026-07-09
> **注入体系**: Hermes Agent Features
> **目标产品**: AI数智名片 (微信小程序) — `D:\AI数智名片\miniapp\`

---

## 目录

1. [注入总览](#1-注入总览)
2. [Feature 1: 认知进化引擎](#2-feature-1-认知进化引擎)
3. [Feature 2: 设计智能引擎](#3-feature-2-设计智能引擎)
4. [Feature 3: 员工能力路由引擎](#4-feature-3-员工能力路由引擎)
5. [Feature 4: 产品技能吸收引擎](#5-feature-4-产品技能吸收引擎)
6. [Feature 6: 变量池自动填充](#6-feature-6-变量池自动填充)
7. [集成点映射表](#7-集成点映射表)
8. [验证与用法](#8-验证与用法)

---

## 1. 注入总览

| # | Feature | 源文件 | 适配器 | 领域 | 产品匹配度 |
|---|---------|--------|--------|------|-----------|
| 1 | 认知进化引擎 | `feature_cognitive_evolution.yaml` | `features/cognitive-evolution-adapter.js` | cognitive | ★★★★★ |
| 2 | 设计智能引擎 | `feature_design_intelligence.yaml` | `features/design-intelligence-adapter.js` | design | ★★★★★ |
| 3 | 员工能力路由引擎 | `feature_employee_routing.yaml` | `features/employee-route-adapter.js` | legion | ★★★★☆ |
| 4 | 产品技能吸收引擎 | `feature_skill_absorption.yaml` | `features/skill-absorption-adapter.js` | learning | ★★★★★ |
| 5 | 三通道账单 | `feature_triple_channel_billing.yaml` | `features/triple-channel-billing-adapter.js` | cognitive | ★★★★★ |
| 6 | 变量池自动填充 | `feature_variable_pool_autofill.yaml` | `features/variable-pool-autofill-adapter.js` | cognitive | ★★★★★ |
| 7 | 七步法员工执行引擎 | `feature_seven_step_engine.yaml` | `features/seven-step-engine-adapter.js` | legion | ★★★★★ |

所有适配器文件位于: `miniapp/features/`

---

## 2. Feature 1: 认知进化引擎

### 2.1 源Feature概要

| 属性 | 值 |
|------|-----|
| 名称 | 认知进化引擎 |
| 版本 | 1.0.0 |
| 领域 | cognitive |
| 核心 | 6步拆解法 + 五池循环(现象池/变量池/模型池/决策验证池/行动池) |
| 原产品 | 白泽控制台、赛博参谋、AI数智军团 |

### 2.2 注入适配器

**文件**: `features/cognitive-evolution-adapter.js`

**核心能力封装**:

```
cognitiveAdapter.extractFromChat(message, response)     ← AI对话萃取
cognitiveAdapter.extractFromScan(scanResult)             ← 名片扫描萃取
cognitiveAdapter.extractFromMatch(matchResult)           ← 人脉匹配萃取
cognitiveAdapter.manualExtract(input, source)            ← 手动触发萃取
cognitiveAdapter.getPoolsStatus()                        ← 查询五池状态
cognitiveAdapter.getPoolCounts()                         ← 查询五池数量
```

**五池数据结构**:
```
phenomena[]  ← 现象池: 原始输入/观察/数据点
variables[]  ← 变量池: 关键变量/维度提取
models[]     ← 模型池: 心智模型/模式/理论
decisions[]  ← 决策验证池: 已验证/待验证的决策假设
actions[]    ← 行动池: 可执行的行动/建议
```

### 2.3 集成点

| 产品模块 | 集成方式 | 集成文件 |
|----------|---------|---------|
| AI对话 (pages/ai/chat/) | 对话后自动萃取认知资产 → 注入五池 | `pages/ai/chat/index.js` |
| AI内容生成 (pages/ai/generate/) | 生成内容后分析变量+模型 | `pages/ai/generate/index.js` |
| 名片扫描 (pages/ai/scan/) | OCR结果录入现象池+变量池 | `pages/ai/scan/index.js` |
| 人脉匹配 (pages/ai/match/) | 匹配结果 → 行动池 | `pages/ai/match/index.js` |
| AI数据洞察 (pages/ai/insight/) | 模型池+决策验证池输出 | `pages/ai/insight/index.js` |
| MockService | 在mock数据层注入认知获取 | `utils/mockService.js` |

### 2.4 API端点映射

| Feature端点 | 适配器方法 | 产品集成 |
|-------------|-----------|---------|
| GET /api/v1/cognitive/pools/status | `getPoolsStatus()` | AI洞察页展示 |
| POST /api/v1/cognitive/extract | `manualExtract()` | AI对话页手动触发 |

---

## 3. Feature 2: 设计智能引擎

### 3.1 源Feature概要

| 属性 | 值 |
|------|-----|
| 名称 | 设计智能引擎 |
| 版本 | 1.0.0 |
| 领域 | design |
| 核心 | SAG驱动·54套真实设计系统·3-Dial细调·Anti-Slop Gate |
| 原产品 | 白泽控制台、**AI数字名片**、中韩出海数智港、链客宝 |

> ⚡ AI数字名片 是该Feature的**原生目标产品**之一！

### 3.2 注入适配器

**文件**: `features/design-intelligence-adapter.js`

**核心能力封装**:

```
designAdapter.analyzeDesign(requirements)         ← 5维分析 → 最优设计匹配
designAdapter.applyDesignSystem(systemKey, overrides)  ← 应用设计系统Token
designAdapter.fineTune(tokens, dials)              ← 3-Dial微调(对比度/温暖度/正式度)
designAdapter.submitFeedback(systemKey, rating)    ← 反馈循环进化
designAdapter.syncDesignSystems(external)           ← 从design_system/同步品牌库
```

**内置设计系统索引 (10/54)**:

| 系统 | 风格 | 最佳用例 |
|------|------|---------|
| Linear | 极简科技 | SaaS/科技产品 |
| Stripe | 高端商业 | 金融/B2B |
| Notion | 内容优先 | 文档/协作 |
| Apple | 极简奢华 | 高端品牌 |
| Vercel | 现代极客 | 开发者平台 |
| Tailwind | 实用主义 | UI组件 |
| Shopify | 电商商务 | 电商/零售 |
| Mailchimp | 活泼创意 | 营销/SaaS |
| 小红书 | 年轻社区 | 社交/内容 |
| 字节跳动 | 数据驱动 | 互联网/AI |

### 3.3 集成点

| 产品模块 | 集成方式 | 集成文件 |
|----------|---------|---------|
| 名片创建 (pages/brochure/create/) | 创建时自动分析设计需求→匹配设计系统 | `pages/brochure/create/index.js` |
| 画册预览 (pages/brochure/preview/) | 应用设计Token到预览样式 | `pages/brochure/preview/index.js` |
| design_system/ 目录 | 通过 `syncDesignSystems()` 同步54品牌库 | `design_system/` |
| config/design-tokens.js | 同步设计Token到全局配置 | `config/design-tokens.js` |
| AI内容生成 | 设计风格建议作为生成模板 | `pages/ai/generate/index.js` |

### 3.4 5维分析引擎

```
analyzeDesign({ productType, industry, style, brandTone, targetUser })
  → 5维度评分:
    1. 行业匹配 (15pts)
    2. 风格匹配 (20pts)
    3. 品牌知名度 (30%加权)
    4. 产品类型适配 (10pts)
    5. 目标用户匹配 (10pts)
  → 排序 + Anti-Slop Gate 质量门禁
```

### 3.5 API端点映射

| Feature端点 | 适配器方法 | 产品集成 |
|-------------|-----------|---------|
| POST /api/v1/design/analyze | `analyzeDesign()` | 名片创建页自动调用 |
| POST /api/v1/design/evolve | `submitFeedback()` | 设计设置页用户反馈 |

---

## 4. Feature 3: 员工能力路由引擎

### 4.1 源Feature概要

| 属性 | 值 |
|------|-----|
| 名称 | 员工能力路由引擎 |
| 版本 | 1.0.0 |
| 领域 | legion |
| 核心 | L1能力域/L2负载均衡/L3灵魂匹配 + 反馈进化 |
| 原产品 | 白泽控制台、AI数智军团 |

该Feature对应**七步法执行引擎**的执行前路由 → 员工被路由后自动走7步。

### 4.2 注入适配器

**文件**: `features/employee-route-adapter.js`

**核心能力封装**:

```
router.routeTask(taskType, context)               ← 三层路由 → 最佳员工
router.submitFeedback(employeeId, rating)          ← 反馈 → 权重进化
router.executeSevenStep(routeResult, taskInput)    ← 七步法执行引擎
router.getEmployeeStatus()                         ← 员工状态概览
router.getDomainOverview()                          ← 能力域统计
router.getRouteStats()                             ← 路由统计
```

**AI数智名片版数字员工索引 (12名)**:

| 员工ID | 名称 | 域 | 核心能力 |
|--------|------|-----|---------|
| chat_assistant | 小言 | conversation | AI对话/客服/RAG |
| deepseek_agent | 深寻 | conversation | 深度推理/复杂分析 |
| write_assistant | 文心 | content | 文案写作/内容生成 |
| summary_agent | 萃思 | content | 摘要/提炼 |
| rewrite_expert | 润笔 | content | 润色/风格适配 |
| ocr_engine | 明视 | vision | 名片OCR/文字提取 |
| image_analyzer | 观澜 | vision | 图像分析/场景识别 |
| match_engine | 缘起 | matching | 人脉匹配/智能推荐 |
| insight_agent | 明见 | matching | 数据分析/趋势洞察 |
| design_advisor | 绘境 | design | 设计建议/风格匹配 |
| seven_step_engine | 循道 | orchestration | 七步法全链路 |

### 4.3 三层路由算法

```
routeTask(taskType, context)
  ↓
L1: 能力域匹配           → conversation / content / vision / matching / design
L2: 负载均衡 + 精确匹配    → score - load*0.3 + mode匹配(15pts) + industry(10pts) + priority(3pts/级)
L3: 灵魂匹配              → 提示词关键词微调 (耐心→小言, 创意→文心, 数据→明见等)
  ↓
返回 top_k 候选 + 选中员工
  ↓
选中员工.load += 5 (负载更新)
```

### 4.4 七步法执行引擎

```javascript
router.executeSevenStep(routeResult, taskInput)
  → 7步: 意图感知 → 知识检索 → 能力确认 → 技能调用 → 执行交付 → 经验沉淀 → 知识反哺
  → 返回每步状态 + 汇总报告
```

### 4.5 集成点

| 产品模块 | 集成方式 | 集成文件 |
|----------|---------|---------|
| AI对话入口 | 用户输入→路由→选择AI模式(RAG/DeepSeek) | `pages/ai/chat/index.js` |
| AI内容生成 | 生成任务→路由→对应写手 | `pages/ai/generate/index.js` |
| 名片扫描 | 扫描任务→路由→OCR引擎 | `pages/ai/scan/index.js` |
| 智能匹配 | 匹配任务→路由→匹配引擎 | `pages/ai/match/index.js` |
| MockService | 路由决定mock/真实API | `utils/mockService.js` |
| AI能力中心页 | 展示员工状态 | `pages/ai/index.js` |

### 4.6 API端点映射

| Feature端点 | 适配器方法 | 产品集成 |
|-------------|-----------|---------|
| POST /api/v1/legion/route | `routeTask()` | 各AI功能调用前路由 |
| POST /api/v1/legion/route/feedback | `submitFeedback()` | 用户评价反馈 |

---

## 5. Feature 4: 产品技能吸收引擎

### 5.1 源Feature概要

| 属性 | 值 |
|------|-----|
| 名称 | 产品技能吸收引擎 |
| 版本 | 1.0.0 |
| 领域 | learning |
| 核心 | 六步飞轮(筛选→浸泡→萃取→技能化→记忆沉淀→代码收割) + 五卡输出(心智模型/变量/决策/动作/代码) |
| 原产品 | 白泽控制台、AI数智军团 |
| 依赖 | 认知进化引擎 (五池归档)、员工记忆系统 (铁律二) |

已验证收入 **300+ 心智模型**，适合从外部GitHub项目/文档/方法论中持续吸收技能知识。

### 5.2 注入适配器

**文件**: `features/skill-absorption-adapter.js`

**核心能力封装** (`SkillAbsorptionAdapter` 类):

```javascript
const SkillAbsorptionAdapter = require('../../features/skill-absorption-adapter')
const absorber = new SkillAbsorptionAdapter(options)

// 分析来源 → 筛选+浸泡
const analysis = absorber.analyze({ type: 'docs', title: '...', content: '...' })
// 执行完整吸收 → 萃取+技能化+记忆沉淀+代码收割
const result = absorber.absorb(analysis, { industry: '科技', domain: 'AI' })
// 验证吸收结果
const report = absorber.validate(result)

// 便捷方法（使用默认实例，无需new）
const { quickAbsorb, analyze, absorb, validate } = require('...')
```

**六步飞轮流水线**:

```
analyze(source)
  ├── 步骤①: 筛选 (Scan)     → 评分来源质量，判断是否值得吸收
  └── 步骤②: 浸泡 (Soak)     → 解析来源结构(标题/章节/代码块)
absorb(analysis, context)
  ├── 步骤③: 萃取 (Extract)   → 提取心智模型 + 关键变量
  ├── 步骤④: 技能化 (Skillify)→ 转化为决策策略 + 可执行动作
  ├── 步骤⑤: 记忆沉淀 (Memorize) → 写入五卡仓库
  └── 步骤⑥: 代码收割 (Harvest)  → 提取代码片段(代码块/内联代码)
```

**五卡输出结构**:

```
mental_models[]  ← 心智模型: 模式/规律/理论抽象
variables[]      ← 变量: 关键维度/参数
decisions[]      ← 决策: 已验证/可复用的策略
actions[]        ← 动作: 可执行的操作步骤
code_snippets[]  ← 代码: 收割的可复用代码片段
```

### 5.3 集成点

| 产品模块 | 集成方式 | 集成文件 |
|----------|---------|---------|
| AI对话 (pages/ai/chat/) | 对话后自动分析→吸收技能知识点 | `pages/ai/chat/index.js` |
| 名片扫描 (pages/ai/scan/) | OCR结果→行业知识自动吸收 | `pages/ai/scan/index.js` |
| 人脉匹配 (pages/ai/match/) | 匹配结果→社交智慧吸收 | `pages/ai/match/index.js` |
| AI内容生成 (pages/ai/generate/) | 生成内容→收割代码/模型 | `pages/ai/generate/index.js` |
| 数据洞察 (pages/ai/insight/) | 洞察结果→记忆沉淀→五卡归档 | `pages/ai/insight/index.js` |
| MockService | 在mock层注入吸收管线 | `utils/mockService.js` |

### 5.4 六步飞轮评分算法

```
_scoreSource(source):
  base = 50
  + type bonus (github:20, docs:15, rss:10, manual:25, chat:8, scan:5)
  + content length bonus (>=50: +10, >=500: +5)
  + url bonus (+5)
  + meta bonus (stars/100: +10 cap, language: +3, topics: +5)
  → 0-100 score (threshold ≥30 方可吸收)
```

### 5.5 验证评分算法

```
validate(absorbResult):
  - 检查 absorbId 存在 (权重20%)
  - 检查 步骤完整性 >=4步 (权重20%)
  - 检查 卡片输出 > 0 (权重20%)
  - 检查 时间戳存在 (权重10%)
  - 检查 来源引用完整 (权重5%)
  - 错误扣减 (每个-10分)
  - 警告扣减 (每个-5分)
  → 0-100 score (>=60 为通过)
```

### 5.6 API端点映射

| Feature端点 | 适配器方法 | 产品集成 |
|-------------|-----------|---------|
| POST /api/v1/learning/absorb | `absorber.absorb(analysis, context)` | AI对话/扫描页提交吸收 |
| GET /api/v1/learning/status | `absorber.getPipelineStatus()` | AI洞察页展示吸收状态 |

---

## 6. Feature 5: 三通道账单

### 6.1 源Feature概要

| 属性 | 值 |
|------|-----|
| 名称 | 三通道账单 |
| 版本 | 1.0.0 |
| 领域 | cognitive |
| 核心 | 三通道(A高精度RAG/B快速SAG/C批量LLM回退) + 账单追踪 + 费用告警 |
| 原产品 | 白泽控制台 |
| 依赖 | knowledge-query-dual-channel, token-extreme-efficiency |

> ⚡ 该Feature深度依赖**双通道知识查询**与**极致Token效率**机制，提供精细化Token消耗追踪与控制。

### 6.2 注入适配器

**文件**: `features/triple-channel-billing-adapter.js`

**核心能力封装**:

```javascript
const billing = require('../../features/triple-channel-billing-adapter')

// 记录RAG查询命中/未命中（通道A）
billing.countRagHits('channel_a', 3, { query: '...', tokens: 450, latency: 120 })

// 追踪SAG Token消耗（通道B）
billing.trackSagTokens(320, { model: 'deepseek-sag', prompt: '...', generated: 280 })

// 追踪LLM回退事件（通道C）
billing.trackLlmFallback('rag_timeout', { query: '...', tokens: 1200, source: 'channel_a' })

// 获取当前账单
const bill = billing.getBill()
console.log(bill.summary)
```

**三通道设计**:

| 通道 | 名称 | 用途 | 费率(分/千Token) | 每日预算 |
|------|------|------|-----------------|---------|
| channel_a | 高精度RAG通道 | 知识检索+重排序（精准查询） | 0.15 | 1,000,000 |
| channel_b | 快速SAG通道 | 自注意力生成（优化Token消耗） | 0.08 | 5,000,000 |
| channel_c | 批量LLM回退通道 | 完整LLM调用（SAG/RAG回退兜底） | 0.25 | 10,000,000 |

### 6.3 账单数据结构

```javascript
getBill() → {
  summary: {
    total_tokens,          // 三通道总Token消耗
    total_cost,            // 总成本(分)
    total_budget,          // 总预算(Token)
    usage_percent,         // 使用百分比
    cycle,                 // 账单周期
    alerts_triggered,      // 是否有告警
  },
  channels: {
    channel_a: { token_usage, cost, budget, usage_percent, hits, misses, hit_rate },
    channel_b: { token_usage, cost, budget, usage_percent, sessions, avg_tokens_per_session },
    channel_c: { token_usage, cost, budget, usage_percent, fallbacks },
  },
  fallback_stats: { total_fallbacks, channel_c_fallbacks },
  alerts: [ { channel, channel_name, percent, message, timestamp } ],
}
```

### 6.4 集成点

| 产品模块 | 集成方式 | 集成文件 |
|----------|---------|---------|
| AI对话 (pages/ai/chat/) | 每次RAG查询后调用 `countRagHits()` 记录命中+Token | `pages/ai/chat/index.js` |
| AI内容生成 (pages/ai/generate/) | SAG生成完成后调用 `trackSagTokens()` 追踪消耗 | `pages/ai/generate/index.js` |
| 名片扫描 (pages/ai/scan/) | OCR产生LLM回退时调用 `trackLlmFallback()` | `pages/ai/scan/index.js` |
| 智能匹配 (pages/ai/match/) | 匹配引擎回退到完整LLM时记录回退事件 | `pages/ai/match/index.js` |
| AI数据洞察 (pages/ai/insight/) | 展示 `getBill()` 汇总数据和告警信息 | `pages/ai/insight/index.js` |
| MockService | 模拟RAG/SAG/回退场景验证账单逻辑 | `utils/mockService.js` |
| config/config.js | Feature开关与预算配置 | `config/config.js` |

### 6.5 API端点映射

| Feature端点 | 适配器方法 | 产品集成 |
|-------------|-----------|---------|
| GET /api/v1/billing/summary | `getBill()`  | AI洞察页展示账单汇总 |
| GET /api/v1/billing/channels | `getBill({ detail: true })` 各通道明细 | AI洞察页展开详情 |
| PUT /api/v1/billing/alert/config | `updateConfig({ alert_threshold })` | 设置页调整阈值 |

### 6.6 配置参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| channel_a_budget | number | 1000000 | 通道A每日Token预算 |
| channel_b_budget | number | 5000000 | 通道B每日Token预算 |
| channel_c_budget | number | 10000000 | 通道C每日Token预算 |
| alert_threshold | number | 0.85 | 费用告警阈值(占预算百分比) |
| billing_cycle | string | "daily" | 账单周期(daily/weekly/monthly) |

---

## 6. Feature 6: 变量池自动填充

### 6.1 源Feature概要

| 属性 | 值 |
|------|-----|
| 名称 | 变量池自动填充 |
| 版本 | 1.0.0 |
| 领域 | cognitive |
| 核心 | 监控变量池水位并自动从认知进化引擎和五池均衡管理器填充缺失变量 |
| 原产品 | 白泽控制台、AI数智军团、盖娅进化大脑 |
| 依赖 | 认知进化引擎 (提供变量推导)、五池均衡管理器 (提供水位监测) |

### 6.2 注入适配器

**文件**: `features/variable-pool-autofill-adapter.js`

**核心能力封装** (适配器协议: scan / match / fill / report):

```javascript
const vpAutofill = require('../../features/variable-pool-autofill-adapter')

// 扫描变量池水位
vpAutofill.scan()       → pools[] + overallHealth + needsFill

// 匹配缺失变量与可用来源
vpAutofill.match()      → matched[] + sourceBreakdown + canProceed

// 执行自动填充
vpAutofill.fill()       → filled[] + poolStatusAfter + cycleInfo

// 获取填充报告
vpAutofill.report()     → fillSummary + sourceStats + history

// 一键式检查+填充
vpAutofill.autoFillIfNeeded()  → { action: 'filled'|'skipped', ... }
```

**适配器协议说明**:

| 方法 | 输入 | 输出 | 说明 |
|------|------|------|------|
| `scan()` | (无) | `{ pools, overallHealth, needsFill, threshold }` | 扫描所有受监控变量池，计算水位百分比与健康状态 |
| `match()` | `scanResult?` | `{ matched[], sourceBreakdown, canProceed }` | 匹配缺失变量 → 认知进化引擎 + 五池均衡管理器 |
| `fill()` | `matchResult?` | `{ success, filled[], fillCount, poolStatusAfter }` | 按置信度排序，填充至多 `max_fill_per_cycle` 个变量 |
| `report()` | `{ historyLimit?, includeVariables? }` | `{ fillSummary, sourceStats, history }` | 生成包含趋势、成功率、分类的综合报告 |

### 6.3 变量池水位健康模型

```
水位 = 当前变量数 / 池容量

健康状态:
  healthy  (水位 > 阈值 × 2)        → 无需填充
  warning  (阈值 < 水位 ≤ 阈值 × 2)  → 建议填充
  critical (水位 ≤ 阈值)             → 必须填充
```

默认阈值: `fill_threshold = 0.3` (30%)，即变量池满30%以下触发关键水位。

### 6.4 填充来源

| 来源 | 来源适配器 | 贡献变量示例 | 置信度范围 |
|------|-----------|-------------|-----------|
| 认知进化引擎 | cognitive-evolution-adapter.js | 用户意图、情感倾向、行业标签、决策类型、问题复杂度、知识领域、紧急程度、关联人脉 | 0.60-0.90 |
| 五池均衡管理器 | (跨池转移) | 关键实体、核心指标、验证假设、执行瓶颈、时间窗口、资源需求、风险等级、趋势方向 | 0.68-0.88 |

### 6.5 集成点

| 产品模块 | 集成方式 | 集成文件 |
|----------|---------|---------|
| AI对话 (pages/ai/chat/) | 对话生成后调用 `autoFillIfNeeded()` 检查变量池水位 | `pages/ai/chat/index.js` |
| 名片扫描 (pages/ai/scan/) | OCR变量提取后检查池状态，如需调用 `fill()` | `pages/ai/scan/index.js` |
| 智能匹配 (pages/ai/match/) | 匹配完成后调用 `match()` 补充缺失决策变量 | `pages/ai/match/index.js` |
| AI数据洞察 (pages/ai/insight/) | 洞察分析前调用 `scan()` 确保变量池充足，不足则触发 `fill()` | `pages/ai/insight/index.js` |
| AI内容生成 (pages/ai/generate/) | 生成前调用 `scan()` 检查可用变量数 | `pages/ai/generate/index.js` |
| MockService | 模拟变量池水位变化，验证填充逻辑 | `utils/mockService.js` |
| config/config.js | Feature开关与阈值配置 | `config/config.js` |

### 6.6 配置参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `fill_threshold` | number | 0.3 | 触发自动填充的水位阈值 (0.0-1.0) |
| `max_fill_per_cycle` | integer | 10 | 每轮最多填充变量数 |
| `pool_names` | string[] | ['variables'] | 受监控的变量池名称列表 |
| `auto_fill_enabled` | boolean | true | 是否启用自动填充 |
| `min_variables_for_healthy` | number | 5 | 健康水位最少变量数 |

### 6.7 API端点映射

| Feature端点 | 适配器方法 | 产品集成 |
|-------------|-----------|---------|
| GET /api/v1/variable-pool/status | `scan()` + `report()` | AI洞察页展示变量池水位与填充状态 |
| POST /api/v1/variable-pool/fill | `manualFill()` | AI对话页/设置页手动触发一次填充 |

### 6.8 数据流集成

```javascript
// 变量池自动填充在认知循环中的位置

用户交互 → [认知进化引擎] → 五池萃取
  ↓
变量池水位下降 (消耗 > 补充)
  ↓
[变量池自动填充] → scan() → 水位 < 阈值?
  ↓                          ↓
 否 → 跳过                 是 → match() → 认知引擎/五池均衡
                                   ↓
                              fill() → 按置信度排序 → 注入变量池
                                   ↓
                              report() → 记录历史 + 更新水位
```

---

## 7. Feature 7: 七步法员工执行引擎

### 7.1 源Feature概要

| 属性 | 值 |
|------|-----|
| 名称 | 七步法员工执行引擎 |
| 版本 | 1.0.0 |
| 领域 | legion |
| 核心 | 7步：意图感知→知识检索→能力确认→技能调用→执行交付→经验沉淀→知识反哺 |
| 原产品 | AI数智军团、白泽控制台 |
| 已注入 | 220名数字员工，AI数字名片版适配12名 |
| 状态 | 默认运行态，不需手动触发（员工被路由后自动执行） |

> ⚡ 该Feature是**员工能力路由引擎**的后继执行器 — 路由选中员工后自动触发七步法完成指令。

### 7.2 注入适配器

**文件**: `features/seven-step-engine-adapter.js`

**核心能力封装 (七步法适配器协议)**:

```
sevenStep.intent(prompt, options)          ← 步骤① 意图感知 — 解析用户意图/任务类型/情感倾向
sevenStep.retrieve(intent, context)        ← 步骤② 知识检索 — 按域检索相关知识库
sevenStep.confirm(intent, retrieve, emp)   ← 步骤③ 能力确认 — 确认员工能力域/标签是否匹配
sevenStep.execute(confirm, taskInput)      ← 步骤④+⑤ 技能调用 + 执行交付 — 执行并生成交付物
sevenStep.validate(execResult, criteria)   ← 步骤⑤验证 执行交付验证 — 多维质量检查 + Anti-Slop
sevenStep.debrief(execResult, validation)  ← 步骤⑥ 经验沉淀 — 提取教训/可复用模式
sevenStep.feedback(debrief, {rating})      ← 步骤⑦ 知识反哺 — 更新权重/知识库索引
sevenStep.run(prompt, employee, context)   ← ⚡ 一站式执行全部7步
```

**七步法详细说明**:

| 步骤 | 方法 | 输入 | 输出 | Anti-Slop防护 |
|------|------|------|------|--------------|
| ① 意图感知 | `intent()` | 用户文本 + mode | taskType/domain/sentiment/confidence | 关键词阈值 + 置信度计算 |
| ② 知识检索 | `retrieve()` | intent结果 + context | 按域知识源 + 相关文档列表 | 多源交叉验证 |
| ③ 能力确认 | `confirm()` | intent + retrieve + employee | 域匹配/能力匹配率/qualified判定 | 双重判定(域+能力标签) |
| ④ 技能调用 | `execute()` | confirm + taskInput | 员工执行 + 交付物 | 质量评分 (0-100) |
| ⑤ 执行验证 | `validate()` | execute结果 + criteria | 多维检查(5项) + 验证分数 (≥70通过) | 内容完整性/质量/格式/追溯 |
| ⑥ 经验沉淀 | `debrief()` | execute + validate(可选) | lessons/patterns/日志 | 成功/失败/洞察分类 |
| ⑦ 知识反哺 | `feedback()` | debrief + {rating} | 权重调整 + 知识库更新 | 评分映射 (≥4正向, ≤2负向) |

### 7.3 一站式执行引擎 `run()`

```javascript
sevenStep.run(prompt, employee, context)
  → 自动执行全部7步
  → 返回完整执行报告: { success, executionId, steps{1..7}, validation, summary }
```

**执行报告结构**:

```json
{
  "success": true,
  "executionId": "seven_step_1710000000_a1b2c3",
  "employee": { "id": "write_assistant", "name": "文心" },
  "prompt": "写一份产品介绍",
  "steps": {
    "1": { "name": "意图感知", "status": "completed", "detail": "识别为「内容生成」任务 (置信度: 85%)" },
    "2": { "name": "知识检索", "status": "completed", "detail": "从 3 个知识源检索到 4 个相关主题" },
    "3": { "name": "能力确认", "status": "completed", "detail": "「文心」能力确认通过 (域匹配: true, 能力匹配率: 100%)" },
    "4": { "name": "技能调用", "status": "completed", "detail": "completed" },
    "5": { "name": "执行交付", "status": "completed", "detail": "「文心」完成「content」交付，质量评分: 88" },
    "6": { "name": "经验沉淀", "status": "completed", "detail": "经验已沉淀 — 3 条教训, 1 个可复用模式" },
    "7": { "name": "知识反哺", "status": "completed", "detail": "知识反哺完成 — 员工权重已调整" }
  },
  "validation": { "validated": true, "validationScore": 90, ... },
  "totalTime": 1234,
  "summary": "「文心」七步法执行完毕 — ✅ 通过 (1234ms)"
}
```

### 7.4 与员工能力路由引擎的关系

```mermaid
用户指令 → [员工路由引擎] routeTask() → 选中最佳员工
                                           ↓
                                   [七步法引擎] run(prompt, employee)
                                           ↓
                                   步骤① 意图感知 ── intent()
                                   步骤② 知识检索 ── retrieve()
                                   步骤③ 能力确认 ── confirm()
                                   步骤④ 技能调用 ── execute()    ─┐
                                   步骤⑤ 执行交付 ── execute()    ←┘
                                   步骤⑤验证      ── validate()
                                   步骤⑥ 经验沉淀 ── debrief()
                                   步骤⑦ 知识反哺 ── feedback() → 路由权重更新
                                           ↓
                                   执行完成，返回报告
```

- `employee-route-adapter.js` 内置的 `executeSevenStep()` 方法可直接调用本引擎
- 本引擎的 `confirm()` 和 `feedback()` 内部依赖路由适配器的员工索引和反馈机制
- 两者联合形成完整的「路由→执行→反哺」闭环

### 7.5 集成点

| 产品模块 | 集成方式 | 集成文件 |
|----------|---------|---------|
| AI对话 (pages/ai/chat/) | 路由选中员工后调用 `run()` 自动执行七步法 | `pages/ai/chat/index.js` |
| AI内容生成 (pages/ai/generate/) | 生成任务路由后 `run()` 走内容域七步法 | `pages/ai/generate/index.js` |
| 名片扫描 (pages/ai/scan/) | OCR路由后 `run()` 走视觉域七步法 | `pages/ai/scan/index.js` |
| 智能匹配 (pages/ai/match/) | 匹配路由后 `run()` 走匹配域七步法 | `pages/ai/match/index.js` |
| 数据洞察 (pages/ai/insight/) | 洞察前 `run()` 确保七步法完整性 | `pages/ai/insight/index.js` |
| 员工路由引擎 | `employee-route-adapter.js` 通过 `executeSevenStep()` 调用 | `features/employee-route-adapter.js` |
| MockService | 在mock数据层注入七步法模拟执行 | `utils/mockService.js` |

### 7.6 配置参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `auto_activate` | boolean | true | 是否自动激活七步法 |
| `log_level` | string | "result_only" | 输出详细程度 (silent/result_only/full) |
| `max_steps` | integer | 7 | 最大步骤数 |

### 7.7 Anti-Slop防护

本引擎内置 **Anti-Slop Gate** 机制，防止空壳/幻觉输出：

1. **意图置信度阈值**: `intent().confidence` 过低则提前止损
2. **能力匹配双重判定**: 域匹配 + 能力标签匹配率，任一不通过则拒绝执行
3. **执行验证5维检查**: 内容完整性(30%) + 质量达标(30%) + 格式合规(20%) + 员工追溯(10%) + 执行ID(10%)
4. **质量门禁**: `validate().validated` ≥ 70分方可通过
5. **Anti-Slop标记**: 检测内容过短(`<10字符`)、格式异常、质量不达标等情况并标记警告

### 7.8 API端点映射

| Feature端点 | 适配器方法 | 产品集成 |
|-------------|-----------|---------|
| GET /api/v1/legion/seven-step/status | `getEngineStatus()` | AI洞察页/AI能力中心展示引擎状态 |
| POST /api/v1/legion/seven-step/execute | `run()` | AI对话/生成/扫描/匹配页手动触发 |

---

## 8. 集成点映射表

### 8.1 按产品模块

| 产品模块/文件 | 注入Feature | 注入方式 |
|--------------|-------------|---------|
| `pages/ai/chat/index.js` | 认知进化 + 路由引擎 + 技能吸收 + **三通道账单** + **变量池自动填充** + **七步法引擎** | wrap对话流，萃取认知资产 + 路由AI模式 + 吸收技能知识点 + 追踪RAG命中+Token消耗 + 对话后检查变量池水位 + 路由后自动执行七步法 |
| `pages/ai/generate/index.js` | 认知进化 + 路由引擎 + 技能吸收 + **三通道账单** + **变量池自动填充** + **七步法引擎** | wrap生成调用，分析变量/模型 + 路由写手 + 收割代码/模型 + 追踪SAG Token + 生成前检查可用变量数 + 生成后路由→七步法执行 |
| `pages/ai/scan/index.js` | 认知进化 + 路由引擎 + 技能吸收 + **三通道账单** + **变量池自动填充** + **七步法引擎** | OCR结果→现象池 + 路由OCR引擎 + 行业知识吸收 + 记录LLM回退 + OCR变量提取后检查池状态 + OCR后路由→七步法执行 |
| `pages/ai/match/index.js` | 认知进化 + 路由引擎 + 技能吸收 + **三通道账单** + **变量池自动填充** + **七步法引擎** | 匹配结果→行动池 + 路由匹配引擎 + 社交智慧吸收 + 记录回退事件 + 匹配后补充缺失决策变量 + 匹配后路由→七步法执行 |
| `pages/ai/insight/index.js` | 认知进化 + 技能吸收 + **三通道账单** + **变量池自动填充** + **七步法引擎** | 模型池+决策池→洞察输出 + 五卡归档 + 展示账单汇总+告警 + 洞察前确保变量池充足 + 洞察前触发七步法确保知识完整 |
| `pages/ai/index.js` | 路由引擎 + **三通道账单** + **变量池自动填充** + **七步法引擎** | AI能力中心→展示路由统计 + 账单概览 + 变量池水位状态 + 七步法引擎状态与执行统计 |
| `pages/brochure/create/index.js` | 设计智能引擎 | 创建时自动匹配设计系统 |
| `pages/brochure/preview/index.js` | 设计智能引擎 | 预览时应用设计Token |
| `utils/mockService.js` | 路由引擎 + 技能吸收 + **三通道账单** + **变量池自动填充** + **七步法引擎** | 路由决定mock/真实API + 注入吸收管线 + 模拟RAG/SAG/回退场景 + 模拟变量池水位变化触发填充 + 模拟七步法执行 |
| `utils/api.js` | 全部7个 | 扩展新API端点入口 |
| `config/design-tokens.js` | 设计智能引擎 | 同步设计Token |
| `config/config.js` | 全部7个 | Feature开关配置 |
| `design_system/` | 设计智能引擎 | 54品牌库同步源 |

### 8.2 数据流

```
用户输入/操作
  ↓
[员工路由引擎] → 路由到最佳处理员工
  ↓
[七步法引擎] → 自动执行7步 (意图→检索→确认→执行→交付→沉淀→反哺)
  ↓
[具体AI处理] (对话/生成/扫描/匹配)
  ↓
[变量池自动填充] → scan() 水位检查 → 必要时 match()+fill()
  ↓
[三通道账单] → 记录RAG命中/SAG Token/LLM回退
  ↓
[认知进化引擎] → 自动萃取认知资产 → 五池
  ↓
[技能吸收引擎] → 从对话/扫描/生成/匹配中吸收 → 五卡
  ↓
[设计智能引擎] → 设计匹配/风格建议 (涉及设计时)
  ↓
[员工路由引擎] → 反馈提交 → 权重进化
```

---

## 8. 验证与用法

### 8.1 验证适配器可被引用

```javascript
// 在任意页面引用测试
const cognitiveAdapter = require('../../features/cognitive-evolution-adapter')
const designAdapter = require('../../features/design-intelligence-adapter')
const router = require('../../features/employee-route-adapter')
const SkillAbsorptionAdapter = require('../../features/skill-absorption-adapter')
const billing = require('../../features/triple-channel-billing-adapter')
const vpAutofill = require('../../features/variable-pool-autofill-adapter')

// 1. 认知进化引擎
const counts = cognitiveAdapter.extractFromChat('我需要一款产品介绍', '写了一篇专业的产品介绍。建议: 突出三个核心卖点')
console.log('五池状态:', cognitiveAdapter.getPoolsStatus())

// 2. 设计智能引擎
const scheme = designAdapter.analyzeDesign({
  productType: '名片',
  industry: '科技',
  brandTone: '专业',
})
console.log('推荐设计:', scheme.primary.name)

// 3. 员工路由引擎
const route = router.routeTask('内容生成', { prompt: '写一份产品介绍', mode: 'write' })
console.log('路由结果:', route.selected.name)
const exec = router.executeSevenStep(route, { prompt: '写一份产品介绍' })
console.log('七步法:', exec.summary)

// 4. 产品技能吸收引擎
const absorber = new SkillAbsorptionAdapter({ auto_hunt: false })
const analysis = absorber.analyze({
  type: 'docs',
  title: 'AI产品设计方法论',
  content: '核心原理: 用户中心设计模式。关键变量: 用户体验评分。建议迭代: 每周一次可用性测试。',
})
console.log('吸收分析:', analysis.success ? `评分 ${analysis.score}` : analysis.message)
if (analysis.readyForAbsorb) {
  const absorbResult = absorber.absorb(analysis, { industry: '科技', domain: '产品设计' })
  console.log('吸收结果:', absorbResult.summary)
  const validation = absorber.validate(absorbResult)
  console.log('验证:', validation.valid ? '✅ 通过' : '❌ 失败', `(${validation.score}分)`)
}

// 5. 三通道账单
billing.countRagHits('channel_a', 3, { query: '产品介绍生成请求', tokens: 450, latency: 120 })
billing.trackSagTokens(320, { model: 'deepseek-sag', prompt: '写一份产品介绍', generated: 280 })
billing.trackLlmFallback('low_confidence', { query: '复杂产品对比', tokens: 1200, source: 'channel_a' })
const bill = billing.getBill()
console.log('账单汇总:', `${bill.summary.total_tokens} Token, ¥${(bill.summary.total_cost / 100).toFixed(2)}`)

// 6. 变量池自动填充
console.log('变量池扫描:', vpAutofill.scan().summary)
const fillResult = vpAutofill.fill()
console.log(`填充结果: ${fillResult.filled.length} 个变量 (成功: ${fillResult.success})`)
const report = vpAutofill.report()
console.log('填充报告:', `${report.fillSummary.totalCycles} 轮, ${report.fillSummary.totalFilled} 变量`)
```

### 8.2 验证结果

```
✓ 6个适配器JavaScript文件已创建: miniapp/features/*.js
✓ 每个文件语法检查通过 (Node.js lint OK)
✓ 所有适配器遵循 CommonJS module.exports 可被 require
✓ SkillAbsorptionAdapter 类暴露 analyze() / absorb() / validate() 方法
✓ TripleChannelBillingAdapter 暴露 countRagHits() / trackSagTokens() / trackLlmFallback() / getBill() 方法
✓ VariablePoolAutofillAdapter 暴露 scan() / match() / fill() / report() 适配器协议方法
✓ FEATURE_ADAPTER.md 完整记录注入方式和集成点
```

### 8.3 产品接入建议

1. **最小接入**: 在 `app.js` 的 `onLaunch` 中初始化六个Feature
2. **AI对话接入**: 在 `pages/ai/chat/index.js` 的 `onGenerate` 后调用 `cognitiveAdapter.extractFromChat()` + `absorber.absorb()` + `billing.countRagHits()` + `vpAutofill.autoFillIfNeeded()`
3. **名片创建接入**: 在 `pages/brochure/create/index.js` 提交前调用 `designAdapter.analyzeDesign()`
4. **全链路接入**: 在 `MockService` 的路由分发中加入 `router.routeTask()` 决定mock/真实API
5. **技能吸收接入**: 在AI对话/扫描/匹配完成后调用 `absorber.absorb()` 自动沉淀五卡知识
6. **账单追踪接入**: 在AI对话/SAG生成/LLM回退时调用对应账单方法追踪Token消耗与成本
7. **变量池保护接入**: 在AI处理前调用 `vpAutofill.scan()` 检查变量池水位，不足时调用 `vpAutofill.fill()` 保障认知循环不中断

---

*文档结束 · 由 Hermes Agent 自动生成*
