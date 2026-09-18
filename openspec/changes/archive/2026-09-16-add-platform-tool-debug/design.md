## Context

动机见 `proposal.md` Why。现状：12 个平台工具在 `apps/ai_assistant/tools.py` 的 `TOOLS` / `TOOL_META`；智能体经 AgentScope `PlatformFunctionTool` 进程内直调。管理端 `GET /api/ai/available-tools` 只给 name/summary/icon/read_only/enabled，无入参。`POST /api/ai/tools/{module}/{action}` 是 JWT 豁免的内部网关（`X-Internal-Token`），ARCH §1.4 通道 ① 禁止 SPA 使用。装配台 `ToolboxPanel` 无调试入口。Skill 已有 L2：`/ai-assistant/toolbox/skills/:name` + `WorkbenchCrumbs`。`views_drf.py` 已超 views 行数上限。写库仍只发生在各业务 App `api.py`（工具函数内部），本变更不新增 `ai_*` 表。

## Goals / Non-Goals

**Goals:**

- JWT schema + invoke，调用与智能体同一批 `TOOLS` 函数
- 前端 L2 调试页：动态表单、只读直跑、写操作确认、截图预览
- 权限：登录读 schema / 跑只读；超管才能跑写工具

**Non-Goals:**

- 不改内部网关鉴权模型，不把令牌暴露给前端
- 不经 AgentScope 发任务、不加 WS
- 不覆盖自定义 Skill / 设备提示词
- 不为每个工具手写专用表单
- 不把调试调用记入任务板

## Decisions

### D1 新 JWT 路径，不复用内部网关

- 选择：`GET /api/ai/platform-tools/<name>`（schema）、`POST /api/ai/platform-tools/<name>/invoke`（body = 工具 kwargs 的 JSON 对象，可为空 `{}`）
- 理由：路径落在 `/api/ai/platform-tools*`（已有 toggle），与 `/api/ai/tools/` 内部前缀隔离，避免中间件 JWT 豁免
- 备选：SPA 打内部网关 — 违反通道 ① / 令牌模型；把 invoke 做成 `available-tools` 的 action — 与列表 GET 混在一起，鉴权分支难测

### D2 schema 从函数签名推导，剥掉 `user_id`

- 选择：`inspect.signature` + 注解映射 `str/int/float/bool`；无默认值且非 `user_id` 为 required；`user_id` 永不出现在 schema
- 理由：与 AgentScope `FunctionTool` 从类型注解推导 input_schema 同源；12 个工具参数均为简单类型
- 备选：手写 JSON Schema 表 — 与 docstring 双份维护；把 AgentScope schema 从引擎 import 到 Django — 上层碰引擎包装，越界

### D3 按名分发放在 `tools.py`，视图只鉴权分发

- 选择：`get_tool_debug_schema(name)` / `invoke_platform_tool(name, user_id, params)` 与现有 `TOOLS` 同文件；未知名抛约定错误供视图转 404。视图新建 `views_tool_debug_drf.py`，不堆 `views_drf.py`
- 理由：网关已是 `handler(user_id=..., **body)`；调试应同一分发。本 App 无新 ORM 写，不必硬塞 `api.py`
- 备选：invoke 进 `api.py` — 无表可写，变成空壳；视图内直接 `TOOLS[name][0](...)` — 鉴权与分发缠在一起，单测要抬 HTTP

### D4 写工具权限以后端为准，确认框只在前端

- 选择：`TOOLS[name][1] is False` 时 `_is_superuser`，否则 403。前端 `ElMessageBox.confirm`（已有删除确认模式）；取消则不 `POST`
- 理由：API 可被直接打，确认框不能当鉴权
- 备选：后端再收 `confirmed: true` — 无增量安全，徒增契约

### D5 额外字段拒绝，身份字段丢弃

- 选择：params 先 `pop("user_id")`；其余键若不在签名中则 400；按注解做简单类型转换（表单常把数字变成字符串）
- 理由：模糊入参拒绝猜测（项目代码规范）；避免把未知键喂进 `**kwargs`
- 备选：忽略未知键 — 调用者以为生效实际丢了，更难排查

### D6 结果形状与工具函数一致，截图由前端特判

- 选择：invoke 返回工具原结果（str JSON 则 parse 成对象，与网关 `_normalize_tool_result` 同语义）。`screenshot_page` 仍为 `{image: {base64, media_type}, summary}`；前端用 `img` 预览，JSON 区只展示 `summary`（或折叠 image）
- 理由：与智能体看到的 payload 一致，调试才有意义
- 备选：invoke 改成只返回 URL — 要另做媒体接口，超出范围

### D7 前端路由与 Skill 查看器同构

- 选择：`/ai-assistant/toolbox/tools/:toolName`；`WorkbenchHeader` + `WorkbenchCrumbs` `back-to=/ai-assistant/toolbox`；装配台 `.pt-tool-head` 加调试按钮（所有登录用户可见）
- 理由：已有 L2 模版与 tokens；不新造第三套子页壳
- 备选：抽屉 — 写确认、大 JSON、截图预览会挤爆目录

## 模块防火墙自检

- 跨 App import：调试调用只进现有 `tools.py` 函数，后者已调各 App `api.py`（及设备引擎，与现行 Tool 相同）；本变更不新增跨 App service/runner/consumer import
- 写库：无新 `ai_*` 表；设备锁/截图等副作用仍走既有 `device_pool` / `device_inspector` api
- 引擎：Django 不 import `engines.ai.agentscope.tool_wrapper`；不改 AgentScope 装配
- 前端：只走 `djangoClient` `/api/ai/platform-tools/<name>` 与 `.../invoke`；禁止 `/api/ai/tools/`
- 无新 WS 生产点

## Risks / Trade-offs

- [写工具调试即真实锁设备/点屏幕] → 超管 + 二次确认；页上标明只读/写
- [截图 base64 撑满响应] → 契约保持与 Agent 一致；UI 不把编码当正文；超时沿用现有 REST
- [签名推导漏掉 docstring 枚举约束（如 action 取值）] → schema 带 summary；非法值仍由工具 `ValueError` → 400
- [停用工具仍可调试] → 刻意：验返回与「交给助手」解耦；文档写明
- [views 再膨胀] → 独立 `views_tool_debug_drf.py`

## Migration Plan

无数据迁移。部署后新路由即用；回滚删除路由与前端入口即可，不影响任务执行。

## Open Questions

无。停用仍可调、非超管写页只读、schema 路径与 invoke 同前缀，均已在探索中拍板。
