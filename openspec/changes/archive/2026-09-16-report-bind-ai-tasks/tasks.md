## 1. 后端列表聚合

- [x] 1.1 将 `filter_agents_for_user` 加入 `apps.ai_assistant.api` 的 `__all__`，并用现有助手可见性单测或一条最小断言确认导出可用
- [x] 1.2 在 `report_generator` 增加只读查询辅助（禁止写 ORM）：按用户可见 `AITask` 填 `runs`/`summary`/`trend`，成功口径 `completed`/`success`、失败 `failed`；`list_reports` 改为调用该辅助。`python manage.py check` 与 `ruff check apps/report_generator apps/ai_assistant/api.py` 通过
- [x] 1.3 补 `GET /api/reports` 测试：有任务时返回对应行与 KPI；无任务时仍为空壳趋势；pending 不计入 pass/fail；设备展示 label 优先。`pytest` 覆盖该测试路径通过

## 2. 前端工作台

- [x] 2.1 报告列表列改为任务 ID/设备/任务名称/创建人/状态/耗时/时间；任务 ID 纯文本；删除 `openReport`/`openCaseBreakdown` 及 KPI 点击。`npm run typecheck`（或项目等价）通过
- [x] 2.2 更新页头 subtitle、筛选占位（任务 ID）、空态 hint 指向 AI 助手且不提执行引擎；去掉迭代/用例分解展示。相关 `constants.ts` 与 `index.vue` 文案与模板一致

## 3. 关单

- [x] 3.1 同步 `apps/report_generator/AGENTS.md` 与 `frontend/src/modules/report-generator/AGENTS.md`：列表数据源改为 `AITask`、本页不跳转详情；与实现一致
- [x] 3.2 `python tools/gen_arch_stats.py --check-boundaries` 通过；报告模块无跨 App service import、无写 `ai_tasks`
