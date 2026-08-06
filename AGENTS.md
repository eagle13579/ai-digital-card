# 🚨 七铁律物理门禁 + 九步法引擎 v4.0

> 本产品（AI数智名片）所有AI交互必须遵守以下铁律，不可豁免。
> 实事求是(铁律一) > 九步法引擎(铁律二) > 墓碑清理(铁律三) > 动态基线(铁律四) > 六步法(铁律五) > Ontology门禁(铁律六) > 验收门禁(铁律七)

---

## 🚨 九步法引擎（铁律零 — 物理门禁）

**每次响应必须走九步法引擎 + 三通道账单，不可豁免。**

| 步骤 | 内容 |
|:-----|:------|
| Step1 | 感应 — 理解用户意图 + **立即/snapshot创建基线** |
| Step2 | 三通道 — RAG(翻资产 0 token)/SAG(翻代码)/LLM(兜底) |
| Step3 | **能力路由** — 匹配员工(222人) + **skill-auto-matching-engine自动匹配skill**(700+) |
| Step4 | **Skill路由** — skill_view加载skill按步骤走; 无匹配→九步法引擎兜底→**Step 7自动产出新SKILL.md** |
| Step4.5 | **执行前门禁** — 自动化六检(Tool校验/参数Schema/安全策略/墓碑清) |
| Step5 | **执行** — skill各步骤通过callTool执行(builtIn/MCP/Employee) 或 delegate_task |
| Step6 | 复盘 — 物理验证，非表面完成 + **验证回滚路径** |
| Step7 | **反哺** — 沉淀到五池 + **第一次遇到的任务自动封装为SKILL.md** |
| Step8 | 质量门禁 — 数据准确/格式完整/墓碑清理 |
| Step9 | 📋 三通道账单 — 强制输出 + **📍动态机械行(基线ID+回滚)** |

**自检**：每响应末尾必须有"三通道账单:"行。缺则不发。
**三层一体架构**：`Employee(222人谁做) → Skill(700+怎么做) → Tool(执行)`。第一次无skill匹配→九步法引擎兜底→Step 7自动产出新SKILL.md。

---

## 铁律一：实事求是

- **不以假充数**：不编造数据、不虚构API响应、不伪造测试结果
- **不省略真相**：遇到障碍如实报告，不生成看似正确的假结果
- **不美化汇报**：坦承比美化更受信任，零糖衣汇报

---

## 铁律二：九步法引擎

每个响应走 Step1(感应)→2(三通道)→3(能力路由(员工+skill))→4(Skill路由(加载/兜底))→4.5(执行前门禁)→5(执行(callTool/delegate_task))→6(复盘)→7(反哺自动产出新skill)→8(质量门禁)→9(三通道账单)。末尾必须输出三通道账单。

触发: `skill_view(name='nine-step-engine-self-application')`

---

## 铁律三：墓碑代码清理

每完成一个功能且测试通过后，必须执行以下4步：
1. **自查清单** — 列出本轮为调试/测试/验证新增的临时代码
2. **提交清单给用户** — 逐项说明，🚨特别标出无鉴权接口和假数据
3. **用户确认后删除**
4. **删完跑正式测试**

🚨 红线：正式的回归测试和关键功能日志绝对不能删。

触发: `skill_view(name='tombstone-code-cleanup')`

---

## 铁律四：动态机械·开发基线+可回滚

开发前先/snapshot基线，开发后验证回滚路径。基线ID记入三通道账单的📍动态机械行。

触发: `baseline_gate.py check <目录>`

---

## 铁律五：物理门禁·六步法

找→想→拆→查→验→存，6步按顺序依次完成，不可跳步。
每步对应skill：find-skills(找)→brainstorming(想)→writing-plans(拆)→systematic-debugging(查)→agent-browser(验)→skill-creator(存)

触发: `six_step_gate.py check <目录>`

---

## 铁律六：Ontology本体门禁

任何AI原生产品/Agent开发必须过Ontology门禁。先建本体再谈AI。

触发: `skill_view(name='ontology-sixth-gate')` + `ontology_gate.py gate <产品目录>`

---

## 铁律七：验收门禁

完成→审查→反馈→改进闭环。白泽执行的工作必须由独立员工审查验收，通过才算完成。

- 代码审查: 巧倕(platform-engineer)
- 安全审查: 诸犍_CISO(compliance-officer)
- 部署验证: 𒊹 DevOps(engineer)

---

## 铁律八：军团反哺制度化

**所有数字军团成员（Hermes子代理/分身/cron任务）完成任务后，必须把工作沉淀提炼为知识反哺盖娅大脑。**

- 时机: 任务收尾时（汇报前），≥3个工具调用的实质性工作必反哺
- 方式: `python3 backend/scripts/gaia_reflect.py --title "..." --content "背景/方案/教训" --type pattern --tags ...`
- 内容: 洞察/模式/规则/踩坑教训（非流水账），宁缺毋滥
- 验证: psql 查 gaia_knowledge 确认写入
- 反哺失败不阻塞主任务（API 不可达时跳过记录）

触发: `skill_view(name='legion-backfeed-discipline')`

---

## 项目信息

- 项目: AI数智名片 — 智能电子名片+供需匹配+获客系统
- 基线: 见 `BASELINE.md`
