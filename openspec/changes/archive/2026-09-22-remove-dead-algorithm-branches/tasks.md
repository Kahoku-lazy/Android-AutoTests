## 1. 删除 OCR 的 base64 缩略图

- [x] 1.1 `algorithms/vision/ocr.py`：`recognize()` 不再裁图与编码（删 `_pil_to_b64`、`Image.open`、crop 与 `thumbnail` / `thumbnail_format` 两个键），并同步模块与函数 docstring 的返回说明；`base64` / `io` / `PIL` 随之成为未用 import。验证：`python -m ruff check algorithms` 通过且 `grep -n "thumbnail|_pil_to_b64|base64|PIL" algorithms/vision/ocr.py` 无命中
- [x] 1.2 `apps/device_inspector/service.py`：删掉 `capture_ocr_payload` 里两处恒为空操作的 `pop` 与「丢弃 base64 缩略图」注释，函数 docstring 的「（不含 base64）」同步更新。验证：`python manage.py check` 通过，`grep -n "base64" apps/device_inspector/service.py` 无命中
- [x] 1.3 `tests/graybox/unit/test_inspector_ocr_tool.py`：桩输入 `_REGION` 不再伪造 `thumbnail` / `thumbnail_format`（`recognize()` 已不产出）；保留「OCR 工具响应只含文本/置信度/坐标/中心点」的字段断言。验证：`python -m pytest tests/graybox/unit/test_inspector_ocr_tool.py -q` 全绿

## 2. 删除分层算法的候选列表分支

- [x] 2.1 `algorithms/element_layers.py`：删 `element_entry` 的 `include_candidates` 形参与 `xpath_candidates` 输出分支、`build_layers` 的同名形参与透传，docstring 同步。验证：`grep -n "include_candidates|xpath_candidates" algorithms/` 无命中
- [x] 2.2 `tests/graybox/unit/test_element_layers.py`：去掉传 `True` 的断言，保留「候选按需生成、条目只带主定位」的断言。验证：`python -m pytest tests/graybox/unit/test_element_layers.py -q` 全绿

## 3. 规格与门禁

- [x] 3.1 `specs/element-layering/spec.md` delta 落地：MODIFIED 需求去掉「候选定位列表」并新增 MUST NOT 场景。验证：`npx openspec validate remove-dead-algorithm-branches --strict` 通过
- [x] 3.2 后端门禁：`python manage.py check`、`python -m ruff check`、`python -m ruff format --check`、`python -m pytest tests/graybox -q`、`python tools/gen_arch_stats.py --check-boundaries`。验证：全绿（分层接口用例含在 graybox 内）
