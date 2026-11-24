# REVIEW — Agent 文档审计复核与修复方案

> 复核时间：2026-11-19 15:49–16:10（Asia/Shanghai）
> 复核方式：全程只读。lead 亲自逐行复核 A 组 5 条代码级指控；三个只读子代理并行复核 B/C/D/结构组；关键定性证据（D8 规格依据、C1 失效测试、CI 门禁口径、A2 可达性）由 lead 二次抽验。
> **重要前提：复核期间仓库存在并发写入。** 另一会话正在实施 `fix-agentscope-usage-defects`（record.py 已加 `sop_roles`，15:53 修改），并于 15:58:50 提交 `bc719c17 refactor(models): 把 govee 厂商改名为 openai`（含迁移 0082/0083，横跨 backend/engines/frontend）。本报告行号以复核时点 read 实测为准；涉及并发文件的结论已标注时效。

---

## 一、总体结论

**原审计 25 条指控 + 5 条结构项：方向全部成立，无一条完全不属实。** 但需要四类修正：

1. **定性过强（3 条）**：B1 不是严格逻辑互斥（红线 4 带「先上报」程序限定）；D8 不是「权限绕过」（规格明文要求登录可读全量字段，真问题是保密口径冲突）；A2 是**有书面记录的有意暂缓**（活跃变更明文「GoalPipeline 生产接线…需求方明确暂缓」），不是失控缺陷——但「编造数据入库」的 interim 行为仍不可接受。
2. **机制/行号不精确（4 条）**：D1（urls 注册 3 个 router 而非「只有 roles」；死代码无调用方）、D3（可选乐观锁：前端不传 revision 时**静默放行**而非报错；:96 是入参不是出参）、D4（后端业务字面量 9 处非 8）、C2（`event_log.py` 是事件**面板日志**写文件，不是「事件落库」实现；引擎侧根本没有落库绑定/折叠的实现文件）。
3. **规模低估（2 条）**：C1 残留远不止 5 处（技能文档、utils CLI 默认路径、ruff.toml、4 份现行 openspec 规格、一条**必失败的架构测试**、多处 docstring）；C4 docstring 残留实际 15 处（审计列 3）。
4. **时效（2 条）**：D5 的第三厂商 govee 已被并发提交改名为 openai（互斥仍在，值变了）；A3 的修复在复核期间由并发会话落地工作树（record.py 名字映射 + runner.py:211 传映射 + workflow/AGENTS 文档同步，尚未提交），生产 SOP 路径已不再依赖奇偶推断。

**复核新发现（原审计未列，见第五节）**：最重要的是 **A1 与 A2 耦合**——当前恒假的发布门禁意外挡住了大部分「编造用例入库」路径；**只修 A1 不修 A2 会打开编造数据的闸门**。其次是 **CI 的 Python 门禁只跑 `pytest --collect-only`（收集不执行）**，这解释了 A1 与失效架构测试为何能存活。

---

## 二、逐条判定总表

