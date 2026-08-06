---
name: superpowers-agent-hardgate-system
version: 1.0.0
description: Superpowers Agent技能门禁系统Feature — HARD-GATE设计门禁·验证铁律·技能TDD循环·小粒度拆解
created_at: 2026-07-05
atomic_models:
  - HARD-GATE设计门禁: 没有设计批准不得写任何代码，简单项目也不例外
  - 验证铁律: 没有运行验证命令不得声称完成，跳过=撒谎
  - 子Agent驱动开发: 每个独立任务用新子Agent + 两阶段审查(规约+质量)
  - 技能TDD循环: RED(无技能时Agent犯错)→GREEN(技能纠正)→REFACTOR(堵漏洞)
  - 小粒度任务拆解: 每步2-5分钟，一个动作为一步
  - 系统调试四阶段: 理解症状→根因追踪→修复→验证的铁律
  - PR防护方法论: 94%拒绝率驱动的7条谨慎规则
  - 并行Agent隔离派遣: 每个独立问题域一个Agent，不共享上下文
entry_points:
  - layer: 开发流程治理
    trigger: 任何代码修改或新功能开发
    usage: "先过HARD-GATE设计门禁(design approval)→拆小步(writing-plans)→子Agent执行(two-stage review)→验证(verification-before-completion)"
  - layer: 质量保障
    trigger: 遇到Bug/测试失败/异常行为
    usage: "强制走系统调试四阶段，根因追踪完成前禁止修复"
products: []
applicable_domains:
  - AI Agent行为治理
  - 代码开发流程
  - 质量保障
  - 代码审查
source: D:\superpowers\skills/ 14个SKILL.md文件
