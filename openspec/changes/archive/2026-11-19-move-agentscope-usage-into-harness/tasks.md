## 1. 原语

- [x] 1.1 新增 `engines/ae_harness/agents/messages.py` 的 `user_message(content)`，返回 `name="user"` 的用户消息。验证：`tests/engines/ae_harness/unit` 断言名字与正文。
- [x] 1.2 新增 `engines/ae_harness/tools/scripted.py` 的 `scripted_tool(name, input_schema, respond)`，调用时执行 `respond` 并返回一个文本块。验证：单测断言工具名、入参形状与返回正文。

## 2. 调用点

- [x] 2.1 `backend_bridge/session.py` 改为调用 `user_message`，删除 `agentscope` 导入。验证：`tests/engines/backend_bridge/unit/test_session.py` 通过。
- [x] 2.2 `backend_bridge/workflow/fake_world.py` 改为调用 `scripted_tool`，删除 `agentscope` 导入，保留按勾选复制与记账。验证：`tests/engines/backend_bridge/unit/test_fake_world.py` 通过。

## 3. 守卫与规则

- [x] 3.1 `test_import_guard.py` 把 `agentscope` 从允许清单移到禁止前缀。验证：该测试通过，且 `grep -n "import agentscope" engines/backend_bridge` 无输出。
- [x] 3.2 更新 `ae_harness/AGENTS.md` 与 `backend_bridge/AGENTS.md`，只补 design.md 决策 4 点名的两句。验证：`git diff` 中这两份文件没有决策 4 之外的条款改动。
