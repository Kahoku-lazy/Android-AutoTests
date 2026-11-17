## Context

现状（见 proposal.md - Why）：编写与验收到目前为止是「一份长 Markdown + 独立模型判卷」，产物形态决定了后续所有复杂度；执行侧的结构化用例（每步 action/expected + 页面锚点 + 日志证据）与设计产物没有交集，只能人工再写一份。

约束：

- AgentScope 2.0.9 的 `GoalPipeline(executor, verifier, verifier_reset_context=True, max_iters, max_retries)`：执行者输出 `{report}`，验证者输出 `{result: pass|fail|impossible, message}`；验证失败时把 `message` 作为 system 消息回给**同一个**执行者，执行者上下文保留。
- `engines/` 禁止 import `apps.*` / `django.*`；产物存储与预检必须留在引擎侧。
- 用例库 `cm_test_definitions` / `cm_case_steps` 的列是既有契约，落库侧需要做字段映射，不能改表结构（本次）。
- 历史任务结果（含 `modules`）与已入库的 44 条用例必须继续可读。

## Goals / Non-Goals

**Goals:**

- 产物从「长文档」变为「三段结构化数据」，单次模型输出有界，从而删除模块切分、截断二分、统计回写三套兜底。
- 编排收敛为一条目标流水线、两个角色；删除 SOP 双轨与模块规划角色。
- 验收只判「数据与需求一致」与「无捏造」，且把可机器判的部分交给代码预检。
- 三段产物能被确定性渲染成 Markdown + Mermaid，供人读与后续导出。

**Non-Goals:**

- 不产出设备执行用的结构化用例 YAML，不改设备执行工作流（`case_file.py`、`step_brief.py`、`platform_run.py` 不动）。
- 不引入覆盖率/方法数等新门禁（旧门禁已删，不换一套新的）。
- 不做产物独立建表；产物先随 `Task.result` 存储。
- 不做历史数据迁移或回填。

## Decisions

### D1：用「增量结构化交付」替代「一次生成整篇文档」

编写角色通过 4 个工具交付（`save_state_machine` / `append_scenarios` / `append_cases` / `read_artifact`），每批 ≤20 条，工具返回只回条数不回内容。

- 理由：截断的根因是「一次生成 5 万字」，切模块只是把问题摊薄；改成有界批次后，模块切分、60k 阈值、递归二分、父结果丢弃全部不需要。
- 备选：保留模块切分但去掉规划模型（用确定性切块）——仍然要处理「批量之间如何拼装」「批次间状态一致」，复杂度没降。
- 备选：先用 Markdown 再解析成结构化——解析器与提示词格式强耦合，已被证明脆（`case_document_check.py` 依赖 `## 六、`、`| 用例编号 |`）。

### D2：单一 GoalPipeline，执行者上下文不重建

`run_goal_module` 改为 `run_case_authoring_artifact`：一次 `GoalPipeline(writer, verifier, verifier_reset_context=True, max_iters=3, max_retries=3)` 跑完整个需求，执行者只构建一次。

- 理由：`GoalPipeline` 本来就是把驳回意见作为 system 消息发回同一个执行者；现有实现每轮 `build_case_writer_goal()` 重建执行者再把上一版全文拼进输入，等于把 O(n²) 的上下文成本自己造出来。
- 备选：每轮重建执行者 + 全文回灌（现状）——成本高且容易把「只修三条用例」变成「重写全文」。

### D3：只保留两个角色，模块规划角色删除

角色配置收缩为 `case_writer_role` + `case_verifier_role`；`case_planner_role`、`case_writer_goal_role`、`case_verifier_goal_role` 删除。

- 理由：规划角色的唯一职责是切模块；切模块取消后它没有存在意义。Goal 变体与主变体的提示词相似度 0.97，保留两套等于双份维护成本。
- 备选：保留 planner 做「子系统划分」——在增量交付下，子系统信息由状态机本身表达（状态名即页面/模式），不需要额外模型。

### D4：事实预检做成工具，而不是平台侧后置校验

新增 `check_artifact_facts()` 只读工具，同时给验收角色与任务结果使用；判定三类事实：source 是需求子串、引用完整、数值可追溯。