| # | 指控 | 判定 | 关键修正 |
|---|---|---|---|
| A1 | 发布门禁恒假 | **属实** | 测试手工造全集运行绕过生产路径，故测试绿、生产死；goal/team 工作流不走此门禁（见 A2） |
| A2 | goal/team 不建 Agent、编造用例入库 | **属实（有意暂缓）** | 暂缓有书面记录；但 stub 编造 rows 经 `import_case_rows` 入库不可接受；team 只校验用户粘贴的 JSON，不编造 |
| A3 | 报告角色按 reply 奇偶猜 | **属实（修复已落地工作树，未提交）** | 复核期间并发会话完成 4.1/4.2/4.4：record.py 名字映射 + runner.py:211 传 sop_roles + workflow/AGENTS 已知限制 2 更新；奇偶仅作无映射兜底；密钥归属一直按名字绑定，合规 |
| A4 | 双模型压成单 model、账本错账 | **属实（比审计更重）** | 双重缺陷：run 级 model 覆盖逐次 model + 兜底读错键（`model_name` vs 实际 `model`）；任务正文费用与账本费用会分叉 |
| A5 | 取消令牌不复位 | **属实** | `CancelToken.clear()` 存在但线程路径零调用；`drop_thread` 仅测试调用；SOP 任务侧 `clear_cancel` 收口正常（对照） |
| B1 | 红线 4 vs 红线 10 | **部分属实** | 原文准确；「直接互斥」言重，属表述张力，可调和 |
| B2 | rules 教旧包 vs 现行红线 | **属实** | rules 另有 8 行旧引用；`tools_config.py` 全仓 0 文件；门禁反而要求旧目录不得存在 |
| B3 | 配置只经 config.py vs models 自读 .env | **属实** | models.py 用 `dotenv_values`+`os.environ` 直读；config.py 只剩 log_keywords 职责 |
| B4 | WS 生产点 1 vs 路由清空 | **属实** | 残留不止 apps/AGENTS：活跃 spec knowledge-assistant-voice、ARCH/PRD 均滞后 |
| B5 | report 接口存在 vs 已下线 | **属实** | urls 11 条无 report、无视图残留；前端文档与代码一致，后端文档滞后 |
| B6 | 前端没有测试运行器 | **部分属实** | 主句假（vitest + 88 个 spec），括号真（src 下 0 个） |
| C1 | engines/agents 残留引用 | **属实（规模低估）** | 5 处点名全中；另发现技能/utils/ruff/4 份现行 spec/必失败测试 test_channels.py:79 等大量残留 |
| C2 | events/ 目录不存在 | **属实（职责需纠正）** | event_log.py 是面板日志非落库；「目录现状」行失实；token_usage/ 也非空目录 |
| C3 | 测试迁移表失实 | **属实** | 实际 ae_harness/unit 24 + backend_bridge/unit 17 + device/unit 2；无 e2e；表里全无这两个现行目录 |
| C4 | docstring 指向已删模块 | **属实（15 处）** | sop_runner 5 处 + agent_executor 10 处；backend 0 引用 |
| C5 | AIAgent / filter_agents_for_user | **属实** | 0070 迁移 DeleteModel 坐实；函数代码 0 命中；api.py:138 docstring 也残留 |
| D1 | /ai/agents/ 必 404 | **部分属实** | 路由确不存在、调用必 404，但无人 import（死代码）；两条前端注释本身失实 |
| D2 | 无发布入口、永远 draft | **属实** | 409 发生在首次发送（非打开对话）；任务提交拒绝是 400；存量记录经迁移 0080 已 published |
| D3 | revision 乐观锁失效 | **属实** | 后端是「可选乐观锁」；前端从不传 → 跳过校验静默覆盖（后写者赢） |
| D4 | release_state 无 SSOT | **属实** | 业务字面量 9 处（另模型默认 2 + 迁移 4）；前端魔法串 2 处（AssistantCard.vue:72/98） |
| D5 | 厂商枚举互斥 | **属实（时效+降级）** | govee→openai 已提交；ModelProvider 零消费，属死枚举背离非运行时冲突；usage_ledger AGENTS 红线 2 是第三套口径 |
| D6 | EvalFailure.sample 必填不下发 | **属实（低危）** | 前端从不消费该字段，纯类型契约债；内部 evaluate_target 是死代码 |
| D7 | 分页口径分歧 | **属实** | 两页是带明示注释的有意设计（小表全量）；条款语境偏 users 页；属口径分歧非实现 bug |
| D8 | RoleViewSet 权限绕过 | **部分属实** | 事实链成立（任何登录用户可读全部 system_prompt），但 spec ai-role-registry:114 明文如此要求；真问题是与名片隐藏逻辑的保密口径冲突；api_key_env 只是变量名非密钥 |
| S1 | 7 个空 AGENTS + knowledge_search 缺失 | **属实** | 0 字节恰 7 个，名单一致；delta 承诺在 apps/AGENTS.md:60 |
| S2 | prompts 空目录 | **属实** | 存在且空；不构成实质违规，属残留空壳 |
| S3 | ae_harness/logs 6.7MB | **部分属实** | 首测 6.82MiB，复核期间被并发会话清空；.gitignore:50 覆盖；助手对话报告另落 logs/agents/assistants/ |
| S4 | 一级子包漏 utils | **属实** | 清单 5 个，实际 6 个包目录 |
| S5 | 8899/8811 双端口 | **属实** | :83/:134 用 8899，:169 用 8811，同一命令 |

