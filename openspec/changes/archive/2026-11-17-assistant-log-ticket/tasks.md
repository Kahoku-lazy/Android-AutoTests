## 1. 换票与验票

- [x] 1.1 在 `ai_assistant/api.py` 签发 60 秒一次性 ticket，只记栏编号与报告编号。进行中拒绝。验证：`python -m pytest -c tests/pytest.ini tests/ai_assistant/unit/test_assistant_log_ticket.py -q`。
- [x] 1.2 打开报告时接受 `ticket`。匹配且未过期则返回 HTML 并作废；无票、过期、已用、栏不匹配返回拒绝。验证：`python -m pytest -c tests/pytest.ini tests/ai_assistant/api/test_assistant_log_ticket.py -q`。

## 2. 前端

- [x] 2.1 「查看」先换票再 `window.open`，地址不含登录令牌。验证：`cd frontend && npx vitest run tests/ai-assistant` 覆盖换票后打开。

## 3. 关单

- [x] 3.1 `python manage.py check` 与相关 ruff 通过。验证：两条命令退出码 0。
