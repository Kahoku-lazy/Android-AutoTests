## 1. 时间点只到秒

- [x] 1.1 查询时间点与 `check_device_log` 的起点接受 `YYYY-MM-DD HH:MM:SS` 和 `HH:MM:SS`，只到秒按该秒的 `.000`。验证：`python -m pytest tests/graybox/unit/test_device_log_read_tool.py::test_parse_log_at_without_milliseconds tests/graybox/unit/test_device_log_check_tool.py::test_second_precision_start_still_hits -q`

## 2. 验收提示词

- [x] 2.1 验收系统提示词写明 UI 断言不要查日志，只有结果明确要求核对设备日志时才调用检查工具。验证：`python -m pytest tests/graybox/unit/test_device_log_check_tool.py::test_verifier_prompt_carries_keyword_catalog -q`

## 3. 上下文只留最近 3 步截图

- [x] 3.1 新的一次执行开始前裁剪两个角色的上下文：含当前步只留最近 3 步截图，更早步骤收成文字结论；重试算同一步；挂起恢复和验收半程不裁。验证：`python -m pytest tests/graybox/unit/test_sop_context_trim.py tests/graybox/unit/test_sop_steps.py tests/graybox/unit/test_sop_log_empty_abort.py -q`
