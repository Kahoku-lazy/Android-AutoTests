# Tasks: route-cross-app-imports-via-api

## 1. api 导出

- [ ] 1.1 usage_ledger/api.py 增 `display_fx()` 只读口（返回展示汇率与日期）并进 `__all__`，docstring 按模板。验证：新增 unit 用例断言返回值与 rates 常量一致；`python -m pytest -c tests/pytest.ini tests/task/unit/test_usage_ledger.py -q` 通过
- [ ] 1.2 task_list/api.py re-export `case_identity_label` 并进 `__all__`。验证：`python -c "from backend.apps.task_list.api import case_identity_label"` 成功，`python -m pytest -c tests/pytest.ini tests/task/unit -q` 通过

## 2. 消费方改道

- [ ] 2.1 前置检查：retire-backend-dead-code 已合并（ai_usage.py 无未合并改动）。dashboard/ai_usage.py 删 rates import 改调 `usage_ledger.api.display_fx()`；三处 case_identity import（dashboard/ai_usage.py、report_generator/report_inventory.py、bug_manager/api.py）改调 `task_list.api.case_identity_label`。验证：grep `usage_ledger.rates|task_list.case_identity` 于 backend/apps 跨 App 消费零命中；`python -m pytest -c tests/pytest.ini tests/dashboard tests/report tests/bug_ticket -q` 通过

## 3. 门禁补盲

- [ ] 3.1 utils/gen_arch_stats.py `--check-boundaries` 增「跨 App import 非 api/models/contracts 模块即违规」AST 规则。验证：`python utils/gen_arch_stats.py --check-boundaries` 对修复后全仓零违规；临时 fixture 负向自测（构造违规 import 断言报错）通过后清理 fixture
- [ ] 3.2 tests/arch/unit 增边界规则回归用例（若既有边界测试文件存在则并入）。验证：`python -m pytest -c tests/pytest.ini tests/arch/unit -q` 通过

## 4. 关单门禁

- [ ] 4.1 `python run.py check` 退出码 0；ruff check/format --check 相关路径通过；逐文件暂存、refactor(backend) 提交，推特性分支提 PR，确认 python 与 frontend 两个 CI job 全绿后合并