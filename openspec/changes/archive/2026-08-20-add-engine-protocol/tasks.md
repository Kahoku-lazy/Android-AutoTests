## 1. 数据契约与协议（engines/ + models/）

- [x] 1.1 新增 `models/ui_nodes.py`：`Node` dataclass（depth/class_name/text/content_desc/resource_id/package/index/bounds/x/y/width/height/clickable/enabled/scrollable/checkable/checked/focusable/long_clickable/xpaths 默认空列表）；验证 `python -m ruff check models/ui_nodes.py`
- [x] 1.2 新增 `engines/base.py`：`EngineCapabilities`（xpath_locate/toast_wait/ocr 三标志默认 False）+ `UiEngine` Protocol（connect/disconnect/is_alive/reconnect/screenshot/dump_hierarchy/app_current/click/long_click/swipe/input_text/press_key/shell/start_app/stop_app/exists/get_text/wait_toast/capabilities）；验证 `python -m ruff check engines/base.py`
- [x] 1.3 新增 `engines/registry.py`：`ENGINE_REGISTRY = {"airtest_u2": "engines.android.airtest_u2.AirtestU2Engine"}`、`ConfigurationError`、`get_device_engine(name)`（惰性 import + 实例缓存 + 失败转 ConfigurationError）；验证 ruff + `python -c "from engines.registry import get_device_engine, ConfigurationError"`

## 2. 单元测试（tests/engines/）

- [x] 2.1 新增 `tests/engines/test_base.py`：Node 默认值与字段、EngineCapabilities 默认值、Node 可从 `models.ui_nodes` import；验证 `python -m pytest tests/engines/test_base.py -m unit -q`
- [x] 2.2 新增 `tests/engines/test_registry.py`：未知名 → ConfigurationError；已知名（monkeypatch sys.modules 注入假实现）→ 返回实例且缓存；airtest_u2 未实现时调用 → ConfigurationError（含路径信息）；验证 `python -m pytest tests/engines/test_registry.py -m unit -q`

## 3. 门禁与文档同步

- [x] 3.1 全量门禁：`python manage.py check`（0 issues）+ ruff（全过）+ `python -m pytest -m "unit or integration" --nomigrations -q`（**270 passed**，261 基线 + 9 引擎契约测试）
- [x] 3.2 层纯度红线：`grep -rn "from apps\|import django" engines/` 0 命中；`python tools/gen_arch_stats.py --check-boundaries`
- [x] 3.3 Checklist §五 P0 引擎接口行标记完成；L1c 详档 §三/§四 标注"契约已落地"（实现待 3b）
