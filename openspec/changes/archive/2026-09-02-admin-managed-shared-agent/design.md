## Context

- 前端平台用 JWT：`gateway.middleware.JWTAuthenticationMiddleware` 仅对 `/api/*` 校验并注入 `request.user_id`（字符串），`/admin/` 在 `PUBLIC_PREFIXES` 中被跳过；Django 后台用 Session + `request.user`。
- DRF 侧 `shared/auth/drf_auth.py` 的 `JWTAuthentication` 目前返回 `SimpleNamespace(id, is_authenticated=True)`，**没有** `is_superuser`/`groups`/`has_perm`，故 `settings.py` 里虽全局挂了它，但视图无法用 `IsAdminUser` 等权限类。
- `apps/ai_assistant` 权限层现状：`check_agent_owner`（仅 owner）、`check_conversation_access`（对话 owner 且 agent owner 双重）、`check_can_create_agent`（任何登录用户）、`filter_agents_for_user`（`owner_id == user_id`）。
- `agent_factory.build_agent(agent_model, user_id)` 的 `user_id` 来自 `request.user_id`（发起对话者），已正确流转到工具，需保持不变。
- `admin.py` 已注册 AIAgent/AIConversation/AIMessage 等，但无 owner 展示与按用户过滤。

## Goals / Non-Goals

**Goals:**

- JWT 认证在 DRF 视图解析为真实 `auth.User`，使 `is_superuser`/`groups`/`has_perm` 可复用。
- 智能体写操作（建/改/删、导入工具、reveal-key）仅超级管理员可执行。
- 非超级管理员可见共享智能体并在其上对话；数据隔离仍按 `user_id` 生效。
- 超级管理员在 Django 后台查看并过滤/搜索全部对话与消息。

**Non-Goals:**

- 前端「对话审计页」（路径 2）不在本次范围。
- 不引入自定义 User / `is_ai_admin` 字段，不引入多租户 / 多全局智能体。
- 不改 SSE 与工具网关的鉴权协议（仅按需加 `require_superuser` 装饰）。
- 存量多用户自建智能体的清理/合并策略不在本次范围（另行决策）。

## Decisions

### D1：DRF 桥接返回真实 `auth.User`
`JWTAuthentication.authenticate` 由 `SimpleNamespace` 改为 `User.objects.get(pk=int(payload["sub"]))`，`User.DoesNotExist` 抛 `AuthenticationFailed`。
- 理由：一处改动使全平台 DRF 视图获得 `request.user.is_superuser`/`has_perm`/`groups`，可直接用 `IsAdminUser`。
- 备选：`is_admin(user_id)` 辅助函数逐端点判断（方案 B）——拒绝，每端点手写易漏；自定义 `is_ai_admin` 字段——拒绝，需改 User 模型，过度设计。

### D2：超级管理员判定用 `is_superuser`
统一 `request.user.is_superuser`；裸 function view 用 `require_superuser`（读 `request.user_id` → `User.is_superuser`）。
- 理由：Django 语义即「绕过一切权限」，与「admin 属于超级管理员」一致，零新增字段。
- 备选：`is_staff`——语义偏「能进后台」，不如 `is_superuser` 明确。

### D3：权限层收敛与放宽（`apps/ai_assistant`）
- `check_can_create_agent`/`check_can_update_agent`/`check_can_delete_agent` → 仅 `is_superuser` 通过。
- `filter_agents_for_user(queryset, user)` → 超级管理员返回全部；非超级管理员返回「超级管理员拥有的智能体 ∪ 自己拥有的（遗留）」。
- `check_conversation_access` → 去掉「agent owner == user」，仅保留「对话 owner == user」。
- 对话创建（`AgentViewSet.create_conversation`）由 `check_agent_owner` 改为「owner 或共享可见」。
- 写端点挂 `permission_classes=[IsAdminUser]`（或保留 `_user_id` + `check_can_*` 二选一，落地时统一走 DRF 权限类）。

### D4：敏感出参收敛
非超级管理员读取智能体详情时不返回 `api_key`（连脱敏值也不给）、`system_prompt`、`base_url`；`reveal-key` 仅超级管理员。
- 理由：共享智能体的 Key 是超级管理员资产，普通用户无查看必要；对齐安全铁律「API Key 脱敏、日志不输出」。

### D5：数据隔离保持
`build_agent`/工具链路的 `user_id` 仍取发起对话者（`request.user_id`），不改；新增回归用例断言「非管理员经共享智能体写用例落在其本人名下」。

### D6：对话审计（Django 后台）
`AIConversationAdmin` 增加 `owner` 到 `list_display`、`list_filter`、`search_fields`（`owner__username`）；`AIMessageAdmin` 增加 `conversation__owner` 展示与内容预览。Django 后台本身就是「仅管理员可进」，天然满足超级管理员审计。

## 模块防火墙自检

- `shared/auth/` 是共享层，各 App 可 import，不违反跨 App 内部实现禁令。
- 本变更仅改 `apps/ai_assistant` 内部文件（permissions/api/views_drf/serializers/admin），**不新增跨 App import**。
- 所有写操作沿用既有 `api.py`（`create_agent`/`update_agent`/`delete_agent`/`reveal_agent_key` 已在 `api.py`），无新增直接 ORM 写。
- `admin.py` 属「Django Admin → ORM（仅管理员）」白名单路径，合规。
- 未新增通信通道（SSE/JWT/HTTP 不变），未触碰 service/runner/consumer 内部实现。

## Risks / Trade-offs

- [每请求 +1 次 `auth.User` 主键查询] → 可接受；后续可按需加内存缓存；`User.DoesNotExist` 已映射 401。
- [普通用户经共享智能体触发高危写（`run_test` 占设备、`save_case` 写库）] → 保留 HITL 确认 + 写工具逐智能体 `enabled` 开关（由超级管理员决定），只读工具默认兜底。
- [共享单一凭据带来的成本/限流归属不清] → 保留 `usage_tracker`；按用户用量报表不在本次范围，后续补。
- [前端未及时隐藏入口导致 403] → 前端最小改动隐藏「新建/编辑/删除」入口 + 后端 403 兜底。
- [无数据库迁移，回滚成本低] → 桥接改动可独立回滚（改回 `SimpleNamespace`），但会失去 `is_superuser` 判定，回滚需同步撤权限收敛。
