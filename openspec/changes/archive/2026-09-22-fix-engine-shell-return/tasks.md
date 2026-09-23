## 1. 引擎实现归一化

- [x] 1.1 修改 `engines/device/android/u2.py::shell`，返回 `self._u2.shell(cmd).output`，验证：`python -m ruff check engines/device/android/u2.py` 与 `python -m ruff format --check engines/device/android/u2.py` 通过

## 2. 回归守卫（零设备）

- [x] 2.1 新增 `tests/graybox/unit/test_engine_shell_contract.py`：假 u2 的 `shell` 返回真 `uiautomator2.abstract.ShellResponse`，断言 `U2Engine.shell` 返回类型为 `str` 且等于 stdout，并断言协议对 `shell` 的返回声明为 `str`，验证：`python -m pytest tests/graybox/unit/test_engine_shell_contract.py -q` 通过（不连设备）

## 3. 端到端确认与门禁

- [x] 3.1 真机确认修复：对 `R5CT62RH88F` 调用 `list_apps`，验证：返回 `{"packages": [...], "count": N}`，不再抛 `AttributeError`、不再 400
- [x] 3.2 门禁：`python manage.py check`、`python -m ruff check engines/device/android/u2.py tests/graybox/unit/test_engine_shell_contract.py`、`python -m pytest tests/graybox/unit -q`，验证：全部通过
