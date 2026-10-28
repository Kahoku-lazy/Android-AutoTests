## 1. 后端 BUG 域

- [x] 1.1 新建 `backend/apps/bug_manager/`（apps/models/api/extract/serializers/views/urls/migrations/admin），模型 `BugTicket` 使用 `bug_tickets` 表、`(task_id, category, source_ref)` 唯一约束与分类/状态索引；运行 `python manage.py makemigrations bug_manager` 与 `python manage.py check` 通过。
- [x] 1.2 在 `BugTicket` 上实现 `bug_no` 属性（`BUG-{id:04d}`）与状态常量；运行 `python manage.py shell` 观察迁移后表结构，确认无 FK 到 `Task`。
- [x] 1.3 注册 `backend.apps.bug_manager` 到 `INSTALLED_APPS`，在 `backend/config/urls.py` 挂 `/api/bugs/`，在 OpenAPI `TAGS` 增加 `bugs`，在 `utils/gen_arch_stats.py` 的 `TABLE_PREFIX` 登记 `bug_manager: "bug_"`；运行 `python manage.py check` 与 `python utils/gen_arch_stats.py --check-boundaries` 通过。

## 2. 提取规则与登记服务

- [x] 2.1 在 `bug_manager/extract.py` 实现 `build_bug_drafts`：UI 自动化失败用例逐条、无明细时任务级、中断任务级、用例编写失败任务级、入库失败、取消跳过、标题截断；补 `tests/graybox/unit/test_bug_ticket_extract.py`，pytest 通过。
- [x] 2.2 在 `bug_manager/api.py` 实现 `record_task_bugs` 与 `sync_visible_tasks`：幂等 `get_or_create`、保留 `status/resolved_at`、并发唯一冲突重查、返回 `created/updated/skipped`；补 `tests/graybox/unit/test_bug_ticket_api.py` 覆盖重复登记与已解决状态不被覆盖。
- [x] 2.3 实现 `sync_bug_tickets` 管理命令（`bug_manager/management/commands/sync_bug_tickets.py`），扫描失败/中断与入库失败任务并调用同一服务；运行 `python manage.py sync_bug_tickets` 在本地库可重复执行且第二次 `created=0`。

## 3. 任务终态接入

- [x] 3.1 `task_list.api.finalize_task` 在保存终态后调用 `bug_manager.api.record_task_bugs`，异常只记日志、不改变任务状态；补 `tests/graybox/unit/test_case_authoring_task_runner.py` 或新增测试断言失败任务产生 BUG、登记异常不影响任务。
- [x] 3.2 `task_list.api.recover_orphaned_tasks` 在把任务改 `interrupted` 后逐条登记 BUG；补单元测试覆盖中断任务产生 BUG。
- [x] 3.3 确认 `delete_task` 不级联删除 BUG 单，并在 `bug_manager` 同步时对已删除任务使用快照标题；pytest 通过。

## 4. BUG API 与契约

- [x] 4.1 `GET /api/bugs/` 支持分类、状态、关键字过滤与 `summary` 统计，按当前用户可见 Agent 隔离；`GET /api/bugs/{id}/` 返回完整正文；`PATCH /api/bugs/{id}/` 只接受三种状态并维护 `resolved_at`；补 `tests/api/test_bug_tickets.py`，pytest 通过。
- [x] 4.2 实现 `POST /api/bugs/sync/` 返回 `scanned/created/updated/skipped`，并只扫描当前用户可见任务；补测试覆盖同步幂等与不可见 Agent 隔离。
- [x] 4.3 更新 `openspec/openapi.yaml`（如项目门禁要求）并运行 `python run.py check` 中 OpenAPI 相关检查；确认 `/api/bugs/*` 出现在 schema。

## 5. 前端 BUG 单管理

- [x] 5.1 新建 `frontend/src/modules/bug-manager/`（`index.vue`、`routes.ts`、`api.ts`、`constants.ts`、`types.ts`、`components/BugDetailDrawer.vue`），实现分类/状态筛选、关键字、KPI、表格、详情抽屉、任务跳转与状态更新；`npx vue-tsc --noEmit` 与 `npm run lint:styles` 通过。
- [x] 5.2 在 `router.ts` 汇总 `/bugs` 路由；在 `sidebarNavConfig.ts` 的「AI任务」分组追加「BUG单管理」与独立 `MOD_COLORS["/bugs"]`；在 `lucide-registry.ts` 注册 `Bug` 图标；更新 `frontend/tests/shared/p0/sidebarNavConfig.spec.ts` 断言四项顺序与新模块色。
- [x] 5.3 补 `frontend/tests/bug-manager/p0/` 常量/映射测试（分类标签、状态标签、任务链接、关键字参数），`npx vitest run tests/bug-manager tests/shared` 通过。
- [x] 5.4 保证新 `.vue` ≤ 500 行，卡片/抽屉/三态使用共享件；`npx vitest run tests/task-list tests/shared tests/bug-manager` 与 `npm run build:check` 通过。

## 6. 门禁与人工验收

- [x] 6.1 运行 `ruff check backend/apps/bug_manager backend/apps/task_list` 与 `ruff format --check`，通过；运行 `python utils/gen_arch_stats.py --check-boundaries` 确认跨 App 只走 `api.py`。
- [x] 6.2 运行 `python -m pytest -c tests/pytest.ini tests/graybox/unit/test_bug_ticket_extract.py tests/graybox/unit/test_bug_ticket_api.py tests/api/test_bug_tickets.py`，全部通过。
- [x] 6.3 启动前后端，打开 `/bugs` 确认侧栏入口、分类切换、任务编号跳转、状态更新与「同步历史错误」可用；确认历史失败任务补录后列表出现分类正确的 BUG 单。
- [x] 6.4 运行 `openspec validate add-bug-ticket-management --strict` 与 `python run.py check`，记录与本次无关的既有失败项；完成 OpenSpec 归档。
