## 1. 缺省不截断

- [x] 1.1 `api.list_layers` 的条数参数改为可缺省（`None` = 不切片），`elements` 返回自 `offset` 起的全部命中；显式给定时行为不变。验证：单测断言缺省时 `len(elements) == total_matched == summary["total"]`，且响应里的条数字段为 `null`
- [x] 1.2 `views.snapshot_layers` 参数解析：`limit` 缺省 → 不传（`None`）；显式传入时按整数解析，不可解析或 `≤ 0` 仍返回 400，并按既有约定钳制到 500。验证：接口测试覆盖「缺省返回全部（元素数 > 100）」「显式 limit=1 只回 1 条」「limit=abc → 400」「limit=0 → 400」
- [x] 1.3 集成测试补「分组计数与返回条目一致」用例：构造元素数 > 100 的快照，断言缺省响应的每个分组（含内容控件的二级分组）条目数等于该分组摘要计数。验证：`pytest tests/graybox/integration/test_inspector_layers_api.py -q` 全绿，既有分页 / 降级 / 404 用例不受影响
- [x] 1.4 同步 `api.list_layers` 的 docstring：记录条数缺省语义与 `null` 的含义；`test_layers_payload_is_lean` 保持显式 `limit=500`（体积用例需要确定量）。验证：docstring 与实现一致

## 2. 文档与门禁

- [x] 2.1 手写接口文档 `dev_docs/DEV_TEST/接口文档/API-设备检查器.md` 的「快照分层查询接口」小节补：条数缺省 = 不施加上限；未施加上限时 `limit` 为 `null`；`total_matched` 与分组计数的口径关系
- [x] 2.2 落单门禁全量执行：`python manage.py check`、`ruff check`、`ruff format --check`（相关路径）、`python manage.py makemigrations --check`、`pytest tests/graybox -q`、`python tools/gen_arch_stats.py --check-boundaries`。验证：全部通过
