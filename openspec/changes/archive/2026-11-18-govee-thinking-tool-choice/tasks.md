## 1. govee 重发

- [x] 1.1 在 `engines/ae_harness/agents/models.py` 的 govee 分支包一层模型：只认 `Thinking mode does not support this tool_choice`，流开始后不重发，其它错误原样抛出。验证：`python -m pytest -c tests/pytest.ini tests/engines/ae_harness/unit/test_govee_tool_choice.py -q` 中「普通 400 不重发」通过。
- [x] 1.2 没强制工具的请求不重发。强制设备工具只关思考并保持工具名。`tool_choice=none` 只关思考并保持禁止调用。验证：同一测试文件这三支都断言第二次请求的 `tool_choice` 与工具列表。
- [x] 1.3 强制 `GenerateStructuredOutput` 时，先关思考并保持强制；仍是同一句 400，就把工具列表收成只有该工具并改为 `auto`。验证：同一测试文件断言第三次请求没有设备工具。
- [x] 1.4 deepseek 与 dashscope 的 `create_model` 不套这层。验证：同一测试文件断言这两个通道的模型类不变。

## 2. 校验

- [x] 2.1 `openspec validate govee-thinking-tool-choice --type change --strict`。验证：命令退出码为 0。
