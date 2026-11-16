## Why

运营后台能停用账号、重置密码，但不能把一个普通用户设成运营。现在授予运营只能由超管进 Django Admin 的组成员页勾选，运营同事自己看不到、也做不了。用户管理页已经是超管看账号的地方，缺的就是这一档授权。

## What Changes

- 新增两个端点，**仅超级管理员**可调用：`POST /api/ops/users/<id>/grant-operator/` 把普通用户加入用户组「运营」，`POST /api/ops/users/<id>/revoke-operator/` 把运营移出该组。
- 授权范围只有这一档「运营」。不新增角色表、不改 `is_superuser`、不引入更细的权限档。
- 运营调用这两个端点 MUST 返回 403。运营之间不能互相授权，也不能给自己授权。
- 不能对超级管理员授予或取消运营：超管身份不由用户组决定，页面上也不提供这个动作。
- 不能对自己授予或取消运营。
- 重复授予、重复取消 MUST 幂等：目标已是目标状态时返回成功且不额外写库。
- 用户管理抽屉对超级管理员多一个动作：「设为运营」或「取消运营」，随目标当前身份切换；对运营账号这个按钮不出现。
- 写库新增 `accounts.api.set_operator(user_id, enabled)`，经用户组关系落库，不在 `ops_console` 里直接改组。
- 本期不做：运营互相授权、审计表、批量授权、第二档角色。
- **BREAKING**：无。既有四个端点的权限与行为不变。

## 关联文档

无。`dev_docs/ARCH_PRD/PRD-平台总需求.md` 不覆盖运营侧能力。本变更是 `add-ops-user-console` 明确留下的非目标（页内授予运营），不改既有业务流。

## Capabilities

### New Capabilities

（无。授权是运营用户管理能力的增量，不单立能力。）

### Modified Capabilities

- `ops-user-console`: 在既有「运营可停用/启用/重置普通用户」之上，新增「仅超级管理员可授予/取消运营」的需求，并放宽「运营后台不提供授予端点」这一条。停用、启用、重置密码、列表、越权拦截的既有需求不变。

## Impact

- 后端修改：`backend/apps/accounts/api.py`（新增 `set_operator`）、`backend/apps/ops_console/api.py`（编排与超管校验）、`backend/apps/ops_console/views.py` 与 `urls.py`（两个新端点）、`backend/apps/ops_console/AGENTS.md`（红线从「禁止授予端点」改为「仅超管、仅这一档」）。
- 前端修改：`frontend/src/modules/ops-console/` 的抽屉、列表页动作、`api.ts`、`constants.ts`。侧栏与路由守卫不变。
- 契约：新端点必须同步 `openspec/openapi.yaml`。
- 测试：`tests/ops_console/api/` 增超管 200、运营 403、对自己 403、对超管 403、幂等；前端 `frontend/tests/ops-console/` 增按钮可见性。
- 不触碰：`engines/`、用户表结构、计费与配额、`is_superuser` 的授予。
