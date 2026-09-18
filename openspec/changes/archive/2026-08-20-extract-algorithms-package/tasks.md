## 1. 新建 algorithms/ 包（纯平移）

- [x] 1.1 `algorithms/xpath.py`：自 `device_inspector/service.py:4-228` 平移 `gen_xpath_candidates`/`trim_hierarchy`/`_LAYOUT_VIEWGROUPS`/`_simple_class`/`_has_identity`/`_specificity`（函数体不改）；验证 `python -m ruff check algorithms/xpath.py`
- [x] 1.2 `algorithms/hierarchy.py`：自 `pool.py:175-240` 抽出 `parse_hierarchy_xml(raw)`（decode/前缀补全/截断检测/rfind 修复/bounds/walk），异常文案不变；验证 `python -m ruff check algorithms/hierarchy.py`
- [x] 1.3 `algorithms/vision/ocr.py`：自 `device_inspector/ocr.py` 平移 `_get_engine`/`_pil_to_b64`/`recognize`（双检锁保持）；验证 `python -m ruff check algorithms/vision/ocr.py`

## 2. 原处 re-export 与调用改造

- [x] 2.1 `apps/device_inspector/service.py`：头 228 行替换为 `from algorithms.xpath import ...` re-export（capture 编排段不动）；验证 `python manage.py check && python -m ruff check apps/device_inspector/service.py`
- [x] 2.2 `apps/device_inspector/ocr.py`：整体变 re-export（`from algorithms.vision.ocr import recognize, _get_engine, _pil_to_b64`）；验证 ruff
- [x] 2.3 `apps/device_pool/pool.py::dump_hierarchy`：fallback 循环保留，解析段替换为 `return parse_hierarchy_xml(raw)`；验证 ruff + `python -m pytest tests/device_inspector/test_hierarchy_baseline.py --nomigrations -q`

## 3. 测试与门禁

- [x] 3.1 新增 `tests/algorithms/test_package_smoke.py`：三模块直导冒烟 + re-export 对象同一性（`is` 断言）+ `parse_hierarchy_xml` 独立调用；验证 `python -m pytest tests/algorithms -m unit -q`
- [x] 3.2 全量门禁：`python manage.py check`（0 issues）+ `python -m ruff check algorithms apps/device_inspector apps/device_pool/pool.py tests/algorithms`（全过）+ `python -m pytest -m "unit or integration" --nomigrations -q`（**261 passed**，255 基线 + 6 冒烟）
- [x] 3.3 纯函数红线：`grep -rn "from apps" algorithms/` 与 `grep -rn "import django" algorithms/` 均 0 命中；`python tools/gen_arch_stats.py --check-boundaries`

## 4. 文档同步

- [x] 4.1 Checklist §五 P0 算法行标记完成；L1a 详档 §六 标注"已落地"（re-export 兼容期）
