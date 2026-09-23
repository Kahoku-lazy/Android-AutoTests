## 1. 错误分类改造

- [x] 1.1 在 `apps/ai_assistant/views_tool_debug_drf.py` 新增 `ToolExecutionError(APIException)`（`status_code = 500`），并把 `except Exception` 分支改为先 `logger.exception` 再抛 500（附工具名与请求者），`ValueError` 分支维持 400，验证：`python -m ruff check apps/ai_assistant/views_tool_debug_drf.py` 通过

## 2. 用例

- [x] 2.1 在 `tests/graybox/unit/test_ai_platform_tool_debug.py` 增加用例：打桩 `invoke_platform_tool` 抛非 `ValueError` 异常 → 断言 **500** 且 `caplog` 捕获到含工具名的错误日志；并断言 `ValueError`（未知参数）仍是 **400**，验证：`python -m pytest tests/graybox/unit/test_ai_platform_tool_debug.py -q` 通过

## 3. 门禁与文档

- [x] 3.1 后端门禁：`python manage.py check`、`python -m ruff check apps/ai_assistant`、`python -m ruff format --check`（本次改动文件）、`python -m pytest tests/graybox/unit -q`，验证：全部通过
- [x] 3.2 接口文档登记失败状态码语义（4xx=入参/前置条件，5xx=工具或引擎内部故障），验证：接口文档对应小节含该语义说明