- 理由：让验收模型「凭感觉判断有没有捏造」不可靠；把可判的部分代码化，模型只判语义层面的「表达是否被原文支持」。
- 备选：只在平台侧跑预检、不交给模型——模型看不到结论就会重复追问或放水，且驳回意见无法引用具体条目。

### D5：状态机完整性降为告警，不阻断

「每条迁移至少被一条场景覆盖」只进预检告警，不参与 `pass/fail`。

- 理由：用户明确验收只判数据一致与捏造；把覆盖率再引进来等于换一套门禁。
- 代价：漏迁移不会被拦下；用告警 + 报告可见来暴露，由人决定是否重跑。

### D6：渲染是确定性派生

Markdown 与 Mermaid 由产物渲染，模型不写第二份。

- 理由：模型写图和写文档会出现「图与数据不一致」；派生物可重算。
- 备选：让模型直接写 Mermaid——人看着直观，但机器无法校验，且与结构化产物必然漂移。

### D7：产物存储留在引擎侧内存，随 `Task.result` 落库

`ModuleStore` 改造为 `ArtifactStore`（states/transitions/scenarios/cases/report），生命周期为单任务；任务结束时整体序列化进 `Task.result.artifact`。

- 理由：产物量级可控（≤300 条用例、单条 ≤2KB，序列化后 <1MB，`longtext` 足够），不建表可以省掉迁移与清理策略。
- 备选：建 `case_artifact` 表——需要迁移、权限、清理，收益只有跨任务复用，当前没有这个需求。

## 模块防火墙自检

- `engines/**` 不新增任何 `apps.*` / `django.*` 依赖：产物存储、事实预检、渲染器全部在 `engines/agents/workflow/` 内，需求正文与 SKU 关键词目录已由引擎侧读取。
- `backend` 侧写库仍走 `api.py`：`task_runner` 调 `case_manager.api.import_case_rows`（既有跨 App 写入口，未新增旁路）。
- `Task.result` 由 `task_list` 自己的 `api.py` 落库，不新增跨 App 写。
- 前端不直连数据库；报告字段变化由 `task_reports.build_task_flow` 单点适配。
- 未引入新的 service/runner 跨模块 import。

## Risks / Trade-offs

- **[状态机被模型「归纳」出来，可能归纳错]** → 每个状态/迁移强制 `source` 子串校验；归纳错的条目在预检阶段即被拦下，不会进入用例。
- **[验收只判两条，可能放过低覆盖产物]** → 迁移覆盖率进 `facts.warnings` 并在报告展示；需要收紧时由人重跑，不靠模型。
- **[增量工具轮次变多，可能顶到 ReAct 迭代上限]** → 每批 ≤20 条、`ReActConfig.max_iters` 从 20 提到 60；工具返回只回计数，避免上下文膨胀。
- **[产物 JSON 变大撑爆 `Task.result`]** → 单条用例限制字段长度（title ≤200、source ≤500、每步 ≤200）；超出时工具报错而不是静默截断。
- **[删除 `modules` 导致历史报告字段缺失]** → 报告侧对 `modules` 缺失做空值兜底；历史任务不改写。
- **[验收口径收窄后，编写角色可能「少写少错」]** → 场景必须覆盖全部主流程迁移（告警可见）；同时 `document` 渲染出场景/用例条数，人一眼能看出缩水。

## Migration Plan

1. 引擎侧先落新产物契约与工具（新增文件，不改旧路径），跑通「一段需求 → 三段产物」。
2. 切换编排：`task_runner` 改调新流水线，`Task.result` 写新结构；旧 `CaseAuthoringWorkflow`、`case_module_plan.py`、`case_document_check.py` 随后删除。
3. 角色配置与提示词：新增两角色提示词，删除 5 个旧角色中的 3 个与 2 个 Goal 变体提示词。
4. 回归：`tests/graybox/unit/test_case_*` 重写；用一份真实需求（H6810 或 H717D 规格）跑通完整任务，检查产物、预检、判决、入库。
5. 回滚：本次改动集中在引擎工作流与角色配置，回滚为 revert 对应提交；历史任务数据不受影响（产物只在 `Task.result` 内）。

## Open Questions

- 产物是否需要跨任务复用（例如「H6810 的状态机复用给下一版需求」）：当前不做，等出现第二次同型号需求再评估建表。
- Mermaid 是否需要前端直接渲染成图：当前只下发文本，前端按需再议。
