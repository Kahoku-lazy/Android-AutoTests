## 1. 平台 SOP 角色装配

- [x] 1.1 新增 `engines/backend_bridge/workflow/__init__.py`（11 字段 docstring，`类型` 取 `Agent 能力模块`）。验证：`python -c "import engines.backend_bridge.workflow"` 成功；docstring 0 error
- [x] 1.2 新增 `workflow/roles.py`：`build_sop_roles()` 建执行者（全量工具）与验收者（只读工具），共用一个观测中间件。验证：单测断言验收者工具集只含只读工具
- [x] 1.3 两个角色都经 `ae_harness.agents.create_agent` 创建、复用 `UI_EXECUTOR_PROMPT` / `UI_VERIFIER_PROMPT`。验证：导入守卫 + 单测

## 2. 一次运行

- [x] 2.1 新增 `workflow/sop_ui.py` 的 `SopRunResult`：`phase`、`steps`、`report_path`、`log_path`、`model`、`tokens`、`by_api_key_env`、`usages`、`cost_s`。验证：单测断言字段齐全
- [x] 2.2 `run_sop_once(task, *, spec_key="ui_task", report_root=None)`：选流程 → 覆盖 `spec.task` → 调 `run_sop(log_dir=REPORT_ROOT, role="sop_ui", role_api_keys=…)` → 整理结果；不打印、不读 argv。验证：单测 + 真机
- [x] 2.3 每次调用新建角色，不缓存。验证：单测断言连续两次调用拿到不同角色实例
- [x] 2.4 报告落在 `logs/agents/backend_bridge/<时间戳>/`，文件名带 `sop_ui`。验证：真机产物

## 3. 触发入口

- [x] 3.1 新增 `backend/apps/ai_assistant/management/commands/run_ui_sop.py`：`run_ui_sop "<任务>" [--spec] [--execution-id]`，跑完打印每步通过与 token，并把用量交 `record_run_usages`。验证：真机跑通，账本新增行
- [x] 3.2 命令与 `run_ui_agent` 互不影响。验证：两个命令先后跑，产物与账本各自独立

## 4. 边界与回归

- [x] 4.1 确认 `engines/ae_harness/` 零代码改动。验证：`git status` 中该目录只有既有 WIP，没有本变更的代码改动
- [x] 4.2 确认对话页行为不变：`GET /api/ai/workflows/` 仍只有 `platform_ui`。验证：接口调用
- [x] 4.3 导入守卫：本目录不得 import `ae_harness.assistant` / `ae_harness.workflow.sop_runner` / `django` / `apps`。验证：单测扫描

## 5. 测试与门禁

- [x] 5.1 `python -m pytest -c tests/pytest.ini tests/engines/backend_bridge -q` 全绿
- [x] 5.2 docstring / ruff 全过（`engines/backend_bridge`）
- [x] 5.3 真机：跑一次 SOP → 每步有通过结论 → 报告落盘 → 面板/报告可查 → 账本新增行
- [x] 5.4 `python run.py check` 与基线对比无新增失败
