## Why

🟡 **element_locator 的「分组写」特性在路由层已停用，但代码层整簇残留**（死代码）。

事实链：

1. `urls.py` 已把 4 个分组写路径指向 `group_write_gone`（HTTP 410）：
   `web-groups/create` · `web-groups/batch-move` · `api-groups/create` · `api-groups/batch-move`；
   `web_group_detail` / `api_group_detail` 的 PUT/PATCH/DELETE 也直接返回 410。
2. 但**视图层**仍留着 4 个实现该特性、却无人引用的函数：
   `views_web_groups.create_web_group` · `views_web_groups.batch_move_web_groups` ·
   `views_api_assets.create_api_group` · `views_api_assets.batch_move_api_groups`
3. `api.py` 里对应的 8 个写原语也全部零调用：
   `create_web_group` · `rename_web_group` · `delete_web_group` · `batch_move_web_groups` ·
   `create_api_group` · `rename_api_group` · `delete_api_group` · `batch_move_api_groups`

实测（2026-09-15，`grep <12 个名字>` 于 `apps/`）：这 12 个符号的**全部命中只有「自身定义」与「\_\_all\_\_ 条目」**（4 个视图函数另加它们对 `api.*` 的调用）。跨模块消费方只有 `device_inspector` 用 `element_locator.api` 的 `ImportConflictError` / `import_snapshot_page` / `get_page_full`，与本簇无关；`dev_docs/` 零提及。

即：**一条已下线的特性留下了 12 个死函数（约 190 行）**，其中 4 个视图函数是上一个拆分单（`split-element-locator-views`）的「顺带查实」项。

## What Changes

- 删除 **4 个死视图函数**：`views_web_groups.py` 的 `create_web_group` / `batch_move_web_groups`；`views_api_assets.py` 的 `create_api_group` / `batch_move_api_groups`
- 删除 **8 个死 api 原语**（含 `__all__` 中对应 8 项），以及因此变空的两个分节注释
  （`# ── WebGroup 写操作 ──` / `# ── ApiGroup 写操作 ──`）
- 清理删除后不再使用的 import（如 `views_web_groups.py` 的 `json`）——属本单自身造成的、必须同清
- 🟠 **顺带修复新测试查实的 500 缺陷**：`views_projects_drf.group_write_gone` 是**裸 Django 视图**却返回 DRF `Response`。
  `Response` 是 `SimpleTemplateResponse`，由 Django 的 template-response 中间件调 `.render()`；未经 DRF `dispatch` 的裸视图没有 `accepted_renderer`，
  实测（新测试首次运行）抛 `AssertionError: .accepted_renderer not set on Response` → **HTTP 500**。
  即 `apps/element_locator/AGENTS.md` 登记的「分组写 → HTTP 410」**从未成立**。修法：补 `@api_view(["POST"])` + `@extend_schema`（与同文件 `move_items` / `batch_delete_files` 同形）
- 新增 `tests/graybox/unit/test_element_locator_group_writes_removed.py`：
  ① 12 个符号在模块与 `api.__all__` 中**均已消失**；② 4 个写路径**仍** 410（路由与 `group_write_gone` 绑定未变）；③ 读路径（list/detail）不受影响

- **BREAKING**：无。被删符号全仓零调用；路由契约不变（写路径本就 410，现仍 410）
- 按 schema 约定设 `skip_specs: true`

## 关联文档

- 前置变更：`split-element-locator-views`（2026-09-15，其 tasks §5 登记本项）
- App 约束：`apps/element_locator/AGENTS.md`（**分组写（`web-groups`/`api-groups` create/update/delete/batch-move）→ HTTP 410**）
- 门禁：`django-backend-check/references/calibration.md` §2 · §7

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 不改 Requirement 文本，故无 delta）

## Impact

- 源码：`apps/element_locator/views_web_groups.py`（-2 函数）· `views_api_assets.py`（-2 函数）· `api.py`（-8 函数 -8 `__all__` 项）
- 测试：新增 `tests/graybox/unit/test_element_locator_group_writes_removed.py`
- 验证：`manage.py check` · `makemigrations --check` · `ruff check .` / `format --check .` · 全量 unit/arch/integration · `--check-boundaries`
- 不在本单范围：`group_write_gone`（410 出口）与读路径 list/detail 保留不动