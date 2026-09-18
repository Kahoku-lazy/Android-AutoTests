## Context

- 复检结论与证据见 proposal「Why」；核心是两件事叠加：`PUBLIC_PREFIXES` 豁免 JWT + 视图自身零校验。
- 用户裁定：工具网关需要内部令牌；`/api/docs`、`/api/schema/`、`/api/swagger/` 保持公开。
- 现状：仓库内**无调用方**（grep `/api/ai/tools` 仅命中白名单、视图、文档），故令牌方案不会破坏平台内链路；AgentScope 已进程内直调（不经 HTTP）。
- 现状：仓库内**无任何内部令牌/服务令牌机制**，属首次引入。

## Goals / Non-Goals

**Goals:**

- 让工具网关前缀从「无凭据即可执行工具」变为「必须持有内部令牌」，且默认（未配置令牌时）**拒绝**而不是放开。

**Non-Goals:**

- 不改工具清单、不改 Tool 执行语义、不动 `apps/ai_assistant/tools.py`。
- 不给该前缀加 JWT 要求（服务间调用不持有用户令牌；令牌即身份）。
- 不改文档端点公开策略（用户已裁定）。
- 不引入密钥轮换 / 多令牌 / 审计表（过度设计）。

## Decisions

**D1 校验放在 `gateway/` 的独立中间件，而不是三个视图里的装饰器。**
理由：公开前缀豁免与令牌校验都是「通道边界」职责，集中在 D1（`gateway/`）可避免「视图少写一个装饰器 = 静默放开」；视图保持只做工具解析与执行。
备选：装饰器 `@require_internal_token` —— 更小，但边界规则散落在视图，后续新增 `tools/` 下的路由容易漏。

**D2 令牌中间件只匹配 `/api/ai/tools/` 前缀，其余请求立即返回 `None` 放行；失败即 401、不进后续链路。**
理由：不改既有中间件顺序语义（JWT 中间件对该前缀本来就放行），新中间件独立判定。

**D3 fail-closed：`settings.AI_TOOL_GATEWAY_TOKEN` 为空 → 该前缀一律 401。**
理由：D0-5/6 的教训（fail-open 默认值）；「未配置就放开」等于把本次修复变成空修复。代价：未配置令牌的环境该前缀不可用（当前无调用方，无实际影响）。

**D4 头名 `X-Internal-Token`，比较用 `hmac.compare_digest`。**
理由：常量时间比较避免时序侧信道；头名与常见内部网关约定一致。

**D5 401 响应走项目信封 `{status: false, message: "..."}`，文案不暴露令牌是否存在/是否为空。**
理由：与 `shared/renderers` 信封一致，且不向探测者泄露配置状态。

**D6 公开端点登记（用户裁定）。**
`/api/docs`（手写 API 文档）、`/api/schema/`（OpenAPI）、`/api/swagger/`（Swagger UI）保持公开：在 `PUBLIC_PREFIXES` 行内注释写明「有意公开：API 文档面」，并在 `apps/AGENTS.md` §2 与 API 文档中登记；同时把 `apps/AGENTS.md` 的公开路径清单补全到与 `PUBLIC_PREFIXES` 一致（现仅 3 条 vs 实际 10 条）。

**D7 令牌配置落在 `config/settings.py`，与 `DJANGO_SECRET_KEY` 同级读取 `.env`。**
理由：凭据属 D0 外部资源根；`.env.example` 同步说明（含生成方式）。

## Risks / Trade-offs

- [外部/历史调用方未带令牌 → 401] → 已在 proposal 标 BREAKING；仓库内无调用方可改，文档给出调用示例与生成命令。
- [令牌写进 `.env` 明文] → 与 `DJANGO_SECRET_KEY` / `DB_PASSWORD` 同级（`.env` 已 gitignore，`.env.example` 只放占位）；不在本次引入密钥管理设施。
- [新中间件导致 CORS 预检被 401 拦] → 令牌中间件必须排在 `corsheaders.CorsMiddleware` **之后**，保证 OPTIONS 预检先被处理；tasks 里显式加一条预检验证。
- [忘记给新路由加保护] → 中间件按前缀统一保护，`tools/` 下新增路由自动受保护（这也是 D1 的理由）。
