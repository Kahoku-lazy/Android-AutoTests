## 1. 基类与重构

- [x] 1.1 新增 `tests/engines/contract_base.py`（EngineContractTestBase + 6 契约类 + 假件）；验证 `python -m ruff check tests/engines/contract_base.py`
- [x] 1.2 `test_airtest_u2_contract.py` 重构为基类继承 + 接线 + 静态辅助；验证 `python -m pytest tests/engines -m unit --nomigrations -q`（**25 passed**）

## 2. 门禁

- [x] 2.1 全量：`python -m pytest -m "unit or integration" --nomigrations -q`（**308 passed**）+ `--check-boundaries` 零违规
- [x] 2.2 落地实测差距 #3 标注已完成
