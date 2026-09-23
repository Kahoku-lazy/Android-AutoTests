## 1. 后端活动聚合与分页

- [x] 1.1 在 `DashboardActivitiesAPIView` 合并当前用户可见 `AITask`（`type=run`）与 `AIAgent` 更新（`type=agent`），各源最多 100 条、合并按 `time` 倒序再截 100；禁止查询已删除的 `TestRunRecord`。验证：`python manage.py check` 通过
- [x] 1.2 为 `GET /api/dashboard/activities/` 增加 `limit`（缺省 10、最大 50）与 `offset`（缺省 0）；非法值 HTTP 400 且有明确 `message`；默认无参仍返回至多 10 条数组信封。验证：`ruff check apps/dashboard` 通过
- [x] 1.3 新增 graybox 单测覆盖：默认 10 条、`offset=10&limit=50` 不与首页重复、非法 `limit` 400、任务卡映射为 `run`、智能体映射为 `agent`。验证：`pytest tests/graybox/unit/test_dashboard_activities.py -q` 通过

## 2. 前端主屏十条槽与 API

- [x] 2.1 `fetchRecentActivities` 支持可选 `limit`/`offset`；仪表盘主数据仍默认无参（10 条）。验证：`frontend/src/modules/dashboard/api.ts` 类型与调用处一致
- [x] 2.2 `ActivityTimeline` 列表区用令牌化 `min-height` 固定十条槽位，主屏最多渲染 10 条，空态仍占满槽高；标题行右侧加 `DoodleBtn`「查看历史」。验证：`npx vitest run tests/dashboard/p1/ActivityTimeline.spec.ts` 覆盖空态高度、3 条不塌缩、不超过 10 条、出现历史按键
- [x] 2.3 必要时仅接线 `index.vue` / `DashboardView.style.css`，不改四章节钉板结构。验证：`npm run typecheck`（或仓库等价命令）通过

## 3. 历史弹层

- [x] 3.1 本页 `el-dialog` 打开「活动历史」，首次请求 `offset=10`；有更多则「加载更多」累加 offset；不足则空态「没有更多历史记录」；关闭后主屏十条不变、路由仍为 `/dashboard`。验证：`ActivityTimeline.spec.ts` 增加打开弹层 / 空历史 / 加载更多 用例且通过

## 4. 文档与门禁

- [x] 4.1 同步接口文档：去掉 `TestRunRecord` 口径，写明任务卡 + 智能体、`limit`/`offset`、数组信封。验证：文档与 `urls.py` / 视图行为一致
- [x] 4.2 后端关单：`python manage.py check`、`ruff check apps/dashboard tests/graybox/unit/test_dashboard_activities.py`、`pytest tests/graybox/unit/test_dashboard_activities.py tests/graybox/unit/test_dashboard_agent_tasks.py -q` 通过
- [x] 4.3 前端关单：仪表盘相关 vitest 通过；按 `vue-frontend-check` 核对布局裁剪、字号令牌、硬编码色、DRF 契约
- [x] 4.4 架构边界：`python tools/gen_arch_stats.py --check-boundaries` 通过（dashboard 只读 Model + `filter_agents_for_user`，无写库）
