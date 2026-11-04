## Why

TASK-184（结构化步骤测试-定时功能测试-02）跑完 645s，界面只显示「模型 43s + 8s」，其余 75s 看不见：全案 32 个设备动作产生了 136 次工具调用 + 134 次模型调用，每次往返 4.5s；其中 `mark_dot` 49 次 66.3s（22 次是打完点又重打），`check_device_log` 3 次 44.1s（每次把 8.5MB / 82k 行日志整份重解析），另有 83.8s 纯空档。

结论是两类可消除的浪费：**同一次点击被拆成 4 趟往返、同一帧被截两次**；**日志每次全量重解析**。再加上详情页只有模型耗时，读者无法分辨「慢在推理」还是「慢在工具」。

## What Changes

- **坐标核对帧可复用**：`mark_dot` 在返回标记图的同时返回该帧的 `token` 与已算好的像素坐标；`click_ratio` / `tap_screen` 新增可选 `token`，命中时**直接用该帧算坐标、不再重新截图**。帧缓存放在工具模块进程内（键 `(serial, token)`，TTL 90s，每设备最多 2 帧）；`token` 过期或不匹配 MUST 返回可读 error 并要求重新核对，MUST NOT 静默改用新帧。
- **点击后直接回图**：点击类工具 MUST 回传点击后的页面图（`after`）与 `action_time`；执行模型据此判断下一步，MUST NOT 再单独调一次 `screenshot_page` 验证。
- **执行提示词改写坐标纪律**：确认红点后 MUST 用同一帧点击；点击前后的重复截图 MUST NOT 发生；`xpath_action` 返回的像素坐标同样走 `token`，不再「先截图再对点」。
- **日志检查改增量尾读**：`check_device_log` 按 `(size, mtime)` 复用已解析行、只解析新增部分；结果 MUST 与全量解析完全一致；文件被截断或轮转时 MUST 回退全量解析。当前日志 8.5MB / 82k 行，单次全量解析 1.56s，运行中实测 8.7–20.7s。
- **报告给出工具与空档耗时**：`GET /api/tasks/{id}/report/` 的 `cases[].steps[]` 增加 `tool_ms` 与 `idle_ms`（`idle_ms = duration_ms - model_ms - tool_ms`，不为负）；前端步骤行除「模型」徽标外展示「工具」「空档」，让「2m06s vs 模型 43s」的差额可读。
- **验收口径**：同一份结构化定时用例重跑，墙钟 MUST 明显低于变更前 645s；`mark_dot` 与 `screenshot_page` 的调用次数 MUST 下降；日志检查单次 MUST < 1s。

## 关联文档

无 PRD 需求编号。触发于 2026-11-04 对 TASK-184 的耗时分析（`dev_docs/DEV_TEST/分析-结构化任务184耗时构成-20261104.md`）：模型 343s / 工具 172s / 空档 84s / 装配 44s。约束来源为根 `AGENTS.md`「一次提交只做一件事」与 `engines/agents/AGENTS.md`「工具经 `tools_config.py` 分配」。

## Capabilities

### New Capabilities

（无：本次不新增产品能力，只压缩既有工具的往返次数并补齐耗时展示。）

### Modified Capabilities

- `ai-screen-vision`: 「坐标核对工具」增加帧标识与像素坐标返回，并允许点击类工具在有效期内复用该帧。
- `ai-device-action`: 「设备动作记录并回传发出时间」增加点击类工具接受坐标核对帧标识、以及回传点击后页面图的约束。
- `role-prompt-guardrails`: 执行提示词的坐标纪律改为「确认后用同一帧点击、点击前后不重复截图」。
- `device-log-read-tool`: 新增「重复查询复用增量解析且结果与全量一致」的要求。
- `agent-task-flow-report`: 步骤行耗时增加 `tool_ms` 与 `idle_ms`，并在页面展示工具与空档耗时。

## Impact

- 修改：`engines/agents/tools/tool_img_b64.py`（`mark_dot` 返回值）、`engines/agents/tools/tool_device.py`（`click_ratio` / `tap_screen` 的 `token` 与 `after`）、`engines/agents/tools/tool_serial.py`（增量解析）、`engines/agents/config/data/prompts/UI_EXECUTOR_PROMPT.md`（第 2、5 条）、`backend/apps/task_list/task_reports.py`（步骤耗时三项）、`frontend/src/modules/task-list/**`（步骤行徽标）。
- 新增：`engines/agents/tools/_frame_cache.py`（进程内帧缓存，供两个工具模块共用）。
- 不改：`tools_config.py` 的工具名与分组（常驻组仍为 `screenshot_page` / `mark_dot` / `press_key`）、报告接口字段名与既有 `model_ms` / `duration_ms` 语义、数据库表结构。
- 测试：`tests/engines/agents/test_tool_img_b64.py`、`test_tool_device.py`、`test_tool_serial.py`（新增增量解析与 token 语义）、`tests/api/test_task_report*.py`、`frontend` 的 `report-steps` 相关单测。
- 行为：日志检查结果、坐标核对与点击的对外语义不变；唯一可见差异是工具多返回字段、详情页多两列耗时。
