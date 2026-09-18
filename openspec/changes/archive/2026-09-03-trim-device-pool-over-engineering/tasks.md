## 1. 占用前缀收敛

- [x] 1.1 contracts.py 定义 `RUNNER_OCCUPIED_PREFIXES`
- [x] 1.2 manager.py 删 `_RUNNER_PREFIXES`、改引用
- [x] 1.3 api.py 删 `_EXECUTION_OCCUPY_PREFIXES`、改引用
- 验证：ruff + grep 无重复前缀定义（device_pool 内）

## 2. import 规范化

- [x] 2.1 api.py list_devices 函数内 import 移到顶部
- 验证：ruff 无函数内 import

## 3. 回归验收

- [x] 3.1 `python manage.py check` 零 issues
- [x] 3.2 `ruff check` + `ruff format --check` 通过
- [x] 3.3 `pytest tests/graybox -m device_pool` 25 passed
- [x] 3.4 `--check-boundaries` 零违规
