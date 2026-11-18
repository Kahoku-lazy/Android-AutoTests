# Tasks: rework-test-report-inventory

## 1. 后端：报告台账聚合与接口重建

- [x] 1.1 新建 `backend/apps/report_generator/report_inventory.py` 只读聚合模块（SOP 侧：终态 Task + result 定位解析；智能体侧：带 report_id 的助手消息 + 批量名片名；合并倒序、source/keyword/日期过滤、扫描≤1000/返回≤500、summary 三计数），按注释模板写模块/函数 docstring；验证：`python manage.py check` + `ruff check backend/apps/report_generator` 通过
- [x] 1.2 重写 `report_generator/views.py` 的 `ReportListAPIView` 改调 report_inventory（视图只分发），更新 OpenAPI 参数与响应描述；验证：`python manage.py check` 通过，`/api/reports/` 返回 `{status, data:{summary,total,items}}` 信封
- [x] 1.3 新建 `tests/report/unit/test_report_inventory.py`：覆盖规格场景——完成/失败任务带定位入列、pending/running/cancelled/interrupted 不入列、DONE 轮次入列、running 轮次不入列、名片删除名称回落、用例身份三口径（单条/多条/里程碑/空）、summary 计数、关键字命中任务 ID、扫描与返回上限；验证：`python -m pytest -c tests/pytest.ini tests/report/unit` 全绿
- [x] 1.4 新建 `tests/report/integration/test_report_envelope.py`：列表信封、未登录空负载、`/api/reports/cases/`、`/api/reports/run/{id}/`、`/api/reports/{filename}/`、`/api/reports/{filename}/content/` 均 404；验证：`python -m pytest -c tests/pytest.ini tests/report/integration` 全绿

## 2. 后端：遗产退役

- [x] 2.1 删除 `report_generator/views.py` 的 ReportDownload/ReportContent 视图与 `urls.py` 对应两条路径、`service.py`、`api.py` 的 save_report/ReportGenerator 导出；验证：`python manage.py check` + `ruff check backend/apps/report_generator` 通过，1.4 的 404 用例仍全绿
- [x] 2.2 确认 `rg_reports`/`rg_report_templates` 为空表后删除 `Report/ReportTemplate` 模型并生成 drop 迁移（人工核对迁移语句，反向迁移可重建表结构）；验证：`python manage.py makemigrations --check` 通过 + 迁移正向/反向各执行一次成功
- [x] 2.3 删除 `backend/apps/task_list/task_reports.py`（build_report_list/build_task_flow/report_cache_meta 全仓无其它调用方，先 grep 复核），清理 `tests/report/` 下 .pyc 残骸；验证：全仓 grep 无 `task_reports` 引用 + `python manage.py check` + `python -m pytest -c tests/pytest.ini tests/task tests/report` 全绿
- [x] 2.4 架构边界复核：`python utils/gen_arch_stats.py --check-boundaries` 通过（report_inventory 只读跨 App Model 与 case_identity 纯函数，无 service/views import）

## 3. 前端：报告台账页重建

- [x] 3.1 重写 `modules/report-generator/` 的 types.ts/constants.ts/api.ts：报告行 DTO（sop/agent 两来源）、KPI/筛选/空态文案常量唯一真相源、列表请求走 `/reports/`；查看报告复用 `task-list/api/tasks.ts` 的 fetchTaskReport 与 `ai-assistant/api/assistants.ts` 的 issueLogTicket/threadLogUrl，不新拼地址；验证：`npm run typecheck` 通过
- [x] 3.2 重建 index.vue 为报告台账（WorkbenchHeader + 报告概览 KPI 三卡 + 测试报告分区：FilterTabs 来源筛选带计数、关键字/日期过滤、AppTable 单表、前端分页、EmptyState/ErrorState 三态），身份列按来源切换（SOP→用例名称+任务 ID；智能体→助手编号+名称），超 500 行拆 components/composables；验证：`npm run build` + `npm run lint:styles` 通过
- [x] 3.3 实现行点击打开报告：SOP 行 blob 新标签打开；智能体行换 ticket 后新标签直开；文件缺失提示「报告不存在」且列表不受影响；验证：`npm run typecheck` 通过 + 手动打开两类报告各一份成功
- [x] 3.4 重写 `frontend/tests/report-generator/` 测试：来源筛选计数、身份列渲染、空态文案、行点击分流与缺失提示；验证：`npx vitest run tests/report-generator` 全绿

## 4. 前端：入口挂载与遗产退役

- [x] 4.1 `router.ts` 导入 report-generator 路由（仅 `/reports` 单路由）；`sidebarNavConfig.ts` ai-tasks 组在 `/bugs` 后追加测试报告项（图标名先在运行时子集核验），删除 `/agent-reports` 色项；验证：`npx vitest run tests/shared/p0/sidebarNavConfig.spec.ts` 通过（顺序断言更新为四项）+ 侧栏图标一致性测试通过
- [x] 4.2 删除 `modules/agent-reports/` 整模块与 `frontend/tests/agent-reports/`，全仓 grep 复核无残留引用；验证：`npm run typecheck` + `npm run build` 通过
- [x] 4.3 更新侧栏相关测试断言（AI任务组四项顺序、/reports 激活态与模块色独立）；验证：`npx vitest run tests/shared` 全绿

## 5. 文档与契约同步

- [x] 5.1 更新 `backend/apps/report_generator/AGENTS.md`（列表数据源改为 report_inventory 只读聚合、文件端点退役、关单清单）与 `frontend/src/modules/report-generator/AGENTS.md`（报告台账契约、行点击打开报告、单路由约束保留）；验证：`python utils/gen_arch_stats.py --check-md` 相关文档通过（如适用）+ 人工核对契约段与实现一致
- [x] 5.2 更新 `backend/config/settings.py` 的 reports API 分组描述为报告台账口径；验证：`python manage.py check` 通过

## 6. 全链路验收与提交

- [ ] 6.1 本地门禁 `python run.py check` 通过；前端 `npm run typecheck` + `npm run lint:styles` + 相关 vitest 全绿；后端 `python -m pytest -c tests/pytest.ini -m "unit or integration"` 涉及 report/task/bug/ai_assistant 路径全绿
- [x] 6.2 人工验收：侧栏四项顺序正确；跑一条 SOP 任务与一轮助手对话完成后报告入列、执行中不入列；两类报告可打开；KPI 计数与列表一致；`/reports/143` 落 404
- [ ] 6.3 逐文件暂存（禁 git add -A），Conventional Commits 提交并推送 Kahoku，确认 ci-phase1.yml 6 个 job 全绿
