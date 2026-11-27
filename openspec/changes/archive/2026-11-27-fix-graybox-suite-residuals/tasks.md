## 1. device 状态同步缓存隔离

- [x] 1.1 新增 `tests/device/conftest.py`：autouse 夹具在用例前后调用 `reset_status_sync_cache()`。
  验证：`python -m pytest -c tests/pytest.ini tests/device -q` 全绿（原 1 failed / 30 passed）。

## 2. me 响应 schema 补字段

- [x] 2.1 `tests/api_kit/schemas.py` 的 `ME_SUCCESS_SCHEMA` 补 `is_operator` / `is_assistant_author`，加入 `required`，保留 `additionalProperties: False`。
  验证：`python -m pytest -c tests/pytest.ini tests/auth -q -m "not e2e"` 全绿（原 1 failed / 52 passed）。

## 3. 关单

- [x] 3.1 `python -m pytest -c tests/pytest.ini tests/device tests/auth -q -m "not e2e"` 0 失败。
- [x] 3.2 `python -m run check` 阻塞项 30/30。
- [x] 3.3 `openspec validate fix-graybox-suite-residuals` 通过。