原审计第六节「没有冲突」6 项：依赖方向、中间件三类准入、两个异常登记、报告落点、adb 门面均复核一致；**CI 两 job 名称对齐属实，但需补充：python job 的测试门禁是 `--collect-only`，不执行测试**（ci-phase1.yml:43 + check_gates.py:522-524）。

---

## 三、A 组详细证据链与最佳修复方案

### A1 发布门禁恒假 —— 最高优先，但与 A2 耦合

**证据链（全部逐行复核）**：
- `backend/apps/ai_assistant/api.py:470`：`start_live_eval` 按类型前缀过滤样本 → assistant 得 `["A1"]`，workflow 得 `["S1","S2","S3"]`。
- `api.py:520`：`create_live_run` 原样存子集 `sample_ids=list(sample_ids)`。
- `api.py:648`：`eval_passed` 要求 `latest.sample_ids == sample_ids()`，而 `eval_samples.py:101-103` 返回全集 `GATE_IDS = ("A1","S1","S2","S3")`（:6）。子集 ≠ 全集 → **恒假**。
- `views_drf.py:516-517 / 535-538`：助手与 SOP 工作流发布均被「自测未通过，不能发布」拒绝。
- `live_runner.py:46`：执行器只跑 `run.sample_ids`（子集），不会补齐全集。
- **测试为何绿**：`tests/ai_assistant/api/test_release.py:103` 手工 `create_live_run(..., ["A1","S1","S2","S3"])` 造全集运行，绕过了生产创建路径 `start_live_eval`。
- 旁证：`record_eval`（scripted 自测）存全集，但 `eval_passed` 明言「旧的 scripted 自测记录不参与判定」，只读 LiveRun。
- 范围修正：goal/team 工作流 `workflow_requires_eval=False`（api.py:623-625），不走此门禁；「任何工作流都不能发布」不准确——**助手与 SOP 工作流恒不能发布**。

**最佳修复（推荐方案 1）**：
1. 在 `eval_samples.py` 增加共享函数 `gate_ids_for(kind)`（assistant→A 前缀，workflow→S 前缀），`start_live_eval` 与 `eval_passed` 同读这一份，比较改为 `latest.sample_ids == gate_ids_for(kind)`。语义保持「该类型适用的当前启用样本全部跑过且空清单」，样本集变化仍使旧通过失效。
2. 同步修订活跃变更 `assistant-release-eval` 的 spec 措辞（「当前启用的样本集」→「该类型当前启用的样本集」）与 tasks 3.5 描述（该变更全部任务已✅但未归档，属在途实现缺陷，走 openspec-update-change 收口）。
3. **补一条走生产路径的回归测试**：EvalRunView → start_live_eval → execute（pytest 下不真跑，注入完成态）→ publish 成功；杜绝再次手工造全集绕过。
- 不推荐方案 2（存全集、只跑适用子集）：progress_total 失真、不可跑样本被冒充通过。

**耦合警告**：A1 当前意外挡住了「goal 工作流绑定新助手」的发布链（goal 发布要求执行侧名片已 published，api.py:668-675）。**修复 A1 会放大 A2 的编造数据风险，A2 的 fail-closed 必须先于或随 A1 同批落地。**

### A2 goal/team 桩 —— 有意暂缓，但 interim 行为必须 fail-closed

