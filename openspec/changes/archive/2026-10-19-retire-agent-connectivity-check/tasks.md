## 1. 前端卡片与页面

- [x] 1.1 `AgentRouteCard.vue`：删除连通徽标（第三行）、「校验」按钮、`testing` / `routeStatus` props 与 `test` emit，以及三态相关计算与样式；胶带色固定为青绿；验证：卡片只剩名称 / 职责两行 + 配置按钮
- [x] 1.2 `index.vue`：不再向卡片传 `testing` / `route-status`，不再绑定 `@test`，不再解构健康相关状态；验证：`npm run build` 通过
- [x] 1.3 `index.logic.ts`：删除 `checkAgentsHealth` / `testAgent` 调用、`healthResults` / `routeTestResults` / `routeConnStatus` / `testingRoute`、探测相关函数与定时器，以及未使用的状态辅助函数；验证：全仓 grep 这些名字零命中

## 2. 前端 API 与类型

- [x] 2.1 `api/agents.ts`：删除 `checkAgentsHealth` / `testAgent` / `detectModels` 与相应类型引用；验证：全仓 grep 三个函数名零命中
- [x] 2.2 `shared/types/ai.ts`：删除 `RouteConnStatus` / `RouteHealth` / `AgentTestResponse` / `RouteModelTestResult` / `AgentHealthResponse` 与 `RouteConfig.health`；验证：`npm run typecheck` 无报错
- [x] 2.3 重写 `tests/ai-assistant/p0/AgentRouteCard.spec.ts`：断言两行身份、无状态徽标、底栏只有配置；验证：该文件 4 条用例全绿

## 3. 后端端点与字段

- [x] 3.1 `views_drf.py`：删除 `AgentViewSet.test` / `.models`、`AgentHealthAPIView`、`ModelDetectAPIView` 与全部探测辅助/常量，更新模块 docstring；验证：`ruff check apps/ai_assistant/views_drf.py` 通过
- [x] 3.2 `urls.py`：删除 `agents/health/` 与 `models/detect/` 路由及 import；验证：`python manage.py check` 通过
- [x] 3.3 `api.py`：删除 `update_agent_connectivity` / `update_route_connectivity` / `get_route_model_config` 与 `__all__` 条目；验证：全仓 grep 三个函数名零代码命中
- [x] 3.4 `models.py`：删除 `is_connected` / `last_checked_at` / `available_models`；`serializers.py` 同步收缩详情与列表输出；验证：`manage.py check` 通过
- [x] 3.5 生成迁移 `0057_retire_agent_connectivity_check`；验证：`makemigrations --check --dry-run` 输出 `No changes detected`

## 4. 文档与门禁

- [x] 4.1 更新 `frontend/src/modules/ai-assistant/AGENTS.md`：卡片改为「名称 / 职责」两行 + 仅配置，删除校验与三态描述；验证：文档不再出现卡片校验/三态描述
- [x] 4.2 `python manage.py check` + `makemigrations --check` + `ruff check/format apps/ai_assistant` 通过
- [x] 4.3 `pytest tests/arch -q` → 24 passed；`gen_arch_stats --check-boundaries` 零违规
- [x] 4.4 前端 `npm run build` 通过；`npm run typecheck` 通过；`npm run test` 为 416 passed / 1 failed（仅既有 `TaskInputPanel` 断言）
