## 1. 权威状态判定（state_machine）

- [x] 1.1 `state_machine.py` 新增 `display_state(tc) -> str`（running → queued+终态漂移 → queued → 终态 outcome → idle；引用 `TaskCardStatus`/`TaskOutcome`）；验证 `python -m ruff check apps/test_runner/state_machine.py`
- [x] 1.2 新增 display_state 单测（并入 `tests/test_runner/test_enums_baseline.py` 或 state_machine 基线）：running 标志优先、queued 纯排队、queued+终态漂移、completed 终态、非终态 idle；验证 `python -m pytest tests/test_runner -m "unit or integration" --nomigrations -q`

## 2. 序列化下发 + DEVICE_ENGINE 接线

- [x] 2.1 `task_views.task_card_list` 序列化加 `"state": sm.display_state(tc)`；基线序列化测试增 `state` 断言；验证 `python -m pytest tests/test_runner/test_state_machine_baseline.py --nomigrations -q`
- [x] 2.2 `config/settings.py` 加 `DEVICE_ENGINE = "airtest_u2"`；`apps/device_pool/session.py` 工厂改 `getattr(settings, "DEVICE_ENGINE", DEFAULT_ENGINE)`；验证 `python manage.py check && python -m ruff check config/settings.py apps/device_pool/session.py`

## 3. 全量门禁与文档同步

- [x] 3.1 全量门禁：`python manage.py check`（0 issues）+ ruff（全过）+ `python -m pytest -m "unit or integration" --nomigrations -q`（**308 passed**，300 基线 + 8 display_state/序列化测试）
- [x] 3.2 Checklist §五 P2 权威状态行标记完成；Step 4 登记的 DEVICE_ENGINE 接线项关闭
