## Why

上一 change 修复了"run 不存在"链路后，真实执行暴露出两个新问题：① **设备没有响应用例**——`_do_start_app`（`executors/ui/executor.py:226`）把步骤的 `xpath` 当作启动包名，而 v6.10 写侧校验强制 `adb_start_app` 的 xpath 非空，AI 被迫写 `xpath="/"` → 执行器用 `"/"` 启动应用（无效）→ 应用从未进入前台 → 第 3 步等待 Tab 超时失败（16:36/16:37 两次真实运行均 fail，设备停在 launcher；原版 TC-NAV-001 xpath 为空反而能回退到用例包名正常启动）。② **AI 查询频率太高**——AI 无任何等待工具（其思考中明言"我没有 sleep 工具"），只能密集轮询 `get_run_status`，并自行重复执行用例两次以"确认复现"。

## What Changes

1. **P0** `apps/case_manager/api_ai.py`：从 `_REQUIRED_FIELDS` 移除 `adb_start_app`/`adb_kill_app` 的 xpath 必填约束——与执行器语义对齐（xpath 即包名、可为空并回退用例 `package_name`），消除"校验逼 AI 伪造值"的根因。
2. **P0** 数据修正：TC-NAV-004 第 1 步 xpath 由 `"/"` 改为空串（经 `save_ai_definition` 合法落库），使启动回退到 `com.govee.home`。
3. **P1** `apps/ai_assistant/agent_scope/tool_registry.py`：新增 `sleep` 平台工具（等待 1-30 秒，read_only，归入「测试执行」分类），供 AI 在轮询前主动等待；`get_run_status` 描述补"建议用 sleep 间隔 5-10 秒查询、执行通常需 30-60 秒"。

无 **BREAKING** 变更。

## 关联文档

- `dev_docs/02-PRD需求/PRD-06-执行引擎.md`（adb_start_app 步骤语义）、`PRD-08-AI助手.md` §4.1（26 平台工具）
- `apps/test_runner/AGENTS.md`（执行器拆分、步骤类型对齐）
- `apps/case_manager/AGENTS.md`（写侧校验口径，v6.10）
- 现场证据：`ai_messages` 对话 211（msg 407，AI 自述"设备停留在 launcher"）、`tr_test_runs` 三次真实运行均 fail、`executor.py:224-235`、`api_ai.py:49-50`

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无）

> 纯 Bug 修复 + 工具补充：校验口径与执行器语义对齐、AI 等待能力补充，无需求级行为变化，`.openspec.yaml` 已设 `skip_specs: true`。

## Impact

- 后端：`apps/case_manager/api_ai.py`（删 2 条约束）、`apps/ai_assistant/agent_scope/tool_registry.py`（+~20 行 sleep 工具 + 描述）
- 数据：`cm_test_definitions` 中 TC-NAV-004 第 1 步 xpath 置空
- 测试范围：`manage.py check` + `ruff` + `--check-boundaries`；`validate_steps` 空 xpath 校验；sleep 工具 resolve 验证；真实设备重跑 TC-NAV-004 期望 **pass**
