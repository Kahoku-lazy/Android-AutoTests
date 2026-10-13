## Why

验收模型把功能点中文交给 `check_device_log` 后，工具再按关键词表换成日志原文。模型看不到表，也决定不了该查哪一个词；换算一旦对错，查到的就不是这一步要证明的日志。

## What Changes

- **BREAKING**：`check_device_log` 的 `keyword` 按调用方传入的字符串在日志行里查找（忽略大小写），不再把功能点中文换成表内关键词。
- 验收角色的系统提示词附上 `config/device_log_keywords.json` 的「关键词 → 功能点」对照。模型根据这一步要达成的结果自己选出关键词，原样传入。
- 日志文件、5 秒窗口、`PASS` / `FAIL` 与「窗口内无日志则中断」保持不变。

## 关联文档

无关联 PRD。这是验收侧日志断言的关键词来源调整：表给模型看，工具只查传入的原文。

## Capabilities

### New Capabilities

### Modified Capabilities

- `device-log-read-tool`: 规则检查按传入关键词原文查找；验收上下文附上当前关键词表，由模型自己选择要查的词。

## Impact

- `engines/agents/tools/tool_serial.py`：去掉功能点到关键词的换算。
- `engines/agents/prompts/verifier_prompt.py`、`engines/agents/role/executor.py`：系统提示词附上关键词表。
- 执行手册中验收查日志的说法。
- 测试：`tests/graybox/unit/test_device_log_check_tool.py`。不跑全量回归。
