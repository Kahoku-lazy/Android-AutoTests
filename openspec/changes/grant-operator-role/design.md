## Context

`add-ops-user-console` 已把运营身份落在 Django 内置用户组「运营」上，判定集中在 `backend/shared/users.py::is_operator`（超管或该组成员）。账号写口在 `backend/apps/accounts/api.py`（`set_user_active` / `set_user_password`），运营编排与边界在 `backend/apps/ops_console/api.py::check_manageable`。

那个变更把「页内授予运营」列为非目标，并在 `ops_console/AGENTS.md` 红线里禁止新增授予端点。本变更就是补上这一档，并改那条红线。

现状约束：

- 用户组表已存在，授予 = 加组、取消 = 移组，不需要迁移。
- 超管不靠用户组判定。给超管加「运营」组不改变其身份标签，页面上做这个动作没有可观察效果，所以直接拒绝。
- 抽屉动作目前只有停用/启用与重置密码，按钮是否可用由列表页按 `canManage` 算好后传入。

## Goals / Non-Goals

**Goals:**

- 超管在用户管理抽屉里把普通用户设为运营、把运营取消回普通用户。
- 写库经 `accounts.api` 的一个新写口，`ops_console` 只做「是不是超管」与「能不能动这个人」的校验。
- 运营调用、对自己、对超管，三条都在服务端 403，且可测。

**Non-Goals:**

- 不做运营互相授权。
- 不做第二档角色，不新建角色表，不改 `is_superuser` 的授予方式。
- 不做审计表。授予/取消只记运行日志（谁对谁做了什么），不建查询页。
- 不做批量授予。

## Decisions

### D1 用现有用户组，不新建角色模型

授予 = `user.groups.add(运营组)`，取消 = `user.groups.remove(运营组)`。组不存在时由写口 `get_or_create`，避免「库里还没建组就 500」。

- 备选「新建 `user_role` 表」：要迁移、要改 `is_operator` 的判定来源，和上一单「用组、零迁移」的决定相反，否。
- 备选「复用 `is_staff`」：`is_staff` 的语义是能进 Django Admin，授予运营会顺带打开后台，否。

### D2 写口放 `accounts.api.set_operator`，编排放 `ops_console.api`

`set_operator(user_id, enabled)` 只负责加组/移组并返回用户，不判权限。`ops_console.api.grant_operator` / `revoke_operator` 负责：取目标 → 校验超管 → 校验不是自己、不是超管 → 调写口 → 记日志。

这与停用/重置的分层一致：`ops_console` 不直接 `groups.add`，跨 App 写走对方 `api.py`。

### D3 两个动作式端点，仅超管

`POST /api/ops/users/<id>/grant-operator/` 与 `POST /api/ops/users/<id>/revoke-operator/`。

视图先要求运营身份（沿用 `_require_operator`，挡住未登录与普通用户），再在 api 层要求 `is_superuser`。两层分开的原因：普通用户与运营的拒绝文案不同，测试也能分别断言。

- 备选「一个 PATCH 带 `enabled`」：和现有 `disable/`、`enable/`、`reset-password/` 的动作式路径不一致，日志里也不如两个路径好读，否。

### D4 幂等在写口里做

已在组里再授予、不在组里再取消，都直接返回，不写库。与 `set_user_active` 的幂等口径一致。

### D5 抽屉按钮按身份切换，且只对超管渲染

列表页已有 `isSuperuser`。超管打开普通用户行显示「设为运营」，打开运营行显示「取消运营」，打开超管行两个都不显示。运营打开任何行都不显示这两个按钮。

前端隐藏不是安全边界。服务端 403 才是。按钮缺失只为不给运营一个点了必失败的入口。

提交前走 `ElMessageBox` 二次确认，文案写明「对方将能进入运营后台」或「对方将失去运营入口」。确认取消不发请求。

### D6 红线改写，不绕开

`ops_console/AGENTS.md` 现有红线是「禁止新增授予运营的端点」。本变更把这句话改成「授予/取消运营仅超管、仅这一档，且必须经 `accounts.api.set_operator`」。不在红线仍禁止的情况下偷偷加端点。

## 模块防火墙自检

| 检查项 | 结论 |
| --- | --- |
| 跨 App import | `ops_console` 继续只调用 `accounts.api` 与只读 `auth.User`；新增调用是 `set_operator`，不 import `accounts` 的 views / serializers |
| 写库收敛 | 组关系的 add/remove 只发生在 `accounts.api.set_operator` |
| 依赖方向 | `ops_console` → `accounts` / `shared`，`accounts` 不反向 import `ops_console` |
| 前端边界 | 只经 `/api/ops/*`，不拼组名、不读数据库 |
| engines | 零触碰 |
| 新跨模块依赖 | 无。唯一新增是 `ops_console` → `accounts.api.set_operator`，符合既有约定 |

## Risks / Trade-offs

- [超管误授一个不该进后台的人] → 二次确认，文案写明后果；不做批量，一次只动一个账号。
- [取消运营后对方手里的令牌仍能进运营页最多 1 小时] → 与停用同一限制：`is_operator` 每次请求现查，但已打开的页面要等下次请求才 403。确认文案里写明「已打开的页面会在下一次操作时失效」。不做令牌吊销。
- [运营组被人手从 Admin 删掉] → 写口 `get_or_create`，授予不会因组缺失失败。
- [红线与实现短暂不一致] → 改 `AGENTS.md` 与加端点放在同一提交，不先加端点后改红线。

## 上线与回退

- 无迁移。上线即后端两个端点 + 前端一个按钮。
- 回退：撤两个路由与抽屉按钮，再撤 `set_operator`。已授予的组成员关系保留，不影响登录与其它功能；需要收回时仍可在 Django Admin 的组成员里移出。
