## 1. 复核（已完成）

- [x] 1.1 确认路由已停用：`urls.py` 4 条写路径 → `group_write_gone`；两处 `*_group_detail` 的 PUT/PATCH/DELETE 亦 410（**但 HTTP 层实际不是 410，见 2.6**）
- [x] 1.2 实测 12 个符号（4 视图 + 8 api）在 `apps/` 的全部命中 = 自身定义 + `__all__` + 视图对 api 的调用 → **零外部调用**
- [x] 1.3 确认跨模块消费面：`device_inspector` 只 import `element_locator.api` 的 `ImportConflictError` / `import_snapshot_page` / `get_page_full`
- [x] 1.4 确认 `dev_docs/` 零提及这 12 个名字
- [x] 1.5 确认读路径依赖 `_web_group_payload` / `_api_group_payload`（保留）

## 2. 修改

- [x] 2.1 `views_web_groups.py`：删 `create_web_group` · `batch_move_web_groups`（-2 函数）
- [x] 2.2 `views_api_assets.py`：删 `create_api_group` · `batch_move_api_groups`（-2 函数）
- [x] 2.3 `api.py`：删 8 个原语 + `__all__` 8 项 + 两个已空的分节注释（`# ── WebGroup 写操作 ──` / `# ── ApiGroup 写操作 ──`）
- [x] 2.4 `ruff check --fix` 清理 3 处因此不再使用的 import
- [x] 2.5 新增 `tests/graybox/unit/test_element_locator_group_writes_removed.py`（13 条）
- [x] 2.6 🟠 **修复新测试查实的 500 缺陷**：`group_write_gone` 是裸 Django 视图却返回 DRF `Response` → `.render()` 时
      `AssertionError: .accepted_renderer not set on Response` → **HTTP 500**（即 AGENTS.md 登记的「分组写 → 410」从未成立）。
      修法：补 `@extend_schema` + `@api_view(["POST"])`（与同文件 `move_items` / `batch_delete_files` 同形），并附 docstring 说明原因
- [x] 2.7 同步上一拆分单的测试预期：`@api_view` 后 `func.__name__` 变 `'view'`，4 条 `group_write_gone` 条目改为只校验路由契约

## 3. 验证

- [x] 3.1 `python manage.py check` → 0 issues；`makemigrations --check` → `No changes detected`
- [x] 3.2 `python -m ruff check .` → **All checks passed!**；`ruff format --check .` → **258 files already formatted**
- [x] 3.3 新测试 **13 passed**；`test_element_locator_views_split.py` **41 passed**；`pytest tests/graybox/unit tests/arch -q` → **166 passed**
- [x] 3.4 `pytest tests/graybox/integration -q` → **16 passed**；`--check-boundaries` → 零违规
- [x] 3.5 复扫 12 个名字于 `apps/element_locator/` → **全仓零命中**

## 4. 本单最有价值的一点

**新写的测试当场查实了一个既有 500 缺陷**：4 条「分组写」路径被文档与 AGENTS.md 登记为 HTTP 410，实际是 **500**（裸 Django 视图返回 DRF `Response`）。
若只做「删死代码」而不写「仍 410」这条断言，这个缺陷会继续躺着 —— 这是「双向断言」（符号消失 **且** 行为不变）的直接收益。

## 5. 续做

- ② 收敛 element_locator 写路径（`views_drf.py` 两处 `serializer.save()` + `api.py` 写函数返回 ORM 的契约）
- ③ 其余 ViewSet 的隐式写（`case_manager` 4 · `element_locator/views_projects_drf` 2 · `evaluator` 3 · `ai_assistant/views_drf` 1）
