## 1. 格式化

- [x] 1.1 在 `engines/ae_harness/agents/models.py` 增加 govee 专用格式化器：继承 `OpenAIChatFormatter`，删除 `system` 与 `assistant` 消息的 `name` 键，保留 `user` 与 `tool`。验证：单测构造四类消息，断言键是否存在，且不发网络请求。
- [x] 1.2 `create_model` 的 govee 分支把该格式化器传给 `OpenAIChatModel`。deepseek 与 dashscope 分支不改。验证：源码检索确认只有 govee 分支传入新格式化器。

## 2. 回归

- [x] 2.1 运行 `python -m pytest -c tests/pytest.ini tests/engines/ae_harness/unit/test_creator.py tests/engines/ae_harness/unit/test_govee_message_name.py -q`。验证：全部通过。