**证据链**：
- `task_runner.py:439-441`：`_attempt` 桩 `del prompt; return {"passed": True, "rows":[{"title": task.title or "用例", "module":"默认"}]}` —— 恒通过并编造一行用例。
- `task_runner.py:447-452`：编造的 rows 经 `case_manager.api.import_case_rows` **真实入库**。
- `task_runner.py:464-474` + `team_breakdown.py:44-60`：team 只把 `task.goal/attachment` 当模块 JSON 校验，不建 Agent、不编造（用户粘贴什么校验什么）。
- `goal_case.py:30-58`：引擎侧是真实的可注入目标循环（attempt 回调可替换），docstring 明言「生产调用方传入官方 GoalPipeline」。
- **有意暂缓的书面记录**：活跃变更 `fix-agentscope-usage-defects/proposal.md:13`「不做：…GoalPipeline 生产接线/会话持久化/向量库切换（需求方明确暂缓）」。
- **历史决策张力**：归档变更 retire-engines-agents 的 design.md:122（D9）对旧 YAML 用例流水线拍板「**放弃**：不重建、不改造」；而 goal_case/team_breakdown（2026-11-18 新建）走的是 AgentScope 官方 GoalPipeline/TeamPipeline 新路线，且 openspec 全仓无任何变更引用这两个模块——**新路线未见立项记录**，与 D9 的关系需要需求方明确。
- **UI 可达**：`SopWorkflowEditor.vue:21-22` 仍提供「目标·用例编写」「团队·需求拆解」选项。team 工作流两侧名片为空 → publish_workflow 跳过绑定检查（api.py:669-670）→ 可发布可提交；goal 工作流绑定存量已发布助手（迁移 0080）时同样可达。

**最佳修复（需决策，推荐 b）**：
- a) UI 隐藏/禁用 goal/team 选项 + 后端提交拒绝（最干净，但前后端两处改）；
- b) **后端 fail-closed**：`_finish_goal`/`_finish_team` 在 GoalPipeline 正式接线前直接以 FAILED 收口，reason 写明「用例编写/需求拆解尚未接线（占位）」，**不调用 import_case_rows**；UI 选项保留但提交后得到明确失败而非假成功。改动最小、立即消除编造数据入库。
- 无论 a/b：GoalPipeline 生产接线必须另立 OpenSpec 变更并经需求方批准（同时澄清与 D9「放弃」的关系——是推翻 D9 还是 D9 仅指旧 YAML 路线）。

### A3 角色奇偶推断 —— 修复在途，不要重复修

**证据链**：
- 现行 `record.py:619-639`：`sop_roles` 名字映射优先（:631），无映射时奇偶兜底（:633）——task 4.1 已实现。
- `runner.py:211`：复核期间并发会话已补传 `sop_roles`（task 4.2 完成）；workflow/AGENTS.md「已知限制 2」已同步为名字映射口径（task 4.4 完成）。生产 SOP 路径的角色归属不再依赖回复顺序；奇偶推断仅留给未传映射的调用方兜底。
- `render.py:899-902`：非 executor 一律显示「验收者」（映射落地后角色只有两种，风险收敛；可顺手把未知角色显示为角色名而非默认为验收者）。
- `event/AGENTS.md:18` 的「禁止按 reply 顺序猜角色」语境是**密钥归属**；密钥归属一直按 agent 名绑定（record.py:623-624），合规。显示角色与文档字面存在张力，task 4.4 将更新 workflow/AGENTS「已知限制 2」。

**最佳方案**：修复已由 `fix-agentscope-usage-defects` 在工作树落地（4.1/4.2/4.4），剩 4.3 单测与 5.x 门禁/提交。本批只需：① 确认 4.3 乱序归属/兜底/attempt 序号测试补齐；② 随该变更提交并过 CI；③ 可选顺手把 render.py:901 未知角色显示为角色名而非默认「验收者」。**不另起修复，避免撞车。**

### A4 双模型错账 —— 比审计更重，属钱口径须变更申请

