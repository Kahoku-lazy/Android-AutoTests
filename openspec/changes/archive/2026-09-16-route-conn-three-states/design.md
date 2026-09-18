## Context

动机见 `proposal.md` Why。当前 `_test_model_config` 对 `/models`、`/v1/models` 任一 2xx 即 `connected=True`，`chat/completions` 仅在 list 完全失败且 `last_error` 为空时才走；因此密钥能列目录但推理 402 时，看板仍显示已连通。线路卡 `AgentRouteCard` 用角色 `results[].connected` 全真则「已连通」，无结果则「未检测」。`GET /ai/agents/health` 已在无缓存或超过 30 分钟时实探；缺的是探测语义与三态落库。写库已走 `api.update_route_connectivity`。

## Goals / Non-Goals

**Goals:**

- 角色级：密钥探测与推理探测分离；线路级聚合为 `ready` / `unusable` / `offline`
- 无三态缓存时进页必实探；旧布尔 health 视为过期
- 契约增量字段，布尔 `connected`/`is_connected` 收紧为 `ready`

**Non-Goals:**

- 不改任务执行引擎、不在发布前拦截 402（执行失败仍由 runner 落 `执行异常`）
- 不新增供应商 SDK；不测视觉/强模型顶层配置
- 不把余额数字展示在卡片上（失败原因留在角色 `message` / 配置页明细）

## Decisions

### D1 两段探测顺序（先 list，再 chat）

- 对每个角色：先 GET 模型列表（沿用 `/models`、`/v1/models`）。2xx → `key_ok=true`。
- 无论 list 是否列出该 `model_name`，只要已配置 `model_name`+`api_key`+`base_url`，都发起 `POST /chat/completions`（`max_tokens` 极小、单条 `"hi"`）。推理 2xx → 角色可用于执行。目录未列出只作 chat 失败时的辅助提示，不得单独否决。
- **备选**：只发 chat、不 list。否决：无法区分「密钥断」与「密钥通但不能用」（402/模型不存在），三态需要 list（或等价鉴权）成功作为 `unusable` 的前提。
- **备选**：list 成功即跳过 chat。否决：即当前缺陷。
- **备选**：目录不含模型名则跳过 chat。否决：实验/视觉模型常不在 `/models` 中，会造成有效模型误判不可用。

同一线路内相同 `(provider, base_url, api_key)` 只 list 一次，按 `model_name` 分别 chat，避免三角色重复打目录。

### D2 线路聚合

执行任务需要规划、执行、校验三角色（与 `engine_adapter.ROUTE_ROLES` 一致）。

| 条件 | `status` |
|------|----------|
| 三角色均推理成功 | `ready` |
| 至少一角色 `key_ok`，且非 `ready` | `unusable` |
| 无一角色 `key_ok` | `offline` |

未配置模型名/密钥的角色：`key_ok=false`、不可用。三角色都未配置 → `offline`。

角色结果写入 `health.results[role]`：`connected` 仅表示推理成功；增加 `key_ok`、保留 `message`。

### D3 health 契约与缓存失效

`route_configs.{route}.health` 增加 `status`（`ready`|`unusable`|`offline`）。`is_connected` 仅 `status==ready`。

`_health_is_stale`：缺 `status` 或 `last_checked_at` 过期（仍 30 分钟）即实探，从而清掉历史「list 即连通」缓存。

`POST .../test` 响应：`status`、`connected`（= ready）、`results`、`message`。`GET .../health` 线路对象同样带 `status`。

### D4 看板展示

`AgentRouteCard` 只认 `health.status`（及探测返回的同名字段）。文案固定：

- `ready` → 已连通，可执行任务（成功色）
- `unusable` → 秘钥已连接，但无法使用（警告色，复用现有暖黄/仪表盘强调）
- `offline` → 连接失败，小助手断线（危险色）

删除 `is-unknown` / 「未检测」。无缓存等待响应时徽标与按钮同为「校验中…」（过程态）。配置页角色行：`connected` 显示可用于执行；`key_ok && !connected` 显示密钥可达但不可用及 `message`。

### D5 超时与费用

单次 HTTP 超时保持现有量级（可略降 chat 超时以免三角色串行过长）。探测会消耗极少 token，且可能因 402 失败——这是有意的。不引入计费查询专用 API（供应商不统一）。

## 模块防火墙自检

- 跨 App import：本变更只改 `ai_assistant` 与前端 `ai-assistant`；探测继续用 `requests` 打外部 LLM，不 import 他 App `service/runner`
- 写库：health 仍经 `api.update_route_connectivity` / `update_agent_connectivity`，View 不直接 ORM 写
- 前端只走 `djangoClient` → `/api/ai/agents/...`，不直连数据库
- 不新增 WS / SSE

## Risks / Trade-offs

- [进页实探变慢 / 供应商限流] → 同密钥合并 list；TTL 30 分钟仍跳过未过期且已有 `status` 的线路；手动「校验」始终实探
- [探测本身触发 402 或扣费] → 仅 `max_tokens` 极小的 chat；失败则落入 `unusable`，与任务执行同一信号
- [部分供应商无 `/models`] → 仍发 chat；若 chat 401/网络失败且 list 也失败 → `offline`；若 chat 402 且 list 失败，无法证明密钥曾成功，按聚合规则归 `offline`（不把 402 单独当 key_ok）。若供应商 chat 402 同时 list 不可用，卡片会显示断线而非「密钥已连接」——接受该边界
- [旧前端只读 `connected`] → 布尔收紧后不会再把 402 场景标成已连通；未升级的配置页成功 Toast 变严，符合预期

## Migration Plan

1. 后端先写 `status` 再改前端；缺 `status` 的缓存自动实探，无需数据迁移脚本
2. 回滚：恢复 list-only 探测与旧三态文案；JSON 多一个 `status` 字段可忽略

## Open Questions

无。进页策略已确认为方案 A。
