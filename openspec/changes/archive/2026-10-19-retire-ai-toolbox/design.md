## Context

AI 工具箱只剩两个来源（平台业务工具、自定义 Skill），无线端口与日志关键词已迁到独立「串口日志」页。SOP 的工具集由 `engines/agents/tools_config.py` 固定装配，装配台开关从未影响任务执行；`apps/ai_assistant/tools.py` 的平台工具、`skills_catalog.py`、内部工具网关 `/api/ai/tools/*` 都只服务这套 UI。产品决定整体删除（见 proposal.md - Why）。

## Goals / Non-Goals

**Goals:**

- 侧栏 AI 助手收为单一入口，点击直达 `/ai-assistant/agents`，不再有子项与页内 Tab。
- 工具箱在代码、路由、数据三层同时下线，不留下无入口的后端能力。
- 去掉一条免 JWT 前缀（`/api/ai/tools/`）及其内部令牌中间件，缩小攻击面。
- 保持 `manage.py check` / `makemigrations --check` / ruff / arch / 前端构建全绿。

**Non-Goals:**

- 不删除引擎侧工具（`engines/agents/tools/*`）与 Skill 目录装配；SOP 行为不变。
- 不动已迁出的「串口日志」页与其 API（`log-ports`、`log-keywords`）。
- 不处理 `device-log-keyword-catalog` / `device-log-port-console` 两份 spec 中「工具箱入口」的表述——它们由在途的 `serial-log-module` 单负责收口。
- 不重排接口文档全册章节号。

## Decisions

**D1 侧栏用「无 children 的普通导航项」，而不是保留分组再隐藏子项。**
`AppSidebar` 对无 `children` 的项渲染普通 link，`isActive` 以 `/ai-assistant` 前缀匹配，任务详情/智能体编辑页仍高亮；`/ai-assistant` 已有 redirect 到 `/ai-assistant/agents`。备选：保留 children 但只留一项——会留下无意义的展开箭头与子级缩进，否决。

**D2 后端 API 与前端同步删除，不保留「无 UI 的 API」。**
备选：只删前端、后端保留。否决理由：没有调用方的端点仍会进入 OpenAPI 与文档，继续制造「能力还在」的错觉；且其数据层（两张表）与 agent 开关字段会永远无人写入。

**D3 内部工具网关整条删除。**
`/api/ai/tools/*` 的唯一消费面是工具箱调试与历史外部调用；令牌默认空即 401，实际不可用。删除 `gateway/internal_token.py`、MIDDLEWARE 注册、`AI_TOOL_GATEWAY_TOKEN` 与 `PUBLIC_PREFIXES` 中的豁免前缀，减少一条免 JWT 通道。

**D4 `apps/ai_assistant/tools.py` 整体删除，接受四项能力退役。**
平台侧 `ocr_page`、`list_page_flows` / `get_page_flow`、`list_apps`，以及平台侧 `screenshot_page` / `check_device_log` 副本，都只经工具箱调试页与内部网关注入；SOP 使用引擎自带同名工具，不依赖本模块。因此删除后：OCR 与页面流查询能力退役（spec 已同步移除），包名发现退役；截图与日志检查仍由引擎工具提供。备选：把 OCR/页面流搬到引擎——无消费方，属新增能力，不做。

**D5 数据物理删除（用户已确认）。**
删 `ai_shared_tools`、`ai_platform_tools` 两表与 `AIAgent` 的 `skills_config` + 4 个 `enable_*` 字段；迁移只生成、不自动执行。

**D6 文档只做「摘章节 + 标下线」，不整册重编号。**
接口文档删除工具箱组、平台工具调试、平台配置、内部网关章节，并在总览表去掉对应行；模块 AGENTS 去掉装配台段落。

## 模块防火墙自检

- 跨 App import：删除的是本 App 内部模块；`gateway/internal_token.py` 在 gateway 层，删除后 `apps/` 不再引用。
- 禁止跨 App import service/runner：未触碰。
- 写库收敛：删除的写函数无调用方；剩余写操作仍全部经 `apps/ai_assistant/api.py`。
- 前端不直连数据库：仅删页面与类型，请求链路不变。
- 数据面：两张 `ai_` 表由本 App 自己的迁移删除。

## Risks / Trade-offs

- [删表不可逆] → 用户已确认；迁移不自动执行，可先备份 `ai_shared_tools` / `ai_platform_tools`。
- [OCR / 页面流查询 / 包名发现能力永久消失] → 已在 proposal 与 spec delta 明确；如需恢复应在引擎侧按新契约重新立项。
- [仓外调用方仍在打 `/api/ai/tools/*`] → 该网关默认 401（令牌未配置），实际不可用；删除后返回 404，文档同步标注下线。
- [两份 spec 仍写「工具箱入口」（串口日志相关）] → 归 `serial-log-module` 在途单收口，本单不碰以免冲突。
- [前端残留引用导致构建失败] → 删除后跑 `npm run build`；类型检查只认 src（既有测试漂移不在本单）。

## Migration Plan

1. 合并代码与迁移；
2. 备份或确认无需保留两张工具表；
3. 执行 `python manage.py migrate ai_assistant`；
4. 回滚：恢复代码后用备份重建表（迁移不可逆）。

## Open Questions

无。
