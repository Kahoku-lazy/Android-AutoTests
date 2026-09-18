## 1. 认证桥接（shared/auth）

- [x] 1.1 修改 `shared/auth/drf_auth.py` 的 `JWTAuthentication.authenticate`：由 `SimpleNamespace` 改为 `User.objects.get(pk=int(payload["sub"]))` 返回真实 `auth.User`，`User.DoesNotExist` 抛 `AuthenticationFailed`；验证 `python manage.py check` + `ruff check shared/auth/drf_auth.py` + 相关鉴权单测通过
- [x] 1.2 在 `shared/auth/require_auth.py` 新增 `require_superuser` 装饰器（sync/async 双支持，读 `request.user_id` → `User.is_superuser`）；验证 `ruff check shared/auth/require_auth.py` + 同步/异步两种单测通过

## 2. 智能体写权限收敛与共享（apps/ai_assistant）

- [x] 2.1 `permissions.py`：`check_can_create_agent`/`check_can_update_agent`/`check_can_delete_agent` 改为仅 `is_superuser` 通过；`check_conversation_access` 去掉「agent owner==user」约束；新增「共享可见」判定；验证 `ruff check apps/ai_assistant/permissions.py` + 相关单测
- [x] 2.2 `api.py` 的 `filter_agents_for_user(queryset, user)`：超级管理员返回全量；非超级管理员返回「超级管理员拥有 ∪ 自己拥有（遗留）」；验证 `python manage.py check` + `pytest tests/ai_assistant/ -q`
- [x] 2.3 `views_drf.py` 写端点（create/update/delete/reveal-key/import-toolbox）挂 `IsAdminUser`；`serializers.py` 非超级管理员出参隐藏 `api_key`/`system_prompt`/`base_url`；验证 `pytest tests/ai_assistant/test_agents_api.py -q`
- [x] 2.4 回归 `build_agent` 链路：确认工具 `user_id` 仍为发起对话者（非管理员），补「共享智能体下写用例落本人名下」隔离用例；验证 `pytest tests/ai_assistant/test_tools_cases.py -q`

## 3. Django 后台对话审计（apps/ai_assistant/admin.py）

- [x] 3.1 `AIConversationAdmin` 增加 `owner` 到 `list_display`/`list_filter`/`search_fields`（`owner__username`）；`AIMessageAdmin` 增加会话所属用户展示与内容预览；验证 `python manage.py check` + 超级管理员登录 `/admin/` 可见全部记录并可按用户过滤/搜索

## 4. 前端最小改动（frontend）

- [x] 4.1 非超级管理员隐藏「新建/编辑/删除智能体」入口（智能体看板/详情页按 `is_superuser` 条件渲染）；验证 `npm run build` 通过 + `vue-frontend-check` 门禁

## 5. 测试与门禁

- [x] 5.1 补齐权限用例：非管理员建/改/删智能体与 reveal-key → 403；管理员放行；非管理员共享对话成功且归属自己；验证 `pytest tests/ai_assistant/ -q`
- [x] 5.2 全链路门禁：`python manage.py check` + `ruff check .` + `pytest` + `python tools/gen_arch_stats.py --check-boundaries` + `python tools/gen_arch_stats.py --check-md` 全部通过
