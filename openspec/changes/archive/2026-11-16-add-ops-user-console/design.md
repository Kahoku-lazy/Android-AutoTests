## Context

现状事实（已核对代码）：

- 身份只有两档：`auth_user.is_superuser`，跨模块判定集中在 `backend/shared/users.py::is_superuser`。
- 账号相关的写口只有 `backend/apps/accounts/api.py::create_user`；没有停用、改密、列用户的写口或接口。
- `POST /api/auth/login/` 走 `django.contrib.auth.authenticate()`（`accounts/serializers.py:38`），因此 `is_active=False` 天然登录失败，无需改登录代码。
- `GET /api/auth/me/` 已返回 `id / username / is_superuser`（`accounts/views.py:192`），且 `auth-response-shape` 要求前端 `MeUser` DTO 与响应 key 集合一致。
- 前端 10 个模块统一形态：`modules/<name>/{index.vue,routes.ts,api.ts,constants.ts,...}`，由 `src/router.ts` 汇总；侧栏是 `shared/components/sidebarNavConfig.ts` 里的静态配置，模块不拥有 L1。
- `backend/config/urls.py` 每个 App 一行 `include()`；`INSTALLED_APPS` 逐个登记。
- 新接口必须同步 `openspec/openapi.yaml` 基线，否则 `openapi-schema` 门禁阻塞。

## Goals / Non-Goals

**Goals:**

- 用「组」把运营身份表达出来，并让判定只有一处实现。
- 四个端点覆盖列表 / 停用 / 启用 / 重置密码，写操作全部经 `accounts/api.py`。
- 前端一个单页模块，侧栏入口按身份渲染，深链有兜底。
- 所有边界（不能动超管、不能动其他运营、不能停用自己、不能删账号）在服务端可测。

**Non-Goals:**

- 不做审计表、不做操作历史查询页（本期只写运行日志）。
- 不做页内授予/取消运营（授予仍由超管在 Django Admin 的组成员里做）。
- 不做批量操作、导出、账号创建（创建已有 `/api/auth/register/` 与 Django Admin）。
- 不动登录契约（不新增「账号已停用」专用 403 文案）。
- 不做令牌即时吊销：停用后已签发令牌到期前仍有效。
- 不碰 `engines/`、计费、配额。

## Decisions

### D1 用 Django 内置用户组 `运营` 表示运营身份

`auth_group` / `auth_user_groups` 已存在，因此**零迁移**；判断 = `is_superuser OR groups(name='运营')`。不改 `is_staff`，被授予运营的人不会顺带获得 Django Admin 权限。

- 备选「复用 `is_staff`」：省一次组查询，但 `is_staff` 的语义是「能进 Django Admin」，会把后门一起打开，否。
- 备选「新增 `user_profile.role` 表 / 自定义 User」：语义最干净，但要迁移、要改用户体系、要处理存量，本期收益与风险不成比例，否。

代价：授予运营仍需进 Django Admin 的组成员页。这是本期非目标，作为下个变更的输入。

### D2 运营判定放进 `backend/shared/users.py`，与 `is_superuser` 同文件

那已经是「跨 App 唯一实现」的落点，`ops_console`、`accounts`、前端判定都能复用同一语义。禁止各视图自己写 `groups.filter(...)`。

### D3 新建独立 App `backend/apps/ops_console`，不塞进 `accounts`

`accounts` 是登录鉴权（公开端点、会话、吊销），运营台是管理面（受保护、有写操作）。分开的理由：① 以后加「平台配置只读」页时不必再动鉴权 App；② `accounts/AGENTS.md` 有「路径必须带尾斜杠」「错误码表」等契约，混入管理端点会让那张表失真。

代价：多一个 App 目录与一次 `INSTALLED_APPS` 登记。

### D4 写库经 `accounts/api.py` 的两个新写口，`ops_console/api.py` 只做编排

新增 `accounts.api.set_user_active(user_id, active)` 与 `accounts.api.set_user_password(user_id, new_password)`，`ops_console/api.py` 负责：取目标 → 校验边界 → 调写口 → 记日志 → 返回 DTO。

这满足 `backend/apps/AGENTS.md`「跨 App 写必须走对方 api.py」，也让「改 active」「改密码」以后被别的入口复用时不必复制校验。

### D5 四个端点，不做详情端点

`GET /api/ops/users/`、`POST /api/ops/users/<id>/disable/`、`POST /api/ops/users/<id>/enable/`、`POST /api/ops/users/<id>/reset-password/`。

列表已回带抽屉所需的全部字段（用户名、邮箱、身份标签、启用状态、注册时间、最后登录），故不做 `GET /api/ops/users/<id>/`——少一个契约面、少一组测试。

- 备选用 PATCH `/api/ops/users/<id>/` 改状态：写操作语义更通用，但 `is_active` 只有开/关两态，动作式 URL 在日志与审计上更可读，且与仓库既有 `.../update/`、`.../refresh/` 的动作式风格一致。

### D6 重置密码 = 服务端生成 16 位随机密码，一次性返回

字符集去掉 `0/O/1/l/I` 等易混字符，用 `secrets.choice` 生成；写库只存哈希（`user.set_password`）；响应里带 `username` + `password`，并提示「仅显示一次」。数据库与日志都不得落明文——日志只记「谁重置了谁」，不记密码。

- 备选「运营自定义新密码」：更灵活但会引入弱口令与「运营知道别人密码」的问题，否。
- 备选「发邮件链接」：项目没有邮件配置，且本期不引入外部依赖，否。

