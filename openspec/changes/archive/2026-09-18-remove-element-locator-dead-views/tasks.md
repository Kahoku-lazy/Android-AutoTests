## 1. 变更

- [x] 1.1 `openspec/changes/remove-element-locator-dead-views/` 四件套（`skip_specs: true`）
- [x] 1.2 `openspec validate remove-element-locator-dead-views` 通过 —— `Change 'remove-element-locator-dead-views' is valid`

## 2. 删除死代码

- [x] 2.1 删除 `apps/element_locator/views_web.py` —— 196 行；符号 `list_web_elements` / `web_element_detail` / `flows_handler` 等排除自身定义后引用数为 0
- [x] 2.2 删除 `apps/element_locator/views_flows.py` —— 120 行；同上
- [x] 2.3 删除 `apps/element_locator/views_web_groups.py` —— 核实中发现：它只被护栏测试 import 着，而那个测试断言的是「这些符号不存在」→ 本身即「无实质消费者」的证据
- [x] 2.4 删除 `apps/element_locator/views_api_assets.py` —— 同上；`create_api_endpoint` 在 `api.py` 里的同名者是写原语（同名不同物），不是引用
- [x] 2.5 删除 `views_projects_drf.py` 中的 `group_write_gone`（含随之无用的 import 清理） —— `_GONE_MSG` 也随之无人引用，一并删除；`api_view` 仍被另两个函数使用，保留

## 3. 护栏用例

- [x] 3.1 `test_element_locator_group_writes_removed.py`：模块断言由「符号不存在」改为「模块不存在」（`find_spec`） —— 改用 `importlib.util.find_spec(...) is None` + 参数化为 4 个模块名；护栏强度不降反升
- [x] 3.2 保留并复核 `api.__all__` 中写原语不存在的断言 —— 保留 `api.__all__` 与 `hasattr` 双重断言（8 个写原语）
- [x] 3.3 跑该用例 + `test_element_locator_views_split.py` 全绿 —— 48 passed（含 `test_element_locator_views_split.py` 行数预算用例：删除后 glob 集合自动缩小）

## 4. 文档

- [x] 4.1 `dev_docs/DEV_TEST/接口文档/API-元素定位.md`：修正「两种信封 / 尾斜杠差异 / NormalizeTrailingSlashMiddleware」的过期描述 —— 修正「信封双口径 / 尾斜杠差异 / NormalizeTrailingSlashMiddleware」三处过期描述；并顺带修掉 `API-设备检查器.md`、`API-评估器.md`、`API-仪表盘.md` 中引用已删中间件的 3 处

## 5. 门禁与归档

- [x] 5.1 `manage.py check` / `ruff` / `format` / `gen_arch_stats.py --check-boundaries` —— check / ruff / 边界检查全部通过
- [x] 5.2 `pytest tests/graybox/unit tests/arch` —— `tests/graybox/unit` + `tests/arch` **307 passed**
- [x] 5.3 归档（`skip_specs`，无 spec delta）
## 6. 实施期发现（需另开变更）

- [x] 6.1 **`evaluator` 存在同款重复路由遮蔽**：`apps/evaluator/urls.py` 同样是 `urlpatterns = router.urls + legacy_patterns`，
  router 在前。统一尾斜杠后，手写的 `banks/`、`banks/create/`、`banks/<id>/`、`banks/<id>/update/`、`banks/<id>/delete/`、
  `runs/`、`runs/start/`、`runs/<id>/`、`runs/<id>/delete/`、`results/<id>/score/` 共 **11 条**全部被 ViewSet 遮蔽、**不可达**。
  实测：`/api/evaluator/banks/` → `bank-list`（QuestionBankViewSet）而非 `list_banks`。
  本变更**未处理**（属独立的取舍决策：删除被遮蔽的 legacy 侧，还是调整注册顺序），已在归档说明中登记。
- [x] 6.2 全仓核对：已删中间件引用 **0**、已删视图模块引用 **0**（`dev_docs` / `apps` / `config` / `gateway`）
