---
name: superpowers-decision-flywheel
version: 1.0.0
description: Superpowers庙算决策飞轮引擎Feature — 13大师×50铁律×五池×飞轮的完整决策操作系统
created_at: 2026-07-05
atomic_models:
  - 庙算决策飞轮: 5步循环(问题定位→蜂巢讨论→决策生成→派单执行→复盘进化)
  - 13大师心智模型体系: 孙武/贝索斯/芒格/达利欧/德鲁克/乔布斯/马斯克/费曼/林纳斯/爱因斯坦/巴菲特/毛泽东/宫本武藏
  - 50铁律体系: 6大模块(A灵魂核心/B团队组建/C产品开发/D决策方法/E执行纪律/F进化机制)
  - 五池认知管道: 现象→变量→模型→决策→行动的五阶认知流水线
  - 零依赖向量搜索引擎: TF-IDF(支持numpy/纯Python双模)+BM25混合检索+种子索引
  - MECE拆解+行动池+小闭环: 三合一行动引擎(matching+action+execute)
  - CFC+国学+时光机匹配引擎: 三维匹配(中国模式/经典智慧/出海评估)
  - 安全网关四合一: 意图路由+注入检测+限流+审计日志
entry_points:
  - layer: 战略决策
    trigger: 需要分析复杂问题/制定战略/做关键决策
    usage: "飞轮5步走: flywheel.py analyze '问题' → 匹配大师→铁律自检→五池映射→执行类型判断→复盘"
  - layer: 出海/投资评估
    trigger: 评估新产品/新市场/新投资
    usage: "matching_engine.py CFC匹配+时光机评估+国学经典智慧辅助"
  - layer: 代码开发管理
    trigger: 管理开发任务/拆解需求/追踪进展
    usage: "action_engine.py MECE拆解→行动池管理→小闭环验证"
products: []
applicable_domains:
  - 战略决策
  - 竞争分析
  - 出海评估
  - 产品管理
  - 知识管理
source: D:\superpowers\flywheel.py + matching_engine.py + action_engine.py + vector_search.py + security_gateway.py  
