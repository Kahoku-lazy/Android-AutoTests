## Context

会话/聊天在 SPA 已无入口：`conversations`、`messages`、`save-message` 无任何前端调用，相关类型只被自身引用；后端仍保留 `ConversationViewSet` 与三张 `ai_` 表。产品已裁定不要该功能（见 proposal.md - Why）。

约束：`ai_execution_logs` 只剩 admin 注册、无写入方；`ai_tasks.description` / `scheduled_at` 无读写；`AIAgent.agent_scope_id` 仍被内部工具网关 `tools/agent-config/{id}` 用于回退查找，**不属于**本次删除范围。

## Goals / Non-Goals

**Goals:**

- 会话/聊天在代码、路由、数据三层同时下线，不留下「代码删了表还在」的半吊子状态。
- 前端类型与后端 DTO 一起收敛，避免类型层继续暗示能力存在。
- 保持 `manage.py check` / `makemigrations --check` / ruff / arch 门禁全绿。

**Non-Goals:**

- 不删除 `ai_intent_routing`、`ai_multi_agent_orchestration`、`ai_agent_model_config` 等已经无实现的历史 spec（属独立的 spec 债清理）。
- 不移除内部工具网关 `/api/ai/tools/*` 与 `AIAgent.agent_scope_id`。
- 不重排整册接口文档的章节编号（只摘除会话条目并标注下线）。

## Decisions

**D1 物理 DROP 三张表，不做归档表、不做软删。**
备选：保留表只删代码。否决理由：产品确认功能不要，保留空表会让「还有聊天数据」的错觉长期存在，也让后续迁移继续背着三张表；仓内无读取方，历史数据无业务用途。用户已明确选择「连表一起 DROP」。

**D2 `ConversationStatus` 随模型删除；`MessageRole` 保留但去掉涉表注释。**
`MessageRole.USER` 仍被模型探测 `_probe_chat` 用作请求体角色；删它要顺手改探测代码，收益低。`MessageRole` 的 docstring 不再声称对应 `ai_messages.role`。

**D3 前端整簇删除会话类型，而不是逐个保留。**
`ContentBlock`/`ChatMessage`/`ToolCall`/`SSERound`/`Hitl*` 等仅被 `ai.ts` 内部互相引用（已 grep 证实），一并删除可避免残留类型继续被误用。

**D4 两个恒空端点与 `fetchAvailableSkills` 一并删除。**
`GET /api/ai/tasks/`、`GET /api/ai/available-skills/` 恒返空且无调用方；留着只会出现在 OpenAPI 里误导调用方。

**D5 文档只做「摘行 + 标下线」，不整册重编号。**
接口文档章节号被多处交叉引用，整册重排风险高于收益；本次移除会话表格行与两组小节内容，并在原章节位置保留「已下线」说明。

**D6 迁移只生成、不自动执行。**
删表不可逆，`migrate` 交由部署者显式执行；本单只保证 `makemigrations` 产物正确、`makemigrations --check` 通过。

## 模块防火墙自检

- 跨 App import：删除的是本 App 内部符号；`models/constants.py` 仅移除一个枚举与一个映射键，未新增依赖。
- 禁止跨 App import service/runner：未触碰。
- 写库收敛：删除的写函数本就没有调用方；剩余写操作仍全部经 `apps/ai_assistant/api.py`。
- 前端不直连数据库：仅删共享类型，未改请求链路。
- 数据面：三张 `ai_` 表由本 App 自己的迁移删除，不涉及他 App 表。

## Risks / Trade-offs

- [删表不可逆，历史会话数据永久丢失] → 用户已确认不要该功能；迁移不自动执行，部署前可自行备份 `ai_conversations` / `ai_messages`。
- [仓外调用方仍可能请求会话端点] → 平台无外部集成，文档同步标注下线；端点删除后返回 404，属预期。
- [误删仍被使用的类型] → 删除前对前端类型做过全量 grep（仅 `ai.ts` 自引用）；删除后跑前端构建校验。
- [文档与代码再次漂移] → 本单只摘会话相关条目，其余历史漂移（model-debug / HITL）不在本单扩大处理。

## Migration Plan

1. 合并代码与迁移文件；
2. 备份或确认无需保留 `ai_conversations` / `ai_messages` / `ai_execution_logs`；
3. 重启前执行 `python manage.py migrate ai_assistant`；
4. 回滚：恢复代码后用备份重建三张表（迁移本身不可逆）。

## Open Questions

无。
