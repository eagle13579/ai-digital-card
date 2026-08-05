# 全球模型吸收: tencent/hy3 (腾讯混元)
> 吸收日期: 2026-07-17 | 来源: 腾讯官方 + 社区评测 | P0优先级

## 模型概况
- **全称**: Hunyuan Hy3（腾讯混元Hy3）
- **开发者**: 腾讯混元团队 (Tencent Hy Team)
- **发布日期**: 2026-04-23（preview）; 2026-07-06（正式全量）
- **架构**: 295B参数 Mixture-of-Experts (MoE) — 21B激活参数/次
- **专家配置**: 192个专家，Top-8路由
- **MTP层**: 3.8B MTP (Multi-Token Prediction) 层参数
- **上下文窗口**: 256K tokens（原生）
- **许可证**: Apache 2.0（完全开放，无地域/领域限制）
- **定价**: $0.06/M input · $0.21/M output（极低成本）
- **定位**: 开放权重的推理+Agent模型，对标GPT-5.5、Claude Opus 4.8、DeepSeek V4

## 核心心智模型（4个）

### MM-1: 295B/21B稀疏MoE → 超大容量+极低推理成本
Hy3总参数量295B，但每次推理仅激活21B（约为总参数的7%）。192专家Top-8路由实现7%激活率，在保持模型容量的同时将推理计算量压缩到接近中型模型水平。这是**开源MoE的极致工程设计**——7%激活率意味着93%的参数是"备用知识"，随需调用。
- **对军团的借鉴**: 当运行资源受限时，稀疏激活MoE架构是"全量知识+低成本推理"的最优解。7%激活率可作为推理成本估算的基准参考值。

### MM-2: 快+慢双模式推理，模型自主路由
Hy3原生支持两种推理模式：快速模式（直接生成）和深度思考模式（链式推理）。模型可在单个框架内动态切换。这意味着**模型不需要外部prompt工程来区分简单问答和复杂推理**——由模型自身判断何时需要进行深度推理。三种模式（快速/深度/自定义）按需选择。
- **对军团的借鉴**: 在Agent系统中嵌入"推理模式自动切换"机制：简单任务走快速通道（低token消耗），复杂任务自动启用深度推理链。避免全量任务都走"深度思考"造成的浪费。

### MM-3: Apache 2.0 + 完整开放 → 开源模型的商业化范式
Hy3以Apache 2.0许可证发布，无地理限制、无使用场景限制。这是中国科技巨头首次将旗舰级模型（295B）完全开放。这与GLM-5.2（部分开放）、Qwen系列（有限开放）形成对比——**完全开放的许可策略正在成为模型生态的竞争优势**。
- **对军团的借鉴**: 军团自研模型或工具的开源策略可考虑Apache 2.0路线的社区效应——更开放的许可吸引更多开发者，形成生态飞轮。

### MM-4: MTP (Multi-Token Prediction) 层 → 下一代输出加速
Hy3配备了3.8B参数的MTP层，可在单次前向传播中预测多个token而非逐个自回归生成。这是DeepSeek率先引入的技术，Hy3将其工程化到开放权重模型中。MTP使得推理吞吐量大幅提升，同时保持输出质量。
- **对军团的借鉴**: 在需要高吞吐量生成的场景（批量文档处理、代码生成），优先选择支持MTP或多token预测的模型。这是下一个推理效率革命的方向。

## 评测数据
| 基准测试 | Hy3 | 对比模型 | 备注 |
|---------|-----|---------|------|
| SWE-Bench Verified | 74.4%~78.0% | GLM-5.2: 84.2% | 优于多数开源，略逊顶级 |
| AI Index (Analysis) | 33.6 | 超82%已追踪模型 | 表现优质的通用能力 |
| 编码能力 | 竞争力强 | - | 后端场景(SWE-Backend)优秀 |
| 智能等效 | 对标2-5x参数规模的旗舰 | - | 腾讯官方宣称 |
| 推理价格比 | 极优 | $0.06/$0.21 | 旗舰级模型的地板价 |

## 独特定位
- **开源MoE的巅峰**: 295B参数完全开放，Apache 2.0，是目前最大最开放的MoE之一
- **内置Agent能力**: 从一开始就为Agent工作流设计，包括工具调用、函数调用
- **256K原生上下文**: 不需要额外的RoPE扩展，原生支持长文档任务
- **三种推理模式**: 快速模式 / 深度思考模式 / 自定义模式，按需切换
- **极低幻觉率**: 腾讯官方宣称低幻觉率（相比Hy2系列）

## 对军团的价值（P0吸收理由）
1. **开源+Apache 2.0**: 军团可自由部署、修改、商用，无需担心许可问题
2. **21B激活的高效比**: 非常适合军团在有限硬件上运行大规模推理
3. **256K长上下文**: 适合法律文档/代码库/合同等长文本分析
4. **Agent原生设计**: 可作为军团Agent系统的底座模型
5. **中文优化**: 腾讯系模型对中文场景有天然优势，适合军团的中文业务

## 来源
- [Tencent官方: Hy3正式发布](https://www.tencent.com/en-us/articles/2202386.html)
- [HuggingFace: tencent/Hy3](https://huggingface.co/tencent/Hy3)
- [TechNode: 腾讯发布Hunyuan Hy3](https://technode.com/2026/07/07/tencent-launches-hunyuan-hy3-integrates-model-across-multiple-products/)
- [DigitalApplied: Hunyuan Hy3 Open-Weight Reasoning](https://www.digitalapplied.com/blog/tencent-hunyuan-hy3-open-weight-reasoning-model-2026)
- [Caixin Global: 腾讯发布Hunyuan 3](https://www.caixinglobal.com/2026-07-06/tencent-launches-upgraded-hunyuan-3-ai-model-with-free-agent-feature-102461489.html)
- [AIMadeTools: Hy3 Complete Guide](https://www.aimadetools.com/blog/tencent-hy3-complete-guide/)
- [OpenRouter: Hy3 Pricing](https://openrouter.ai/tencent/hy3)
- [Towards AI: Hy3 Review](https://pub.towardsai.net/tencent-hy3-review-21b-active-open-moe-that-beat-glm-5-1-in-a-blind-test-f2e8700d5a5d)