**证据链**：
- `bound_sop.py:96-99`：`role_models` 两套绑定正确传入 run_sop；`record.py:624` 逐次用量按 agent 名取模型；`usage.py:63,74`：TokenUsage 逐次带 `model` 键。**逐次数据是对的。**
- `sop_ui.py:73` + `bound_sop.py:131`：结果形状只有单 `model=executor.model_name`。
- `task_runner.py:110-115`：入账传 `model=outcome.model`（执行侧）。
- `usage_ledger/api.py:111`：`model=model or str(item.get("model_name") or "")` —— **双重缺陷**：① run 级 model 优先覆盖逐次 model；② 兜底键 `model_name` 不存在（实际键是 `model`），即使传空 model 也取不到 → 模型空 → 按红线 4 记 0 价。
- 对照 `task_runner.py:140`：`_price_call_costs` 读 `item.get("model")`（正确键）→ **任务正文费用按逐次模型算对，账本按执行侧模型算错，两个数字分叉**。验收侧用贵模型时账本静默少记。
- chat 路径（assistant_threads.py:228）单角色无实害；live_runner._ask_model 的用量恒 0 token（见 N4）。

**最佳修复（钱口径 → 按根 AGENTS 硬约束 4 先提变更申请）**：
1. `record_run_usages` 改逐次优先：`model=str(item.get("model") or "") or model`（修键名 + 修优先级，run 级仅作兜底）。
2. 单测：双角色双模型 usages → 账本各行保留各自模型、按各自价目计费；run 级兜底仅在逐次缺失时生效。
3. `SopRunResult.model` 保留为汇总字段（或后续增 models 映射），不动结果形状即可修复账本。
4. 同批修订 `usage_ledger/AGENTS.md` 红线 2「厂商只有两类」（govee→openai 提交后已失实，见 N5）——红线条款并入变更申请。
5. **协调**：并发会话刚改过 api.py/pricing.py（改名），本修复与其正交但同文件，须待其提交完成后 rebases 再动。

### A5 取消令牌不复位 —— 独立小修

**证据链**：
- `thread_run.py:86-90`：令牌按栏缓存；`:103-107` cancel 置位；`:110-119` drop_thread 存在但**生产零调用**（grep 全仓仅测试 test_assistant_thread.py:15-16）。
- `control.py:122-125`：`clear()` 存在，生产零调用（仅 test_run_control.py:88）。
- `views_drf.py:437-441`（取消栏）与 `:455-458`（删栏）只调 request_thread_cancel；`assistant_threads.py:207-217`：新轮复用缓存实例 + 已置位令牌 → CancelMiddleware 立即抛 RunCancelled → 「已取消」，**该栏永久不可用**（直到进程重启）。
- 对照：SOP 任务侧 `cancel.py clear_cancel` 在 task_runner.py:577 正常收口——线程路径漏了同样的收口。
- 附带：删栏后 `_AGENTS/_CANCELS` 条目不清理 → 内存泄漏（N9）。

**最佳修复**：
1. `assistant_threads._run_turn` 在状态检查后、取实例前 `thread_cancel_token(thread_id).clear()` —— 每轮开始复位，**保留栏实例与对话记忆**（不能用 drop_thread 复位，会丢记忆）。取消语义不变：运行中置位仍在下次模型调用前生效。
2. `AssistantThreadDeleteView`（删栏）后调 `drop_thread(thread_id)` 释放内存。
3. 单测：取消一轮后同栏再发 → 正常完成；删栏后字典无残留。
- 不新增异常、不改红线；与 fix-agentscope「不动取消异常口径」不冲突（clear 是既有 API）。

---

## 四、B/C/D/结构组修复建议（按批次）

### 批次 D-DOC：文档腐烂一次性收口（一个 OpenSpec docs 变更）

