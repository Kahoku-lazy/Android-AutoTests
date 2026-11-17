## Why

平台只有「超级管理员 / 普通用户」两档身份：停用一个离职账号、给忘记密码的同事重置密码，今天只能由超管登录 Django Admin 直接改库——没有业务规则校验、没有操作留痕，运营也无法自助完成。需要一个只做用户管理的最小运营后台，把这两件事从「改数据库」变成「点按钮」。

## What Changes

- 新增「运营」身份：用 Django 内置用户组 `运营` 表示（`auth_group` 已存在，零迁移；不改 `is_staff`、不新增用户表）。超管自动拥有运营的全部权限。
- 新增后端应用 `backend/apps/ops_console`，提供 `/api/ops/users/*` 四个端点：列表、停用、启用、重置密码（统一 `{status, data}` 信封，路径带尾斜杠）。
- 权限边界：运营可查看全部用户、可停用/启用**普通用户**、可重置**普通用户**密码；MUST NOT 修改超级管理员或其他运营、MUST NOT 授予/取消运营、MUST NOT 删除账号、MUST NOT 停用自己。
- 重置密码 = 服务端生成一次性随机密码，仅在本次响应里返回一次；不接入邮件/短信通道，也不允许运营自定义新密码。
- 停用账号 = 置 `is_active=False`：登录走 Django `authenticate()`，被停用账号按现有凭证错误返回 401，登录代码零改动。
- 新增前端模块 `frontend/src/modules/ops-console`：`/ops/users` 单页列表 + 右侧抽屉操作；侧栏在「AI任务」分组之后追加「运营」分组，仅运营 / 超管可见。
- `/api/auth/me/` 响应补 `is_operator`，前端据此判定入口可见性与深链拦截；`MeUser` DTO 同一次变更内同步更新。
- 本期不做：审计表、删除用户、按运营给权限细分、在页面上授予运营（授予仍由超管在 Django Admin 的组成员里做）。
- **BREAKING**：无。

## 关联文档

无。`dev_docs/ARCH_PRD/PRD-平台总需求.md` 按模块索引、不使用需求编号，且未覆盖运营侧能力；本变更不改动任何既有业务流（登录、任务、用例、设备均不受影响），故无对应 PRD 条目。PRD 是否需要补运营章节，归档后再定。

## Capabilities

### New Capabilities

- `ops-user-console`: 运营身份判定、运营后台的访问控制、用户列表与停用/启用/重置密码、权限边界与防呆、停用对登录的影响、前端入口可见性。

### Modified Capabilities

（无。侧栏只在既有分组之后追加新分组，不触碰 `frontend-sidebar-nav` 已固定的顺序；`/api/auth/me/` 新增字段与 `auth-response-shape` 的「DTO 与响应一致」不变量在同一次变更内同步满足，既有需求本身不变。）

## Impact

- 后端新增：`backend/apps/ops_console/`（`apps.py` / `urls.py` / `views.py` / `api.py` / `serializers.py` / `AGENTS.md`），并在 `backend/config/settings.py` 的 `INSTALLED_APPS` 与 `backend/config/urls.py` 各加一处注册。
- 后端修改：`backend/shared/users.py`（新增 `is_operator`）、`backend/apps/accounts/views.py`（`/api/auth/me/` 补 `is_operator`）、`backend/apps/accounts/api.py`（新增重置密码写口，供 ops_console 跨 App 调用）。
- 前端新增：`frontend/src/modules/ops-console/`（`index.vue` / `routes.ts` / `api.ts` / `constants.ts` / `components/` / `composables/` / `helpers/` / `AGENTS.md`）。
- 前端修改：`frontend/src/router.ts`、`frontend/src/shared/components/sidebarNavConfig.ts`、`frontend/src/shared/styles/tokens.css`（新模块色 `--c-ops`，同步登记到 doodle-craft 参考）、`frontend/src/shared/types/auth.ts` 与当前用户判定。
- 契约：新接口必须同步更新 `openspec/openapi.yaml` 基线（`openapi-schema` 门禁为阻塞项）。
- 测试：新增 `tests/ops_console/`（401 / 403 / 权限边界 / 幂等）；前端 `frontend/tests/ops-console/`；`auth-response-shape` 既有单测随 `MeUser` 同步。
- 不触碰：`engines/`、Django Admin、计费与配额、任务与设备链路。
