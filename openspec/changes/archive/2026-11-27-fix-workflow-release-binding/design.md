## Context

任务提交时若工作流已有发布版本，`task_list/views.py` 会把 `release_version` 记进任务；执行端 `task_runner._resolve_assistant_sop()` 因此走 `ai_assistant.api.resolve_sop_release()` → `_resolved_from_release()`，拿到的是快照里的 `payload["executor"]` / `payload["verifier"]`。而 `_binding(side)`（`task_runner.py:176`）硬取 `run_name`、`system_prompt`、`provider`、`api_key_env`、`model_name`；`used` 还取 `assistant_id`。

快照由 `publish_workflow()` 用 `_release_payload_for_assistant(card)` 组装，当前只存 `role_id / system_prompt / tools / model_config_id / model_name / provider / api_key_env`，缺 `assistant_id`、`run_name`、`base_url`。结果是：未发布时 `resolve_workflow()` 走实时侧（`_resolve_side()` 有 `run_name`）能跑；一发布就换成快照，必崩。

同名后缀规则目前只存在于实时解析（`services/sop_workflows.py:174-175`）：两侧显示名相同时给验收侧加助手标识后缀，用于报告目录与用量归属命名。快照侧必须同口径，否则同名名片下执行与验收会撞名。

既有规格（`assistant-release`「使用方读取冻结版本」）要求开跑与重跑只读版本、不读名片当前内容，因此旧版本修复不能做在解析器里。

## Goals / Non-Goals

**Goals:**

- 发布快照包含执行端与评测端消费的全部字段，发布后的任务不再因缺字段失败。
- 两侧同名时快照与实时解析给出同一套运行名。
- 库里已有的工作流版本一次性补齐，引用它们的历史任务（含 248/249 的重跑）恢复可执行。
- 用功能级灰盒用例守住「发布 → 提交 → 能解析出绑定」这条链。

**Non-Goals:**

- 不改 `task_runner.py`（不在执行端加兜底默认值）：字段齐了就不需要，加兜底会掩盖下一次快照缺字段。
- 不改 `engines/backend_bridge`（`RoleBinding` 契约不变）。
- 不重发工作流新版本；不强制用户重新发布。
- 不改发布接口的请求/响应形状，不改 `POST /api/tasks/submit/`。

## Decisions

1. **把 `assistant_id`、`run_name`、`base_url` 加进 `_release_payload_for_assistant()`。** 该函数已经在查 `AIRole` 与 `AIModelConfig`，多返回三个字段零额外查询；发布助手与发布工作流共用它，助手快照多存身份字段对消费方无影响（消费方按 key 取值）。
   备选（否）：在 `publish_workflow()` 里另写一份组装——两份 payload 会各自漂移，本次故障就是这类漂移。
2. **同名后缀规则提取为共享函数 `align_run_names(executor, verifier)`**，放在 `services/sop_workflows.py`，由 `resolve_workflow()`（实时）与 `publish_workflow()`（快照）共同调用。规则：`executor["run_name"] == verifier["run_name"]` 时把验收侧改成 `f"{run_name}-{assistant_id}"`。
3. **旧版本用一次性数据迁移修复，不做运行时回填。** 迁移 `0089_backfill_workflow_release_binding.py` 遍历 `target_kind='workflow'` 的版本，按 `AISopWorkflow.executor_assistant_id / verifier_assistant_id` 找名片与模型配置，`setdefault` 写 `assistant_id` / `run_name` / `base_url`，并按规则 2 处理同名。
   理由：既有规格要求「开跑与重跑 MUST 读取该版本，MUST NOT 再读取名片的当前内容」；运行时回填每次开跑都读当前名片，直接违反该条。迁移只在升级瞬间读一次，运行时不读。
   备选（否）：让用户「改一版再发」生成 v2——248/249 仍钉在 v1 上，重跑照样失败；且发布态工作流改版流程本身不顺畅。
4. **迁移只补缺、不覆盖、缺名片时跳过。** 用 `setdefault` 语义；找不到名片或模型配置时保留原 payload 继续处理下一条，MUST NOT 让升级因单条脏数据失败。迁移反向操作留空（无 `reverse_code`）。
5. **回归用例写成功能级灰盒**（`tests/ai_assistant/api/test_workflow_release_binding.py`）：按 `tests/AGENTS.md` 口径不新增单元测试，一条用例走「发布 → 提交任务 → 解析该版本 → 构造绑定」，末尾用 ORM 读回任务版本号与版本 payload。

## 模块防火墙自检

- 跨 App import：`ai_assistant` 内部（`api.py` ↔ `services/sop_workflows.py`）；测试侧读 `task_list` 的 `task_runner` 私有函数，属 `tests/` 灰盒，不改后端依赖方向。
- 写库路径：快照写入仍走 `_next_release()` / `AssistantRelease.save()`；迁移在迁移上下文内直接写模型，属数据迁移，不进入业务写路径。
- 未新增自定义异常类；未改 `engines/`；未改前端；未新增表/字段（只改 JSON payload 内容）。
- 依赖方向未放宽：`backend/` → `engines/` 单向不变，`device/` 等底座未触及。

## Risks / Trade-offs

- [迁移改写历史版本 payload，可能影响「不可变版本」的直觉] → 只补缺失的身份字段，提示词/模型/工具/编排逐字不变；规格里把这次补齐写成显式的一次性要求。
- [名片或模型配置已被删除，补不出字段] → 跳过并保留原样；该版本仍不可跑，属数据已损，纳入 tasks 的验证说明（记录数量）。
- [同名后缀规则改动会影响报告目录与用量归属命名] → 与实时解析对齐是本就要的修复；后缀只加在验收侧，执行侧命名不变。
- [助手快照也多了三个字段] → 消费方按 key 取，无破坏；如后续不想要，可再拆专用组装函数（非本次范围）。
