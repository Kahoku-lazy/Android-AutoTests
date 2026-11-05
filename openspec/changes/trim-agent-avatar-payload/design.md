## Context

实测（本机真实数据，20 个任务、2 个智能体）：

- `GET /api/ai/agents/`：13,114,611 B，序列化 106ms，HTTP 1.6–5.5s；
- `GET /api/tasks/`：22 条 SQL，其中 `select_related("agent")` 那条 **1387ms**（每行任务都带上 6.5MB avatar + 6.5MB route_configs）；
- `ai_agents`：id=10 的 `avatar` 与 `route_configs.device_control.avatar` 各 6,556,854 字符；
- 前端已统一使用 `public/agent-avatar.svg`，`agent.avatar` / 线路 avatar 无任何渲染用途。

## Goals / Non-Goals

**Goals:**

- 两页加载从「秒级 + 十几 MB」降到「百毫秒级 + KB 级」。
- 接口其余字段与页面渲染零变化。
- 用测试锁住「响应体积」与「SQL 条数」，并清理存量脏数据。

**Non-Goals:**

- 不做头像上传/存储能力（当前 UI 已固定内置图标）。
- 不改任务详情报告与仪表盘。
- 不做通用缓存层。

## Decisions

**1. 直接不下发头像，而不是改成 URL。**

前端所有头像位都写死静态 SVG，`AgentRecord.avatar` 无人读取；改成 URL 反而要新增媒体路由与前端加载逻辑。列表与详情都去掉 `avatar` 与 `route_configs.*.avatar`，`route_configs` 只保留 name 与三个角色的模型信息。

**2. 用数据迁迁移清理存量，并在写入侧卡长度。**

清理放在 RunPython 里可重复执行：`avatar` 超 4096 字符则置空；遍历 `route_configs` 把每个线路的 `avatar` 同样处理。写入侧在 `AgentInputSerializer.avatar` 上加 `max_length=4096`，避免以后再写进 6.5MB。选择迁移而不是一次性脚本，是因为其它环境（CI/测试库/同事机器）同样需要这份清理，且归档后可追溯。

**3. 任务列表不联表，线路名用 SQL 侧 JSON 提取。**

`select_related("agent")` 换成先取任务列、再用一次查询按 agent id 取线路名。线路名用 Django 的 `KeyTextTransform` 组合出 `route_configs->device_control->name`（MySQL/SQLite 均支持），这样即使 route_configs 里再有历史大字段也不会被读进内存。

**4. 附件批量取。**

`prefetch_related("file_attachments")` 后 `_attachment_names` 继续用 `task.file_attachments.all()`，N+1 变 1 条。

**5. 轮询守卫放前端 composable。**

`useTaskList` 用 `inFlight` 标记跳过重叠轮询，间隔 5s → 10s；与仪表盘同一套做法，避免慢请求越堆越慢。

## 模块防火墙自检

- 跨 App：`task_list` 读 `ai_assistant` 仍只经 Model + `api.filter_agents_for_user`，本变更新增的线路名查询直接在 `task_list` 内用 `AIAgent.objects` 完成，属既有允许的只读 Model 路径；未 import views/service。
- 写库：头像清理是数据迁移（`ai_assistant` 自己的迁移），写入路径仍经 `api.py`。
- 前端：只改类型与轮询，不直连数据库。

## Risks / Trade-offs

- [去掉响应字段导致其它消费方拿不到头像] → 全仓 grep 确认无消费方；类型里字段改为可选，缺失不报错。
- [迁移清空头像不可逆] → 只清长度 >4096 的值（本来就是误写入），且名称/线路名等不受影响；反向迁移留空操作并在注释说明。
- [KeyTextTransform 在测试库（SQLite）不可用] → 单测直接跑该查询，若失败退回 `.only("id","name","route_configs")` 的一次性读取。
- [OpenAPI 基线变化] → 重新生成 `openspec/openapi.yaml` 并随提交更新。

## Migration Plan

1. 先上后端（字段下线 + 数据迁移 + 任务列表查询），前端无需改动即可变快。
2. 再上前端轮询守卫与类型可选。
3. 回滚：迁移不可逆但只影响脏数据；接口字段回滚需同时恢复前端类型（当前前端本就不读）。
