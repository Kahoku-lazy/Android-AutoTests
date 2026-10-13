## 1. 按传入关键词原文检查

- [x] 1.1 `check_device_log` 按 `keyword` 原文在型号日志里查找（忽略大小写），不再把功能点中文换成表内关键词。窗口、型号文件和「无日志则中断」保持不变。验证：`python -m pytest tests/graybox/unit/test_device_log_check_tool.py -q` 中「关闭设备成功」对只有 `switch_off` 的日志返回 `FAIL`，`switch_off` 仍返回 `PASS`。

## 2. 关键词表进入验收上下文

- [x] 2.1 验收角色默认系统提示词末尾附上关键词数据文件中的「关键词 → 功能点」，并要求模型选出关键词后原样传入。文件没有词条时不附空表。执行手册中验收查日志的说法与此一致。验证：`python -m pytest tests/graybox/unit/test_device_log_check_tool.py::test_verifier_prompt_carries_keyword_catalog tests/graybox/unit/test_sop_steps.py -q` 通过；`python -m ruff check engines/agents/tools/tool_serial.py engines/agents/prompts/verifier_prompt.py engines/agents/role/executor.py tests/graybox/unit/test_device_log_check_tool.py` 通过。
