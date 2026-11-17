## 1. 记录一轮

- [x] 1.1 增加助手日志根目录常量 `logs/agents/assistants`，不复用 SOP 的 `REPORT_ROOT`。验证：单测断言路径末段为 `assistants`，且与 SOP 根目录不同。
- [x] 1.2 助手一轮改为 `reply_stream`，把事件交给 `AgentEventRecorder`，目录为 `<根>/<助手编号>/<对话栏>`。验证：`python -m pytest -c tests/pytest.ini tests/ai_assistant/unit/test_assistant_thread_log.py -q` 断言生成 jsonl 与 html。
- [x] 1.3 消息保存该轮时间戳目录名，不保存绝对路径。取消与失败也保留已有文件。验证：同一测试断言取消后 `report_id` 仍可解析到栏目录内。

## 2. 查看

- [x] 2.1 增加该栏日志列表与打开 HTML 的接口。路径跳出该栏目录返回 404；进行中返回 409。验证：`python -m pytest -c tests/pytest.ini tests/ai_assistant/api/test_assistant_thread_logs.py -q`。
- [x] 2.2 对话栏增加「日志」入口，列出各轮并在新窗口打开 HTML。验证：`cd frontend && npx vitest run tests/ai-assistant` 覆盖入口与进行中不可打开。

## 3. 关单

- [x] 3.1 `python manage.py check` 与相关 ruff 通过。验证：两条命令退出码 0。
- [x] 3.2 确认未改 SOP 报告根目录，且助手日志接口不返回磁盘绝对路径。验证：`git diff` 中 `REPORT_ROOT` 赋值未改，接口测试无绝对路径字段。
