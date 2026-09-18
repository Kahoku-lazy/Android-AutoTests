## MODIFIED Requirements

### Requirement: TaskRequest 契约
Django SHALL 通过 `TaskRequest` 传入规划用户输入（字段名仍为 `goal`）、三角色模型配置（planner/executor/verifier，api_key 已解密）、工具清单（`tools`）、`max_loops` 及 `device_serial`/`user_id`/`task_id`/`media_root`/`skill_dirs`。规划用户输入 MUST 为无 Markdown 代码块包裹的 JSON 字符串，键固定为：`任务标题`、`任务目标`、`附件文本内容`、`设备ID`；值为字符串，无附件时 `附件文本内容` 为空字符串，`设备ID` 为已解析的设备 serial。

#### Scenario: 组装请求
- **WHEN** 前端提交任务（`POST /api/ai/tasks/submit`）且任务已落库
- **THEN** `engine_adapter` 从 `AITask` 与 `route_configs`（解密后）组装 `TaskRequest`，模型 api_key 以明文传入引擎，且 `TaskRequest.goal` 为上述四键 JSON

#### Scenario: 规划模型收到结构化任务 JSON
- **WHEN** 引擎启动规划阶段
- **THEN** 规划模型收到的用户输入包含任务标题、任务目标、附件 Markdown（可空）与设备 serial，而不是仅有目标一句自然语言
