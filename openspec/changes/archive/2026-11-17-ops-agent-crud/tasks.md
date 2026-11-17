## 1. 写权限与可见性

- [x] 1.1 `backend/apps/ai_assistant/views_drf.py` 的创建、更新、删除由 `is_superuser` 改为 `is_operator`。更新和删除仍先确认记录存在：不存在 404，存在但调用者不是运营 403。验证：`tests/ai_assistant/` 新增用例覆盖运营 201、普通用户 403、不存在 404。
- [x] 1.2 `filter_agents_for_user` 改为有登录身份即返回原查询集，无身份返回空集。详情对已登录用户不再按归属返回 403。验证：普通用户列表包含运营刚创建的智能体；不存在的详情返回 404。
- [x] 1.3 `create_agent` 不再把 `user_id` 写入 `owner_id`，新建记录归属为空。验证：创建后的 `owner_id` 为空，且另一个普通用户的列表能看到它。

## 2. 运营页

- [x] 2.1 运营栏增加「智能体」，路由 `/ops/agents`，守卫与用户管理相同。验证：运营侧栏可见；普通用户直接打开回到工作台且不发写请求。
- [x] 2.2 页面提供列表、新建、编辑、删除。表单只有名称、头像、标签、描述，HTTP 打既有五个 `/api/ai/agents/` 路径。验证：`cd frontend && npx vue-tsc --noEmit` 通过。
- [x] 2.3 删除前 `ElMessageBox` 确认，文案写明会一并删除该智能体下的任务；取消不发请求。验证：前端测试覆盖确认取消不调用删除接口。

## 3. 契约与收尾

- [x] 3.1 若 OpenAPI 基线未包含这五个路径或描述仍写「仅超管」，随代码更新 `openspec/openapi.yaml`。验证：`python utils/check_gates.py --only openapi-schema,openapi-coverage` 通过。
- [x] 3.2 后端回归：`tests/ai_assistant/api/test_roles.py` 中智能体相关 10 项通过（运营可创建且 owner 为空、普通用户 403、全员可见、不存在 404）。
- [ ] 3.3 人工验收：运营新建一条后，用普通账号打开任务发布，下拉中能看到它；普通账号打创建接口返回 403；运营删除前能取消。

> **2026-11-17 归档**：按需求方决定直接归档，未完成项不再执行；本次 delta 因 MODIFIED 头部缺失未合并，delta 原文保留在本目录 specs/ 下。
