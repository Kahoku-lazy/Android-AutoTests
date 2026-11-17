## 1. 助手名片入库

- [x] 1.1 在 `backend/apps/ai_assistant` 新增 `AIAssistant`（`assistant_id` / `display_name` / `avatar` / `marker` / `role_id` / `tools`）与迁移，`assistant_id` 唯一。验证：`python manage.py makemigrations --check` 无待生成变更，`python manage.py check` 通过。
- [x] 1.2 新增助手编号生成：当地日期 + `_` + 3 位 `[0-9A-Z]`，查重，耗尽抛可读错误。验证：`python -m pytest -c tests/pytest.ini tests/ai_assistant/unit/test_assistant_id.py -q` 覆盖格式、不重复、与 `role_id` 字符集不同。
- [x] 1.3 在 `api.py` 实现创建、更新、删除、列表。创建校验 `role_id` 存在且不复制提示词；写库只经 `api.py`。验证：`python -m pytest -c tests/pytest.ini tests/ai_assistant/unit/test_assistant_cards.py -q`。
- [x] 1.4 头像在 `api.py` 压成最长边 128 的 JPEG，base64 不超过 12KB；列表只返回 `has_avatar`。验证：同一测试文件断言超限拒绝、列表响应无 `avatar` 键。
- [x] 1.5 暴露 `GET/POST /api/ai/assistants/`、`PATCH/DELETE /api/ai/assistants/{assistant_id}/`、`GET .../avatar/`。写操作限运营，读操作限登录用户。验证：`python -m pytest -c tests/pytest.ini tests/ai_assistant/api/test_assistants.py -q` 覆盖 201、403、401、404。

## 2. 工具目录与装配

- [x] 2.1 在 `engines/ae_harness/tools` 增加只读目录：域、预设、函数名与说明，不造 Agent、不读配置。验证：`python -m pytest -c tests/pytest.ini tests/engines/ae_harness/unit/test_tool_catalog.py -q` 断言 `adb` 含全部与只读。
- [x] 2.2 `backend_bridge` 按「预设 + add/remove」过滤 `build_adb_tools()` / 只读子集，拒绝未知名字。验证：`python -m pytest -c tests/pytest.ini tests/engines/backend_bridge/unit/test_tool_selection.py -q`。
- [x] 2.3 增加只追加系统提示的装配入口：`create_agent` 仍用占位提示词文件，运营正文由调用方传入后追加。验证：单测断言最终系统提示含传入正文，且源码不 import `ae_harness.assistant`。

## 3. 测试对话

- [x] 3.1 新增对话栏与消息表：栏保存首次发送的 snapshot 与状态，消息保存用户句和助手最终文本。验证：`python manage.py makemigrations --check` 通过。
- [x] 3.2 首次发送才建实例；同栏续聊复用；新栏不复用。离开页面不取消。验证：`python -m pytest -c tests/pytest.ini tests/engines/backend_bridge/unit/test_assistant_thread.py -q`。
- [x] 3.3 取消按 `thread_id` 登记独立 `CancelToken`，不影响其它栏；进程启动把 `running` 标为 `interrupted`。验证：`python -m pytest -c tests/pytest.ini tests/ai_assistant/unit/test_assistant_thread_cancel.py -q`。
- [x] 3.4 对话 HTTP：建栏、列表、发送、轮询状态、取消。发送前引用的运营配置已删除则 409。验证：`python -m pytest -c tests/pytest.ini tests/ai_assistant/api/test_assistant_threads.py -q`。

## 4. 前端与专有风格

- [x] 4.1 在 doodle-craft 登记「AI 助手颜料片」：虚线允许颜料片与对话栏面板；渐变允许无头像圆、发送钮和对话页头图标；当前栏为浅蓝填充加墨色框。验证：`references/components/` 有对应小节，且未改全局 `tokens.css`。
- [x] 4.2 替换 `/ai-assistant` 占位页为颜料片网格。卡片只显示用户名称、头像或笔色圆、Agent 配置名称。验证：`cd frontend && npx vitest run tests/ai-assistant` 覆盖三字段与无头像圆。
- [x] 4.3 配置弹窗：显示名、头像上传、运营配置下拉、工具域/预设/函数勾选。保存走助手接口。验证：同一前端测试覆盖空工具可提交、未知函数由接口错误展示。
- [x] 4.4 对话页：多栏切换、发送才出现进行中、刷新后轮询到结果、取消只停当前栏。笔色来自该助手。验证：`npx vitest run tests/ai-assistant` 与 `npm run typecheck` 通过。
- [x] 4.5 样式门禁：`cd frontend && npm run lint:styles`。虚线只出现在助手颜料片、对话栏面板与既有白名单文件。

## 5. 关单

- [x] 5.1 `python manage.py check`、相关 ruff、`python utils/gen_arch_stats.py --check-boundaries` 通过。验证：三条命令退出码 0。
- [x] 5.2 确认未改 `/api/ai/roles/`、未改 `frontend/src/modules/ai-assistant/api/agents.ts` 的任务清单契约、未实现 SOP 选择助手。验证：`git diff` 中这些路径无行为变更。
