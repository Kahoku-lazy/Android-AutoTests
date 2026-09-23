## 1. 后端 stats 项目维度

- [x] 1.1 将 `apps/dashboard/views.py` 的 `_cases_breakdown` 改为调用 `apps.case_manager.api.list_projects`，输出 `{project_id, name, total}`；`cases.total`/`enabled` 为各 `total` 之和；无 `user_id` 时返回空列表。删除因此闲置的 `_user_cases_q` 与对 `TestDefinition` 的类型计数。验证：`rg "test_type" apps/dashboard/views.py` 无用例拆分循环；`rg "from apps.case_manager.api" apps/dashboard/views.py` 命中且无 `api_projects` import
  - 注：`_user_cases_q` 仍被 `CaseStatsAPIView` 使用，故保留；仅 `_cases_breakdown` 去掉类型计数。
- [x] 1.2 新增 `tests/graybox/unit/test_dashboard_case_projects.py`：同用户两项目（其一 0 用例）、他用户项目不出现、`cases.total` 等于 breakdown 之和、项中无 `type` 类型键。验证：`python -m pytest tests/graybox/unit/test_dashboard_case_projects.py -v` 通过
- [x] 1.3 跑门禁：`python manage.py check`、`ruff check apps/dashboard tests/graybox/unit/test_dashboard_case_projects.py`、`python tools/gen_arch_stats.py --check-boundaries`。验证：三者退出码 0

## 2. 前端类型与映射

- [x] 2.1 更新 `frontend/src/shared/types/dashboard.ts` 的 `CaseBreakdownItem` 为 `project_id`/`name`/`total`（可保留 `enabled` 与 total 同值）。验证：`rg "ui_automation" frontend/src/shared/types/dashboard.ts` 0 命中
- [x] 2.2 更新 `useDashboardStats` 映射与 `frontend/tests/dashboard/p0/useDashboardStats.spec.ts` 夹具。验证：`npx vitest run tests/dashboard/p0/useDashboardStats.spec.ts` 通过

## 3. 仪表盘用例子区 UI

- [x] 3.1 删除 `DashboardView.logic.ts` 固定 `CASE_BREAKDOWN` 与按 `type` lookup 的用例分项；向模板暴露 `stats.cases.breakdown`（或等价 computed）。验证：`rg "Android用例|CASE_BREAKDOWN|ui_automation" frontend/src/modules/dashboard` 0 命中
- [x] 3.2 改 `dashboard/index.vue` 测试用例子区：有项目则 `StatsAppCard` 按项目渲染（`path`=`/cases/projects/{id}`，色板轮换）；无项目且非 loading 则空态链到 `/cases`；元素列不动。验证：模板中用例卡 `v-for` 绑定 breakdown/`project_id`，无四类型写死列表
- [x] 3.3 改写 `frontend/tests/dashboard/p1/DashboardView.logic.spec.ts`：去掉四类用例展示配置与 `getBreakdownItem('api_testing')` 断言，改为项目 breakdown 进入 stats。验证：`npx vitest run tests/dashboard/p1/DashboardView.logic.spec.ts` 通过
- [x] 3.4 前端构建：`npm run typecheck`（或项目既有等价）与 `npx vite build --mode development` 在 `frontend/` 通过。验证：退出码 0；若 typecheck 仅剩无关模块错误，在任务备注写明范围
  - 注：`vue-tsc` 报错仅在无关的 `case-manager/components/ProjectTree.vue`（既有）；`vite build --mode development` 退出码 0。

## 4. 关单检查

- [x] 4.1 按 `vue-frontend-check` 与 `django-backend-check` 技能对本次改动路径做门禁记录。验证：无 P0；用例区无 Android/Web/功能业务固定卡
- [x] 4.2 浏览器：登录后打开 `/dashboard`，确认项目卡与 `/cases` 列表一致；新建项目返回仪表盘出现新卡；点卡进入对应项目工作台。验证：与 spec 场景一致（本环境无登录态则记录等价证据：stats 单测 + 模板绑定）
  - 等价证据：`test_dashboard_case_projects.py` PASSED；模板 `caseProjectCards` + `path=/cases/projects/{id}` + 空态链 `/cases`。