**须先变更申请的红线/规则条款**（根 AGENTS 硬约束 4，四要素：改什么/为什么/影响面/回退）：
- B1：tools/AGENTS.md 红线 4+10 调和为「准入形态含 Python/Skill/MCP；当前只实现 Python 函数工具；引入 Skill/MCP 须先上报批准」。
- B2：.agents/rules/engines-code-style.md §6 及 :6/:15/:17/:51/:53/:85/:87/:96/:122 旧包引用改为 ae_harness/backend_bridge 现行口径；删 tools_config.py 叙述。
- B3：middleware/AGENTS.md:21 改「参数从构造函数进来；密钥由 agents/models.py 自读仓库根 .env（见 ae_harness/AGENTS 红线 6）」。
- B4：apps/AGENTS.md:41 改「当前没有 WS 生产点（知识助手已下线）；新增先走 OpenSpec」。
- C1：根 AGENTS.md:66 注释模板 `engines.agents.<子包>` → `engines.ae_harness.<子包>` / `engines.backend_bridge.<子包>`；engines/AGENTS.md:18「正在退役」→「已退役（archive/2026-11-17-retire-engines-agents）」（:23 禁止恢复红线保留不动）。
- C2：backend_bridge/AGENTS.md:4「目录现状」删 events/（或标未落地）；红线 9 改为「事件落库的绑定/折叠归本目录（落地时建 events/）；当前 event_log.py 只写事件面板日志，写库在后端」；token_usage/「空目录」描述同步。
- C5：task_list/AGENTS.md:17/:22 依赖边界改为现行 `assistant_api.get_sop_workflow / list_sop_workflows / resolve_sop_release`（AIAgent 已随 0070 删除）。
- D5：usage_ledger/AGENTS.md 红线 2「厂商只有两类」→ 三类（deepseek/dashscope/openai）。
- D7：ops-console/AGENTS.md:19 分页条款注明例外（users 服务端分页；roles/model-configs 小表全量+前端切片系有意设计），或改实现加服务端分页（推荐改文档，小表无必要）。

**描述性修订（同变更内，非红线）**：
- B5：task_list/AGENTS.md:8-9 删 report 接口叙述（与前端 AGENTS 对齐）。
- B6：tests/AGENTS.md:102 改「前端 spec 集中在 frontend/tests/（vitest），不在 frontend/src 内；路径能否解析只有后端能回答」。
- C3：tests/AGENTS.md 迁移表 engines/agents 行替换为 engines/ae_harness/unit(24)、engines/backend_bridge/unit(17)、engines/device/unit(2)；删 e2e 虚记。
- C4：15 处 docstring 残留批量改（sop_runner 5 + agent_executor 10，清单见子代理报告）；走 engines-docstring-check 流程；record.py/render.py 待并发会话完成后改。
- S1：7 个 0 字节 AGENTS 补最小 delta 或删占位并改上级承诺；补 knowledge_search/AGENTS.md。
- S2：删空目录 agents/config/prompts/。
- S4：engines/AGENTS.md 一级子包清单补 utils。
- S5：project-viz/AGENTS.md:169 端口 8811 → 8899 统一。
- D1：删死代码 frontend api/agents.ts；修正 ai-assistant/AGENTS.md:35 与 assistants.ts:1 两条失实注释。
- B4 连带：openspec/specs/knowledge-assistant-voice 活跃规格仍 MUST 已下线路径（归档时 delta 未同步）→ openspec-sync-specs 收口；ARCH-平台架构设计.md:130、PRD-平台总需求.md:151 同步。
- C1 连带：技能 SKILL.md/scripts 示例路径、utils/module_docstring.py CLI 默认路径、utils/gen_arch_stats.py:195/:217、ruff.toml:16-17/:61-62 豁免、4 份现行 openspec 规格（ai-model-gallery/agent-role-skills/ai-screen-vision/project-log）旧包引用。

### 批次 D-TEST：失效测试与门禁

- **test_channels.py:78-87 必失败**（断言已删目录必须存在）：重写为断言 `engines/agents` **不存在** + 新落点 adapters 禁令（与 check_gates.py:475-477 同口径）。
- event_log.py:21 引用的 test_event_log.py 不存在：补测试或改引用。
- **治理决策（N2）**：CI python job 只 `--collect-only`。建议至少把 arch + engines + ai_assistant 的 unit 套件纳入 CI 执行门禁，否则 A1 类「测试绿生产死」与失效架构测试永远漏网。

