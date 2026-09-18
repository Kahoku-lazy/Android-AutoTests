## 1. #1 尾斜杠规范化

- [x] 1.1 新增 `gateway/normalize_slash.py`；`config/settings.py` MIDDLEWARE 最前挂载；验证 `python manage.py check && python -m ruff check gateway/normalize_slash.py config/settings.py`
- [x] 1.2 新增 `tests/test_middleware_slash.py`（unit）：/api/devices→补斜杠、/api/runner/tasks→不动、非 api→不动、不存在路径→不动；验证 pytest

## 2. #2 预检分辨率补齐

- [x] 2.1 `engines/android/airtest_u2.py::_verify_display` 补键循环扩展 displayWidth/displayHeight；验证 ruff
- [x] 2.2 契约用例新增：display_info 缺宽高 → 从 u2 info 补齐；验证 `python -m pytest tests/engines -m unit --nomigrations -q`

## 3. 回归

- [x] 3.1 全量后端：`python -m pytest -m "unit or integration" --nomigrations -q`（基线 311 + 6 = **317 passed**）
- [x] 3.2 真机：#1 `GET /api/devices`（无尾斜杠）→ **200 OK 2 设备** ✅；#2 引擎直连真机 `device_info` 含 `displayWidth:1440/displayHeight:3040`（自 u2 info 补齐，原生键为 width/height）✅
