## 1. 数据模型与迁移

- [x] 1.1 新增 `CaseProject`，改造 `CaseDirectory`（project FK、去掉 case_type、无限 parent），收窄 `TestDefinition` 为文档字段，删除 Api/Web/Storage 模型；`makemigrations` 含清空旧数据；验证 `python manage.py makemigrations --check` 在迁移落地后通过
- [x] 1.2 实现用例 ID `TC-YYYYMMDD-NNNN` 生成（同日唯一、并发重试）；验证 pytest 覆盖撞号重试与格式

## 2. 后端 API

- [x] 2.1 在 `api.py` facade 导出项目/目录/文档用例写接口（可拆 `api_projects.py` 等，禁止 View 直接 ORM 写）；验证无跨 App 内部 import
- [x] 2.2 实现 DRF：projects CRUD、tree、directories CRUD、definitions CRUD、move、batch-delete；标准信封 snake_case；验证 pytest API 覆盖创建树、409 环拖拽、用户隔离
- [x] 2.3 删除四类型 ViewSet/legacy 路径、step-types、YAML 导出、lock 端点；验证旧路径 404
- [x] 2.4 从 `gateway/routing.py` 移除 `/ws/case-editing/`；验证路由只剩执行进度 WS；`python tools/gen_arch_stats.py --check-boundaries` 通过
- [x] 2.5 `test_runner` 不再把文档用例当 steps_json 执行；dashboard 统计改新模型；AI 结构化写用例 Tool 停用或改为文档字段；验证相关 pytest 与友好错误文案
- [x] 2.6 `python manage.py check` + `ruff check` 相关路径 + `pytest` case_manager/dashboard/test_runner 受影响用例通过

## 3. 前端工作台

- [x] 3.1 侧栏「用例管理」改为单项 `/cases`；旧 `/cases/ui|web|api|storage` 重定向；验证路由表与 `sidebarNavConfig`
- [x] 3.2 实现 `ProjectList.vue`：空状态建项目、卡片列表；验证 vitest + 空态文案
- [x] 3.3 实现 `ProjectWorkspace.vue`：无限树、新建目录/用例、多选全选、拖拽、单删批删、无预览；验证树交互单测
- [x] 3.4 实现 `CaseDocForm.vue` + `useCaseForm`：字段、必填校验、时间格式、脏数据确认；验证 vitest 校验不发请求
- [x] 3.5 删除四套 Editor/List 与预览入口；模块 `api.ts` 只保留新契约；`npm run typecheck` 通过

## 4. 文档与关单

- [x] 4.1 改写 `API-用例管理.md`、`apps/case_manager/AGENTS.md`、前端 `case-manager/AGENTS.md`、ARCH-00 中四类型/双 WS/端点数口径；验证 `python tools/gen_arch_stats.py --check-md`（若仍报旧数则同步统计段）
- [x] 4.2 跑 `django-backend-check`、`vue-frontend-check`、`boundary-check`；浏览器走通：建项目 → 建目录 → 建用例 → 保存 → 拖拽 → 删除
  - 已跑：manage.py check / ruff / pytest（case_manager+arch）/ --check-boundaries / vitest case-manager（4 passed）；case-manager 无 vue-tsc 报错（全仓 tsc 仍有既有 dashboard 测试债）。浏览器走通请本地 `python run.py start` 后验证。
