## 1. 引擎实现

- [x] 1.1 新增 `engines/agents/tools/tool_ocr.py`：`ocr_page(serial, texts="")`（只读，返回文本/置信度/角点/归一化中心点）与 `ocr_tool_specs(output_root="")`；验证：`ocr_tool_specs()` 返回一个只读 `ocr_page` 规格
- [x] 1.2 实现只用 `engines.device.action` 与 `utils.vision.ocr`，`PIL`/`cnocr` 惰性导入；验证：`ruff check engines/agents/tools/tool_ocr.py` 通过，全文件无 `apps.` import
- [x] 1.3 更新 `engines/agents/tools/__init__.py` 的模块说明，登记 OCR 工具模块；验证：docstring 含 `tool_ocr`

## 2. 不装配约束

- [x] 2.1 本单未修改 `engines/agents/tools_config.py`；验证：该文件内不含 `ocr_page`（其中存在并行改动，非本单引入）
- [x] 2.2 新增 `tests/engines/agents/test_ocr_tool.py`：断言规格存在且只读、执行/验收基础工具与全部可开关组均不含 `ocr_page`、文本过滤与归一化中心点正确；验证：`pytest tests/engines/agents/test_ocr_tool.py -q` → 4 passed

## 3. 门禁

- [x] 3.1 `python manage.py check` 通过；`ruff check/format` 对新增文件与测试通过（`engines` 全目录存在既有 lint 债务 `engines/device/android/android_device.py` 3 条，非本单引入）
- [x] 3.2 `python tools/gen_arch_stats.py --check-boundaries` 零违规
- [x] 3.3 `python -m pytest tests/arch -q` → 24 passed
