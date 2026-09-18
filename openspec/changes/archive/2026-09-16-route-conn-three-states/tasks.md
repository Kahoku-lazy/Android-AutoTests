## 1. 后端两段探测与三态落库

- [x] 1.1 重写 `_test_model_config`：list 2xx 只置 `key_ok`；配置齐全时始终发极短 chat；`connected` 仅 chat 2xx；list 含 id 但不含 `model_name` 则不可用。用 pytest 覆盖 list 成功+chat 402、list+chat 均 2xx、list/chat 401（`tests/graybox/unit/`，`pytest` 相关路径通过）
- [x] 1.2 线路探测按相同 `(provider, base_url, api_key)` 合并 list，按角色 `model_name` 分别 chat；聚合 `ready`/`unusable`/`offline`（三角色均推理成功才 `ready`）。pytest 覆盖 402→unusable、三角色成功→ready、全未配置/全 401→offline
- [x] 1.3 `update_route_connectivity` 写入 `health.status`；`is_connected` 仅 `ready`；`_health_is_stale` 在缺 `status` 时视为过期。Serializer / `_public_route_health` / `POST .../test` / `GET .../health` 返回 `status`。`python manage.py check` + `ruff check apps/ai_assistant` 通过

## 2. 前端三态徽标

- [x] 2.1 更新 `RouteHealth` / `RouteModelTestResult` / `AgentTestResponse`：`status`、`key_ok`。`AgentRouteCard` 只渲染三态文案（已连通可执行任务 / 秘钥已连接但无法使用 / 连接失败小助手断线），删除「未检测」；探测中显示「校验中…」。`index.logic.ts` 水合 `health.status`；`AgentDetail.vue` 角色行对齐 `key_ok`/`connected`
- [x] 2.2 同步 `frontend/src/modules/ai-assistant/AGENTS.md` 看板连通口径。前端相关单测或组件断言覆盖三态文案；`npm run build` 能编过卡片改动

## 3. 关单校验

- [x] 3.1 跑 `python manage.py check`、`ruff check`（改动路径）、相关 pytest；需要时 `python tools/gen_arch_stats.py --check-boundaries`。确认不新增跨 App 内部 import、写库仍走 `api.py`
