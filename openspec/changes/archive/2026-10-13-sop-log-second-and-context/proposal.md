## Why

验收查日志时，执行者交出的点击时间有时只到秒。工具只认带毫秒的时间点，这些调用直接失败。同时，只看页面的步骤仍去查日志，整场运行的历史截图又一直留在上下文里。

## What Changes

- 日志查询与 `check_device_log` 的起点接受只到秒的北京时间。只到秒等价于该秒的 `.000`，查找窗口口径不变。
- 验收提示词写明：UI 断言不要查日志；只有这一步必须达成的结果明确要求核对设备日志时才调用 `check_device_log`。
- SOP 在新的一次执行开始前裁剪执行角色与验收角色的上下文：含当前步只留最近 3 步截图，更早步骤收成文字结论。同一步重试仍算同一步。挂起恢复和验收半程不裁。

## 关联文档

无关联 PRD。这是一次已落地的 SOP 验收修正：时间点契约、验收查日志的时机、步骤间截图保留。

## Capabilities

### New Capabilities

### Modified Capabilities

- `device-log-read-tool`: 时间点只到秒时按该秒的 `.000` 解析；验收提示词规定 UI 断言不要查日志。
- `agent-sop-workflow`: 新的一次执行开始前，上下文只保留最近 3 步截图，更早步骤收成文字结论。

## Impact

- `engines/agents/tools/tool_serial.py`：时间点格式。
- `engines/agents/prompts/verifier_prompt.py`：验收提示词与关键词表导语。
- `engines/agents/workflow/steps.py`、`engines/agents/workflow/context_trim.py`：步骤开始前裁剪上下文。
- 测试：`tests/graybox/unit/test_device_log_read_tool.py`、`tests/graybox/unit/test_device_log_check_tool.py`、`tests/graybox/unit/test_sop_context_trim.py`。不跑全量回归。