### 批次 D-CONTRACT：前后端契约

- D2：补发布 UI（按钮 + POST publish + 失败清单展示 + draft 提示）。**属 assistant-release-eval 既定 Impact（前端助手页：草稿标识、自测、发布和失败清单），task 4.1 已✅但发布入口缺失——在该变更内补完，不另立单**。前置：A1 修复。
- D3：前端 updateAssistant 携带 revision（出参 serializers.py:116 已下发），409 时提示刷新；后端保持可选锁不变。
- D4：backend/models/constants.py 增 `ReleaseState(StrEnum)`（draft/published），替换 9 处业务字面量 + 模型 default/choices；前端 types.ts 改联合类型、AssistantCard.vue 用常量。纯重构无行为变化。
- D5：ModelProvider 死枚举对齐三家（或删除）；真实 SSOT 是 KEY_BY_PROVIDER + PROVIDER_CHOICES，文档注明。govee→openai 改名已由并发提交完成，本项只收尾。
- D6：前端 EvalFailure.sample 改可选（或后端 live_run_detail 补发 sample——run.failures 里本就有该字段，api.py:577 加一行即可，推荐后者使类型成真）。顺手删死代码 evaluate_target（全仓无调用方）。
- D8：**规格级决策，不是 bug**。现状合规（ai-role-registry spec:114 明文登录可读 12 字段）。两条路线：(a) 维持现状，承认「角色配置是运营资产、登录可读」，并在名片侧文档说明提示词并非保密资产；(b) 收紧角色读权限（运营/作者可读全量，普通用户只读 role_id/name 选项），需改 spec + 实现 + 前端 RoleOption 取数。**按硬约束走变更申请，由需求方拍板。** 可选优化：增轻量 /ai/roles/options/ 只发 role_id/name，避免前端过度取数。

---

## 五、复核新发现（原审计未列）

| # | 发现 | 证据 | 严重度 |
|---|---|---|---|
| N1 | A4 兜底读错键：`model_name` vs 实际 `model`，即使去掉 run 级覆盖也取不到模型 → 记 0 价 | usage_ledger/api.py:111 vs usage.py:74 | 高（并入 A4） |
| N2 | CI python 门禁只收集不执行测试；「CI 是唯一质量闸门」名不副实 | ci-phase1.yml:43、check_gates.py:522-524 | 高（治理） |
| N3 | test_channels.py:78-79 断言已删目录必须存在 → 该用例必失败（CI 不跑所以没暴露） | tests/arch/unit/test_channels.py:78-79 | 中 |
| N4 | live eval 用量恒 0 token、round 键是提示词正文；「真模型评测」入账全 0 | live_runner.py:158-165 | 中（评测计费失真） |
| N5 | govee→openai 提交后 usage_ledger/AGENTS 红线 2「厂商只有两类」失实；constants.py ModelProvider 未随改名更新 | bc719c17、usage_ledger/AGENTS.md、constants.py:118-122 | 中（新制造的文实冲突） |
| N6 | assistant-release-eval 规格仍描述 scripted 自测，实现已演进为 live run（eval_passed 不认 scripted）；任务全✅未归档 | spec assistant-eval:28-30 vs api.py:629-631 | 中（在途变更规格漂移） |
| N7 | 前端两条注释谎称 task-list 仍用 api/agents.ts（实际零引用） | ai-assistant/AGENTS.md:35、assistants.ts:1 | 低 |
| N8 | knowledge-assistant WS 残留还在活跃 spec 与 ARCH/PRD（归档 delta 未同步） | knowledge-assistant-voice/spec.md:10,14 等 | 中 |
| N9 | 删栏不清 _AGENTS/_CANCELS → 内存泄漏 | thread_run.py:37-38、views_drf.py:455-458 | 低（并入 A5） |
| N10 | A1×A2 耦合：恒假门禁意外挡住 goal 编造数据路径；只修 A1 会开闸 | api.py:668-675 + task_runner.py:439-452 | **高（排序约束）** |

