## 1. 识别包迁入引擎

- [x] 1.1 将 `utils/vision/`（`__init__.py` 与 `ocr.py`）移到 `engines/vision/`，模块说明改为引擎视觉识别包，删除 `utils/vision`。验证：`engines/vision/ocr.py` 存在且含 `recognize`，`utils/vision` 不存在，`ruff check engines/vision` 通过。
- [x] 1.2 更新 `engines/__init__.py` 的包说明，写明 `engines.vision` 是页面文本识别，只供引擎 OCR 工具调用。验证：该文件说明含 `engines.vision`，且 `ruff check engines/__init__.py` 通过。

## 2. 唯一调用方

- [x] 2.1 `engines/agents/tools/tool_ocr.py` 的惰性导入改为 `engines.vision.ocr.recognize`，模块说明同步。验证：`pytest tests/engines/agents/test_ocr_tool.py -q` 通过，且该文件顶层不导入 `engines.vision`。
- [x] 2.2 在 `tests/engines/agents/test_ocr_tool.py` 增加源码扫描：Python 文件中出现 `engines.vision` 的，只能是 `engines/vision/` 自身、`engines/__init__.py` 的包说明，以及 `engines/agents/tools/tool_ocr.py`。验证：该新用例通过，且 `rg "utils\.vision|engines\.vision" --glob "*.py"` 无 `utils.vision`、无 `apps/` 命中。

## 3. 检查器停止执行识别

- [x] 3.1 删除 `apps/device_inspector/service.py` 的 `capture_ocr_payload` 与 `ocr_page_payload`。验证：`rg "recognize|capture_ocr_payload|ocr_page_payload" apps/device_inspector/service.py` 无命中，`ruff check apps/device_inspector/service.py` 通过。
- [x] 3.2 `apps/device_inspector/api.py` 删除 `ocr_screen` 及其白名单导出；`capture_snapshot` 只接受 `dump`，其他 `method` 在打开设备之前以 `CaptureError`（400，「无效的获取方法」）拒绝；成功路径写入空 OCR 载荷。`models.py` 注释改为新抓取只有 `dump`，历史行 `method` 仍可能是 `ocr`。不改表、不改 `snapshot_to_dict` 的历史读出。验证：`python manage.py check` 通过，`ruff check apps/device_inspector` 通过，`rg "ocr_screen|utils\.vision" apps/device_inspector` 无命中。
- [x] 3.3 为 `method=ocr` 增加单测：调用 `capture_snapshot` 得到状态 400 的 `CaptureError`，且不落库。仓库内若仍有引用 `ocr_screen` / `ocr_page_payload` / `capture_ocr_payload` 的测试，改为断言入口已删除或抓取被拒绝。验证：该单测通过。

## 4. 过时说明与边界

- [x] 4.1 把 `frontend/src/modules/device-inspector/store.ts` 中「后端仍接受 ocr」的注释改为抓取只接受 `dump`。验证：该文件不再声称后端保留 `ocr` 入参。
- [x] 4.2 跑架构边界检查。验证：`python tools/gen_arch_stats.py --check-boundaries` 通过。
