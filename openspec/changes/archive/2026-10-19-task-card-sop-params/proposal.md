## Why

新建任务卡片现在是一张通用表单：任务标题 + 任务目标 + 文档 + YAML + 可选设备。平台实际执行的是 SOP，真正需要的参数是「哪份 YAML、哪台设备、跑哪条用例」，目标与文档并不参与执行。结果是用户填了不生效的字段，`case_title` 又完全缺失，无法只跑指定用例。

## What Changes

- **新建任务卡片改为 SOP 参数表单**：任务标题、智能体（单选、必选）、配置 YAML（单选）、设备（下拉、必选）、测试指定用例（下拉，空=全部）；**移除**任务目标与文档入口。
- **智能体必选**：未选智能体时提交按钮置灰；选项来自平台当前支持的流程（当前只有 Agent-01 / `sop`）。
- **测试指定用例**：选 YAML 后由前端 `js-yaml` 解析 `title` 列表，填充下拉；解析失败给出可读提示且不生成选项。
- **提交契约改为**：`title / agent_id / device_serial / case_title / config`；旧字段 `goal / documents / assistant_route` 不再由卡片提交。
- **后端新增 `AITask.case_title`**（空=全部），并在克隆重跑时复制。
- **开场说明改为固定模板**：`本次要操作的设备 serial 是：{serial}。每一步的设备动作都必须带上它。`，由设备 serial 生成，不再拼目标与文档。
- **引擎支持指定用例**：`run_platform_sop(..., case_title)` 只跑匹配标题的用例；空=全部；指定但不存在 → 可读失败，MUST NOT 静默跑全部。
- **BREAKING**：旧客户端即使仍提交 `goal` / `documents`，也不再进入执行开场；字段保留入库只为兼容历史任务。

## 关联文档

无新增需求编号：本次是任务卡片字段与执行参数对齐，`dev_docs` 本次不动；验收口径以本变更 specs 为准。

## Capabilities

### New Capabilities

- `task-card-sop-form`: 新建任务弹窗的字段与交互——智能体单选必选、SOP 参数组、YAML 标题前端解析、提交载荷与提交置灰规则。

### Modified Capabilities

- `ai-task-publishing`: 任务提交字段与附件口径（只保留 YAML）、智能体选择的提交方式、`case_title` 落库。
- `sop-task-run`: 开场说明改为设备序列号固定模板；指定用例时只跑该用例，空时按文件顺序跑全部。

## Impact

- 后端：`apps/ai_assistant/models.py`（`AITask.case_title` + 迁移）、`serializers.py`、`views_drf.py`（提交入口）、`api.py`（`create_task` / `rerun_task` / 新的 `build_sop_run_input`）、`task_runner.py`、`engines/agents/workflow/platform_run.py`。
- 前端：`package.json`（`js-yaml` + 类型）、`composables/useTaskPublish.ts`、`components/TaskBoard.vue`、新增 `helpers/yaml-case-titles.ts`、`api/tasks.ts`（载荷说明）。
- 测试：前端新增 YAML 标题解析与表单校验用例；后端新增两种提交与 `case_title` 过滤用例。
- 不改：SOP 的步骤/重试/验收语义、工具装配、任务列表卡片既有字段。