---

## 六、建议执行顺序与立单

> 前提：与并发会话（fix-agentscope-usage-defects 实施者）协调，record.py/runner.py/models.py/usage_ledger/* 待其提交完成后再动。

1. **A2 fail-closed**（后端小修，先决策 a/b）——消除编造数据入库，为 A1 解锁。
2. **A1 门禁修复**（在 assistant-release-eval 内收口：共享 gate_ids_for(kind) + spec/tasks 修订 + 生产路径回归测试）。
3. **A5 取消复位**（独立小修 + 删栏清理 + 单测）。
4. **A4 账本修复**（变更申请：钱口径 + usage_ledger 红线 2；逐次 model 优先 + 键名修正 + 双模型单测）。
5. **D2 发布 UI + D3 revision**（assistant-release-eval 前端补完，依赖 A1）。
6. **D-DOC 文档批**（一个 docs 变更 + 一份红线变更申请，覆盖 B1-B6/C1-C5/S1-S5/D1/D5 文档/D7 口径）。
7. **D-TEST**（test_channels 重写 + 失效引用 + CI 执行门禁治理决策）。
8. **D4 枚举 SSOT + D5 收尾 + D6 类型**（纯重构小变更）。
9. **D8 保密口径**（需求方拍板后另立 spec 变更）。
10. A3 修复已在工作树落地（4.1/4.2/4.4），待 4.3 单测 + 提交过 CI 即收口，**不重复修**。

与原审计建议顺序（A1→A5→A3→B→D）的差异：**A2 提前到 A1 之前（N10 耦合）；A3 移出本批（在途）；A4 单列变更申请（钱口径硬约束）。**

---

## 七、需要决策

1. **A2 interim 方案选 a 还是 b？**（推荐 b：后端 fail-closed，不入库、明确失败原因。）以及：GoalPipeline/TeamPipeline 新路线是否正式推翻 D9「放弃」？接线何时立项？
2. **A4 变更申请是否批准？**（改什么：账本逐次 model 优先 + 键名修正 + usage_ledger 红线 2 三类厂商；为什么：双模型静默错账、与任务正文费用分叉；影响面：usage_ledger/api.py 一行 + 单测 + 一条红线文档；回退：还原该行即回旧行为。）
3. **D-DOC 红线变更申请是否批准打包提交？**（B1/B2/B3/B4/C1 根模板/C2 红线 9/C5 依赖边界/D7 口径，共 8 处规则条款；均为「把文档改成与现行代码/已归档决策一致」，无行为变化；回退=还原文档。）
4. **D8 保密口径走 (a) 维持还是 (b) 收紧？** 现状合规，收紧才需要改 spec。
5. **N2 治理：CI 是否加测试执行门禁？**（建议至少 arch+engines+ai_assistant unit；否则同类缺陷继续漏网。）
6. **原审计决策项 4「上一轮 PR 方案 5 个决策项」**：PLAN-agent-pr-flow.md 已被并发会话从工作树删除，该方案看起来已被 fix-agentscope-usage-defects（需求方已确认本批 4 项）取代——请确认是否就此关闭。

---

## 附：复核覆盖声明

- A1-A5：lead 逐行复核（含控制流、测试绕过路径、并发提交后状态复验）。
- B1-B6、S1-S5：子代理 doc-check 逐行复核，lead 抽验 B2/B4 关键行。
- C1-C5、D1-D3：子代理 asset-check 逐行复核（含全仓 grep 残留规模）。
- D4-D8：子代理 contract-check 逐行复核；lead 二次抽验 D8 规格依据（ai-role-registry:114）、D5 枚举现状（constants.py:118-122）、N3 失效测试、N2 CI 口径、A2 可达性（publish_workflow 空绑定跳过）。
- 未运行任何测试/lint/构建；未修改任何代码与规则文档。本报告是复核结论与方案，不是已实施的变更。