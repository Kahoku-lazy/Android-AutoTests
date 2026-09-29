## MODIFIED Requirements

### Requirement: TaskRequest 契约

Django SHALL 通过 `TaskRequest` 传入规划用户输入（字段名仍为 `goal`）、三角色模型配置（planner/executor/verifier，api_key 已解密）、工具清单（`tools`）、`max_loops`、`device_serial`/`user_id`/`task_id`/`media_root`/`skill_dirs`，以及设备日志证据提供者（`log_evidence`，可空）。规划用户输入 MUST 为无 Markdown 代码块包裹的 JSON 字符串，键固定为：`任务标题`、`任务目标`、`附件文本内容`、`设备ID`；值为字符串，无附件时 `附件文本内容` 为空字符串，`设备ID` 为已解析的设备 serial。日志证据提供者 MUST 以只含标准库类型的协议对象（开窗 / 读窗两个方法）注入，与 `on_progress` 同构；引擎 MUST NOT 为此直接 import `engines.device` 或 `apps.*`。

#### Scenario: 组装请求

- **WHEN** 前端提交任务（`POST /api/ai/tasks/submit`）且任务已落库
- **THEN** `engine_adapter` 从 `AITask` 与 `route_configs`（解密后）组装 `TaskRequest`，模型 api_key 以明文传入引擎，且 `TaskRequest.goal` 为上述四键 JSON

#### Scenario: 规划模型收到结构化任务 JSON

- **WHEN** 引擎启动规划阶段
- **THEN** 规划模型收到的用户输入包含任务标题、任务目标、附件 Markdown（可空）与设备 serial，而不是仅有目标一句自然语言

#### Scenario: 注入日志证据提供者

- **WHEN** 组装 device_control 任务的 `TaskRequest`
- **THEN** `log_evidence` 由 Django 侧注入并实现开窗与读窗两个协议方法，引擎只经协议调用，不直接触碰串口或 TCP 句柄

#### Scenario: 未注入日志证据提供者

- **WHEN** 未配置设备日志采集，`log_evidence` 为空
- **THEN** 引擎仍能完成执行，验收阶段标注「无日志证据」，MUST NOT 因缺少日志证据而中断任务
