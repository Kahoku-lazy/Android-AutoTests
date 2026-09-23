## Why

登录模块的活体接口用例只覆盖了 `/api/auth/login/` 与 `/api/auth/register/` 两个端点的 20 条；**刷新、登出、me 三个端点以及若干边界仍停留在 PRD 的「待设计」表**里没有任何自动化守护 —— 而会话吊销（access 与 refresh 一起失效）、续期文案、防枚举恰好是最容易悄悄回归的契约。上一步已在 `dev_docs/DEV_TEST/接口自动化测试/接口自动化测试-登录.md` 的「未覆盖清单」里把它们逐条登记，本变更把这批清单落地为可执行用例。

## What Changes

- **补齐 login.yaml 4 条**：TC-LOGIN-015（账号前后带空格 → 401）、016（密码前后带空格 → 200）、017（请求体是 JSON 数组 → 400）、018（公开端点不带 Authorization → 200）。
- **补齐 register.yaml 2 条**：TC-REG-021（用户名前后带空格 → 200 且入库为 strip 后的值）、TC-REG-022（邮箱前后带空格 → 200）。
- **新增 refresh.yaml（4 条）**：TC-REFRESH-001 正常续期 / 002 用 access 冒充 refresh / 003 乱码 refresh / 005 缺 refresh_token 字段；**004「登出后再刷新」**以 `setup: logout` 标记登记在同一文件，由流程驱动执行。
- **新增 logout.yaml（3 条）**：TC-LOGOUT-001 正常登出 / 002 登出后再用原 access 请求 me / 004 未带 Authorization 登出；**003「登出后再用原 refresh 刷新」**同样以 `setup: logout` 登记。
- **新增 me.yaml（3 条）**：TC-ME-001 正常读取身份 / 002 不带令牌 / **003「登出后再读」**（`setup: logout`）。
- **新增驱动 3 个**：`tests/api/test_auth_tokens.py`（refresh/logout/me 单请求用例，按 `auth: none|required` 分流 session）、`tests/api/test_auth_session_flow.py`（4 条 `setup: logout` 多步用例：登出 → 断言 access 与 refresh 同时失效）、`tests/api/test_auth_register_concurrency.py`（TC-REG-023 并发同名注册）。
- **`tests/api/conftest.py` 新增 `admin_tokens` fixture**：提供 `admin_access_token` / `admin_refresh_token` 供 YAML 占位符使用，避免把会过期的令牌写死进用例。
- **口径修正（已与用户确认）**：TC-LOGIN-016 按**实测行为**断言 200 —— 登录侧密码走 DRF CharField 默认 `trim_whitespace=True`，与注册侧显式 `strip()` 一致（密码首尾空格等价于无空格）；PRD 该行同步由「401 / 密码不 trim」改为「200 / 密码被 trim，与注册侧一致」。
- **文档同步**：`接口自动化测试-登录.md` 补入全部新增用例（五字段）、收缩「未覆盖清单」、更新规模与运行方式；PRD 对应章的「待设计」表迁入已实现口径。

**明确不在范围**（活体接口层做不了，已与用户确认）：

- TC-LOGOUT-005「停掉 Redis 后登出 → 503」：需要停全局 Redis，属基础设施操作；其 fail-closed 行为已由灰盒单元用例 `tests/graybox/unit/test_logout_session_revocation.py::test_logout_fails_closed_when_redis_unavailable` 覆盖。
- TC-ME-004「令牌有效但账号已删 → 404」：需要改库，属集成层（`django_db`），不是黑盒 HTTP 能表达的。

## 关联文档

- PRD：`dev_docs/ARCH_PRD/PRD-00-登录模块.md`（各端点的「待设计」用例表）
- 接口文档：`dev_docs/DEV_TEST/接口文档/API-登录.md`
- 测试文档：`dev_docs/DEV_TEST/接口自动化测试/接口自动化测试-登录.md`
- 测试约定：`tests/AGENTS.md`（接口测试用 YAML + JSONSchema 断言；模块 ↔ 脚本映射）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 本变更只新增测试与文档，不改变任何运行时行为；`.openspec.yaml` 已设 `skip_specs: true`。若实现过程中发现后端行为与 PRD 期望不符，另开变更修行为，不在本次偷偷改。）

## Impact

- 测试：新增 `tests/api/case/{refresh,logout,me}.yaml`、`tests/api/test_auth_tokens.py`、`tests/api/test_auth_session_flow.py`、`tests/api/test_auth_register_concurrency.py`；修改 `tests/api/case/login.yaml`、`tests/api/case/register.yaml`、`tests/api/conftest.py`。
- 用例规模：20 → **39**（登录 13 / 注册 14 / 刷新 5 / 登出 4 / me 3；其中 4 条为「登出后失效」多步流程用例、1 条为并发用例）。
- 文档：`dev_docs/DEV_TEST/接口自动化测试/接口自动化测试-登录.md`、`dev_docs/ARCH_PRD/PRD-00-登录模块.md`。
- 后端 / 前端源码：**零改动**；无接口、无字段、无迁移。
