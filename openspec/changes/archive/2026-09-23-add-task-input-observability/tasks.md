## 1. 后端读侧字段

- [x] 1.1 `apps/ai_assistant/api.py` 的详情序列化增补 `planner_input`（调用既有规划输入构造函数派生，不复制实现）与 `attachment`（附件解析正文全文），空附件时均为空字符串。验证：`python -m pytest tests/graybox/unit/test_ai_task_title_attach_dispatch.py -q` 通过，且新增断言覆盖有附件/无附件两种情形
- [x] 1.2 `apps/ai_assistant/api.py` 的列表行序列化增补 `attachment_filename`，MUST NOT 下发附件正文。验证：同文件单测断言列表行含 `attachment_filename`、不含 `attachment`
- [x] 1.3 新增单测锁定「展示 == 入模」：断言详情返回的 `planner_input` 与 `engine_adapter.build_request` 取用的规划输入完全一致（同源派生），并断言无附件时四键中「附件文本内容」为空串。验证：`python -m pytest tests/graybox/unit -q` 全绿

## 2. 前端契约与类型

- [x] 2.1 `frontend/src/shared/types/ai.ts`：`TaskRecord` 增补可选 `attachment_filename`，`TaskDetail` 增补可选 `planner_input` 与 `attachment`。验证：`cd frontend && npm run typecheck` 无新增报错
- [x] 2.2 确认前端 `api/tasks.ts` 无需改动（沿用既有 `GET /ai/agent-tasks/` 与 `GET /ai/agent-tasks/{id}/`）。验证：`python -m pytest tests/graybox/unit/test_api_path_callers.py -q` 通过

## 3. 前端展示

- [x] 3.1 `TaskBoard.vue` 卡片 meta 追加「附件」一行：有附件显示文件名（单行省略号截断），无附件显示「—」；样式复用既有 `task-card__meta` 令牌，不新造字号与颜色。验证：`cd frontend && npm run lint && npm run build` 通过，页面肉眼确认卡片不换行撑高
- [x] 3.2 `TaskDetailPage.vue` 在 KPI 与步骤分栏之间新增两个默认收起的折叠区块：「送给规划模型的输入」（预格式展示四键 JSON）与「任务附件」（文件名 + 正文全文，展开后定高滚动）。验证：`cd frontend && npm run build` 通过；页面展开后正文溢出发生在区块内部，页面整体布局不被撑破
- [x] 3.3 无附件/无规划输入的历史任务显示空态文案，不出现 `undefined` 或空白区块。验证：打开一条无附件的旧任务详情，肉眼确认

## 4. 门禁与验收

- [x] 4.1 后端门禁：`python manage.py check` 0 issues + `ruff check` / `ruff format --check`（apps/ai_assistant）+ `python tools/gen_arch_stats.py --check-boundaries` 零违规。验证：命令逐条通过
- [x] 4.2 前端门禁：`cd frontend && npm run typecheck && npm run lint && npm run build` 通过
- [x] 4.3 端到端自证：新建一条**带 Word/PDF 附件**的任务，任务详情展开「送给规划模型的输入」，把界面上的四键 JSON 与「任务附件」正文同屏比对，确认正文与「附件文本内容」一致、四键值与表单填写值一致。验证：肉眼比对 + 截图留档
- [x] 4.4 回归：既有任务发布类单测全绿（`python -m pytest tests/graybox/unit -q`），确认四键契约、调度与执行链路零行为变更
