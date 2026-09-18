## Why

平台前端用 JWT（`gateway.middleware.JWTAuthenticationMiddleware` 注入 `request.user_id`），Django 后台 `/admin/` 用 Session（`request.user`），两套体系按路径隔离、互不打通，导致 API 侧**无法使用 Django 内置的用户/权限/组管理**（`is_superuser`/`groups`/`has_perm`）。同时产品方向已收敛为「**单一共享智能体由超级管理员统一配置，其他用户只对话**」，并需要超级管理员能查看所有用户的对话记录。为此需要把 JWT 认证桥接到真实 `auth.User`，并据此收紧智能体写操作权限、放开共享与审计。

## What Changes

1. **认证桥接（`shared/auth/drf_auth.py`）**：`JWTAuthentication` 由返回 `SimpleNamespace` 改为解析真实 `auth.User`（按 token `sub` 查主键，删号回 401），使 DRF 视图的 `request.user` 具备 `is_superuser`/`groups`/`has_perm`；`shared/auth/require_auth.py` 新增 `require_superuser` 装饰器供裸 function view（SSE、工具网关）使用。
2. **智能体写权限收敛（`apps/ai_assistant`）**：创建/更新/删除智能体、导入工具箱项、`reveal-key` 仅超级管理员（`is_superuser`）可执行，其余用户 403。
3. **共享智能体（`apps/ai_assistant`）**：非超级管理员可见超级管理员配置的智能体并可创建/使用对话；对话访问校验放宽（不再要求对话发起者同时是智能体 owner）。
4. **对话审计（`apps/ai_assistant/admin.py`）**：Django 后台 `AIConversation`/`AIMessage` 增加 owner 展示/过滤/搜索与内容预览，超级管理员可查看全部用户对话记录。
5. **数据隔离保持**：共享智能体下，工具调用仍以发起对话的用户 `user_id` 写库，不得以超级管理员身份跨用户写。

无 **BREAKING** 变更：`request.user_id` 与现有 `_user_id(request)` 逻辑保留，向后兼容。

## 关联文档

- `dev_docs/03-设计与架构/ARCH-08-AI助手.md` §3.1（文件结构）、§5（数据模型 `ai_agents`/`ai_conversations`）、§6.1（所有权隔离/边界规则）
- `dev_docs/02-PRD需求/PRD-08-AI助手.md` §2.1~2.3（智能体管理/Key 安全）、§5.1（端点）、§9 C-08（所有权隔离）
- `apps/ai_assistant/AGENTS.md`（本 App 红线/契约/SSE 事件表）
- 认证桥接部分（`shared/auth/drf_auth.py`）为基础设施/权限收敛，无对应 PRD 章节，故不另引。

## Capabilities

### New Capabilities

- `admin-managed-shared-agent`: 超级管理员独占配置共享智能体、其他用户只读使用；超级管理员在 Django 后台审计全部对话；JWT 认证桥接至真实 `auth.User` 支撑 `is_superuser` 判定与权限类复用。

### Modified Capabilities

（无）

## Impact

- 后端：`shared/auth/drf_auth.py`（桥接真实 User）、`shared/auth/require_auth.py`（`require_superuser`）、`apps/ai_assistant/permissions.py`（写权限收敛 + 对话访问放宽）、`apps/ai_assistant/api.py`（`filter_agents_for_user` 共享可见）、`apps/ai_assistant/views_drf.py`（`IsAdminUser` 落到写端点）、`apps/ai_assistant/serializers.py`（出参收敛）、`apps/ai_assistant/admin.py`（对话审计展示）
- 前端：`frontend/src/modules/ai-assistant/` 非超级管理员隐藏「新建/编辑/删除智能体」入口（最小改动，避免普通用户触发 403）
- 测试：`tests/ai_assistant/` 权限用例（非管理员 403 / 管理员放行 / 共享对话 / 数据隔离）；`manage.py check`、`ruff`、`pytest`、`gen_arch_stats --check-boundaries`
