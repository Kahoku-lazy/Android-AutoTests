## 1. 列出全部命中

- [x] 1.1 设备控制在读取 xpath 文本时返回全部命中：每条含下标、文本和像素范围；`text` 取入参下标那一条，无命中或越界时 `text` 为空。引擎协议与 Android 引擎包装暴露同一能力。验证：`python -m pytest tests/graybox/unit/test_xpath_text_matches.py -q` 通过。
- [x] 1.2 执行模型工具、旧引擎设备工具和平台工具的 `xpath_action` `get_text` 都返回这份结果。`exists`、点击和长按不改。说明书与执行手册中的 `get_text` 返回约定写明 `count` 与 `items`。验证：`python -m ruff check engines/device/android/android_device.py engines/device/android/__init__.py engines/device/base.py engines/agents/tools/tool_device.py engines/ai/tools/tool_device.py engines/ai/tools/tool_device_catalog.py apps/ai_assistant/tools.py tests/graybox/unit/test_xpath_text_matches.py` 通过；`python -m pytest tests/graybox/unit/test_ai_log_evidence_wiring.py::test_xpath_read_actions_have_no_stamp_branch -q` 通过。
