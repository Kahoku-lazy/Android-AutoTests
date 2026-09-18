## 1. 协议前置与开关

- [x] 1.1 `session.py`：EXCLUSIVE lease 前置校验（process 业务锁）；`connect.py` use_session 模式 + `_sessions` + `release_session`；`executor.py::_cleanup_device` 加释放；`execution.py` 两调用点传 settings；`settings.py` 加开关；验证 `python manage.py check && ruff check`
- [x] 1.2 单测：`tests/device_pool/test_session.py` 增 EXCLUSIVE 前置两用例；`tests/test_runner/test_connect_baseline.py` 增 use_session 注册/释放用例；断言 `settings.DEVICE_SESSION_ENABLED` 默认 False；验证 pytest 相关文件

## 2. 门禁与登记

- [x] 2.1 全量后端：`python -m pytest -m "unit or integration" --nomigrations -q`（基线 322 + 6 = **328 passed**；修正：EXCLUSIVE 前置校验置于租用冲突检查之后，避免无锁场景的 DB 访问）
- [x] 2.2 落地实测差距 #1 标注"开关式接入已落地（默认关），真机开关验证待重启后端执行"
