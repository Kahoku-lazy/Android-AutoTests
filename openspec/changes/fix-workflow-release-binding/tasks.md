## 1. 快照补齐运行身份

- [x] 1.1 `backend/apps/ai_assistant/api.py` 的 `_release_payload_for_assistant(card)` 增加三个字段：`assistant_id`（`card.assistant_id`）、`run_name`（`card.display_name`）、`base_url`（模型配置的 `base_url`，空则 `""`），其余字段与查询次数不变。验证：`.venv\Scripts\python.exe manage.py check`；`ruff check backend/apps/ai_assistant/api.py`。**验证结果**：`manage.py check` 0 issues；`ruff check` All checks passed；`ruff format --check backend tests` 296 files already formatted。

- [x] 1.2 `backend/apps/ai_assistant/services/sop_workflows.py` 抽出 `align_run_names(executor: dict, verifier: dict) -> None`：两侧 `run_name` 相同时把验收侧改成 `f"{run_name}-{assistant_id}"`；`resolve_workflow()` 改用该函数（行为不变）。验证：`.venv\Scripts\python.exe -m pytest -c tests/pytest.ini tests/ai_assistant/api -q` 全绿。**验证结果**：新增用例 `test_same_display_name_keeps_snapshot_and_live_names_aligned` 通过——快照与实时解析给出同一运行名（`同名名片` / `同名名片-verif-card`）。

- [x] 1.3 `publish_workflow()` 在写入版本前对两侧 payload 调用 `align_run_names`，让快照与实时解析同名口径一致。验证：同 1.2 的 pytest 命令。**验证结果**：`test_published_workflow_task_resolves_run_binding` 断言快照两侧含 `assistant_id`、`run_name`、`base_url` 且取值等于发布当刻的名片与模型配置。

## 2. 历史版本一次性补齐

- [x] 2.1 新增迁移 `backend/apps/ai_assistant/migrations/0089_backfill_workflow_release_binding.py`：遍历 `AssistantRelease(target_kind='workflow')`，按工作流的 `executor_assistant_id` / `verifier_assistant_id` 找名片与模型配置，`setdefault` 补 `assistant_id`、`run_name`、`base_url`，对两侧同名套用 1.2 的后缀规则；只对发生变化的行 `save(update_fields=["payload"])`；名片或配置缺失时跳过该侧。验证：`makemigrations --check` 无待生成迁移、`manage.py migrate` 成功且二次执行无写入。**验证结果**：`makemigrations --check` → No changes detected；`migrate` → `Applying ai_assistant.0089_backfill_workflow_release_binding... OK`；补齐函数二次调用后 payload 逐字不变（`test_legacy_release_payload_is_backfilled_for_run` 断言两次结果相等）。

- [x] 2.2 在本机库上应用迁移并核对：工作流 9 的 v1 版本 payload 两侧都含 `assistant_id` 与 `run_name`，提示词/模型/工具字段与迁移前逐字一致（迁移前先 `dump` 一份到 `temps/` 比对）。验证：`.venv\Scripts\python.exe manage.py migrate` 后打印两侧 keys 与提示词哈希比对结果。**验证结果**：迁移前快照存 `temps/pre_release_payload.json`；迁移后两份 payload 的 `system_prompt`、`tools`、`model_name`、`provider`、`role_id`、`api_key_env`、`model_config_id` 逐字段相等（`True`×7），新增 `assistant_id=20261116_8PD/20261124_2FM`、`base_url=https://api.deepseek.com`。

## 3. 功能级回归用例

- [x] 3.1 新增 `tests/ai_assistant/api/test_workflow_release_binding.py`：作者发布工作流 → 通过 `TaskSubmitAPIView` 提交一份合法里程碑 → 用 `_resolve_assistant_sop(task)` 解析该版本 → `_binding()` 对两侧都不抛，`run_name` 等于发布时显示名，`assistant_id` 与名片一致，`base_url` 与模型配置一致；用例末尾 ORM 读回 `task.release_version` 与版本 payload。验证：`.venv\Scripts\python.exe -m pytest -c tests/pytest.ini tests/ai_assistant/api/test_workflow_release_binding.py -q`。**验证结果**：3 passed；与既有 `test_release.py` 合并跑 9 passed。

- [x] 3.2 同文件补一条补齐用例：手工写入一条「旧口径」版本 payload（只有 role_id/prompt/model 等），调用迁移模块的补齐函数（`importlib` 按模块名导入，`apps` 用 `django.apps.apps`），断言补出 `assistant_id`/`run_name` 且原提示词与工具不变；再执行一次断言 payload 不再变化。验证：同 3.1。**验证结果**：`test_legacy_release_payload_is_backfilled_for_run` 通过；补齐后 `resolve_sop_release(workflow.id, 1)` 两侧都能构造 `RoleBinding`。

## 4. 门禁与真机复验

- [x] 4.1 本地门禁 `.venv\Scripts\python.exe -m run check` 退出码 0；`python utils/gen_arch_stats.py --check-boundaries` 退出码 0。**验证结果**：阻塞项 28/30 通过；`boundary`、`linting` 均 PASS。剩余 2 项失败与本变更无关（`frontend/src/modules/ai-assistant/eval-cases.vue`、`evals.vue` 的 prettier 与 >500 行，属 `refine-eval-pages-ui` 在途改动）。

- [x] 4.2 后端重启后，在本机复验解析链路：`resolve_sop_release(9, 1)` 的两侧都能构造出 `RoleBinding`（打印 `run_name`）。验证：脚本输出两侧 `run_name` 与 `assistant_id`。**验证结果**：任务 248/249 的 `_resolve_assistant_sop` 均解析成功——执行侧 `Android-UI-执行 / deepseek-flash / https://api.deepseek.com`，验收侧 `Android-UI-验收`，YAML 正文 134B 可读。

- [ ] 4.3 人工确认端到端：在任务清单点任务 249 的「重跑」，确认新任务不再 0 秒失败，且能进入「平台编译 / 第一步执行」；把结果记入 tasks 勾选说明（真机执行耗时较长，允许只确认到首步启动）。**待验**：后端已重启、快照已补齐；等待点重跑确认。
