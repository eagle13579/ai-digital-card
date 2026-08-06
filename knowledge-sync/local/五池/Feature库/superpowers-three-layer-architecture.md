---
name: superpowers-three-layer-architecture
version: 1.0.0
description: Superpowers三层架构治理Feature — 大脑(决策)·血肉(执行)·手足(交付)的分离与协同
created_at: 2026-07-05
atomic_models:
  - 三层架构模型: 决策层(Brain)→运营层(Muscle)→执行层(Hands)分离，单向驱动+双向反馈
  - 单一数据源原则: LINK.md引用不复制，源文件始终唯一
  - 五池认知管道: 现象→变量→模型→决策→行动的五阶认知流水线
  - 庙算决策飞轮: 问题→蜂巢→决策→派单→复盘的5步循环
  - 原子5分复用制: ≥5分的原子可跨产品注入，成熟度验证机制
entry_points:
  - layer: 组织架构设计
    trigger: 任何需要分层治理的场景
    usage: "采用Brain-Muscle-Hands三层分离，每层输出格式化和标准化，层间通过LINK.md单向引用"
  - layer: 决策流程优化
    trigger: 决策效率低或执行偏差
    usage: "使用五池认知管道+庙算飞轮5步循环，每一步有明确输出物和门禁"
products: []
applicable_domains:
  - 系统架构设计
  - 组织治理
  - 决策流程优化
  - 知识管理
integration_points:
  - 与现有记忆宫殿L0-L5六层架构互补（全局vs专精）
  - 与三层组织架构原子（战略-运营-执行）同源
source: D:\superpowers\ARCHITECTURE.md + layer-1/INDEX.md