### D7 停用 = `is_active=False`，登录零改动

`authenticate()` 对 `is_active=False` 返回 `None`，登录按「用户名或密码错误」返回 401，不新增错误码、不改 `accounts/AGENTS.md` 的错误码表。

已知限制（写进 Risks）：已签发的 access 令牌到期前仍可用。做到即时吊销要改 JWT 中间件与 DRF 认证类，属 `auth-session` 能力的行为变更，必须另开变更——本期不做，但要在页面上把这句限制写进停用确认文案。

### D8 前端单页 + 抽屉；侧栏追加分组；新模块色登记

- 页面：`/ops/users`，`WorkbenchHeader` + `FilterTabs`（全部 / 启用 / 停用）+ `AppTable` + `el-drawer`（选中行开抽屉，抽屉内放停用/启用与重置密码两个动作）。
- 侧栏：新增分组 `运营`，追加在「AI任务」之后（不插在「仪表盘」与「AI 功能」之间，避免破坏 `frontend-sidebar-nav` 已固定的顺序），单条 `用户管理` → `/ops/users`，仅 `is_operator` 为真时渲染。
- 模块色：复用调色板里未被模块占用的 `--color-orange-37`，新增语义别名 `--c-ops`（赭橙），在 `tokens.css` 声明并同步登记到 `.agents/skills/doodle-craft/SKILL.md` 的 8 支彩笔表。**不新增颜色原子**：调色板白名单是 `lint:styles` 的硬门禁，新增原子会被拦。
- 身份状态：**复用既有的 `shared/composables/useAuthUser.ts`**（原本只有 `isSuperuser`），补 `isOperator`、`ensure()` 与 `resetAuthUser()`。侧栏与路由守卫都读它，不新建第二个"当前用户"缓存。
  - 备选「新建 `shared/auth/current-user.ts`」：与既有组合式职责重复，两套缓存还会出现"侧栏已更新、守卫还是旧值"的分叉，否。
- 分页在**服务端**：翻页/改每页条数都重新请求（接口已支持 `page` / `page_size` / `total`），不使用前端切片式的 `usePagination`。
- 复用现有零件，不自创：`AppTable`（表纸）、`DoodleBtn`（动作按钮）、`FilterTabs`（筛选）、`SkeletonCard` / `ErrorState` / `EmptyState`（三态）、`ElMessageBox`（二次确认）。

### D9 审计只写运行日志，不建审计表

写操作统一 `backend_log.info("ops: user=%s action=%s target=%s result=%s", ...)`。不建表的原因：建表要迁移、要查询页、要留存策略，属于另一个变更；日志已能满足「出事了能查谁干的」。

## 模块防火墙自检

| 检查项 | 结论 |
| --- | --- |
| 跨 App import | `ops_console` 只 import `accounts.api`（写）+ `django.contrib.auth` 的 User Model（只读）；不 import 任何 App 的 views/serializers/service/runner |
| 写库收敛 | 全部 INSERT/UPDATE 经 `accounts/api.py` 的两个新写口；`ops_console/api.py` 不直接 `user.save()` |
| 依赖方向 | `ops_console` → `accounts` / `shared`，单向；`accounts` 不反向 import `ops_console`（`/api/auth/me/` 只调 `shared.users.is_operator`） |
| 前端边界 | 前端只经 `/api/ops/*`，不直连数据库、不读 Django Admin |
| engines | 零触碰 |
| 新跨模块依赖 | 无新增；唯一新增依赖是 `ops_console` → `accounts.api`，符合既有约定 |

## Risks / Trade-offs

- [运营误停用真实同事] → 抽屉内二次确认，确认文案写明「该账号将无法登录，已登录会话最长 1 小时后失效」，且不做批量操作。
- [授予运营仍要进 Django Admin] → 明写在提案非目标里；页面对「如何成为运营」给一句说明，下个变更补页内授予 + 审计。
- [停用后旧令牌仍可用最长 1 小时] → 在确认文案与文档中写明；需要即时吊销时另开 `auth-session` 变更。
- [运营把最后一个超管之外的账号都停用] → 超管与运营本身受保护，不会因运营操作失去管理入口。
- [新模块色与既有 8 色混淆] → 选未占用的赭橙，并同时登记 `tokens.css` 与 doodle-craft 参考；`lint:styles` 门禁会拦住未声明令牌。
- [新增接口忘记更新 OpenAPI 基线] → `openapi-schema` 门禁直接失败，tasks 里单列一条并在失败信息里给重生成命令。
- [运营身份缓存过期导致入口闪错] → `current-user.ts` 在每次进入运营页与路由切换时核对一次；服务端 403 时前端清缓存并回工作台。

## 上线与回退

- 上线顺序：后端（两个写口 + 新 App + 一行 include + `INSTALLED_APPS`）→ 生成 `openspec/openapi.yaml` 基线 → 前端（模块 + 侧栏 + 令牌）→ 在 Django Admin 建 `运营` 组并加入首批运营。
- 无数据库迁移（组与用户表都用现成的），无需数据回填。
- 回退：撤前端路由与侧栏项 → 撤 `urls.py` 的 `include` 与 `INSTALLED_APPS` 登记 → 撤两个写口。已发生的 `is_active` 变更按 `backend.log` 里的 `ops:` 记录逐条恢复；组本身可保留，不影响任何既有功能。
