## Context

- 接口层现状：`tests/api/` 三个驱动（`test_login_page.py` / `test_devices.py` / `test_inspector.py`），用例是 YAML 数据，由 `tests/api/loader.py` 统一执行，每条固定三级断言：**状态码 → JSONSchema（`tests/api/schemas.py`）→ 定点字段（`expect.check` 点分路径）**。
- loader 是**单请求**模型：`execute_case(base_url, session, case, ctx)` 只发一次请求；没有多步、没有 setup 钩子。
- 认证分流已有既有约定：`test_devices.py` 按 YAML 里的 `auth: none|required` 把用例分给 `api_session` / `auth_session` 两个 fixture，本变更沿用，不发明新机制。
- 本次实测探针（2026-09-20，live `:8766`，Python `requests` 逐个打真实端点）得到的真实信封与文案：

| 场景 | 实测 |
|---|---|
| `POST /api/auth/refresh/` 正常 | `200` `{status:true, data:{access_token, token_type:"bearer"}}` |
| 用 access 冒充 refresh | `401` `{status:false, message:"令牌类型错误，需要刷新令牌"}` |
| refresh 乱码 / 缺字段 / 空串 | `401` `{status:false, message:"刷新令牌无效或已过期"}` |
| `POST /api/auth/logout/` 正常 | `200` `{status:true, data:{}}` |
| logout 未带 Authorization（网关拦） | `401` `{status:false, message:"请先登录"}` |
| `GET /api/auth/me/` 正常 | `200` `{status:true, data:{user:{id, username, is_superuser}}}` |
| me 无令牌 | `401` `{status:false, message:"请先登录"}` |
| 登出后 me（原 access） | `401` `{status:false, message:"登录已过期或令牌无效"}` |
| 登出后 refresh（原 refresh） | `401` `{status:false, message:"刷新令牌无效或已过期"}` |
| 登录账号带首尾空格 | `401` 「用户名或密码错误」（`LoginSerializer.username` 显式 `trim_whitespace=False`） |
| 登录密码带首尾空格 | `200`（`password` 走 DRF 默认 trim；注册侧显式 `strip()`，两侧一致） |
| 请求体为 JSON 数组 | `400` `{status:false, message:"无效数据。期待为字典类型，得到的是 list 。"}` |
| 注册用户名/邮箱带首尾空格 | `200`（入库为 strip 后的值） |
| 两线程同时注册同一用户名 | 恰好一个 `200`、一个 `409`「用户名已存在」 |

## Goals / Non-Goals

**Goals:**

- 把「未覆盖清单」里可被黑盒 HTTP 表达的 16 条全部落地为可执行用例，并在文档中可见。
- 用例仍是 **YAML 优先**：新增的期望值写在 YAML 里，Python 只做驱动与编排。
- 零后端改动；不改既有 20 条用例的断言口径。

**Non-Goals:**

- 不发起任何后端行为变更（含「登录密码不 trim」这一口径 —— 本次按实测行为记录，行为改动另开变更）。
- 不在活体层模拟基础设施故障（停 Redis）或直接改库（删用户）。
- 不重构 loader 的既有语义，不为 4 条多步用例把单请求模型改造成通用步骤机。

## Decisions

### D1 · 单请求用例继续纯 YAML，多步用例用「YAML 期望 + Python 编排」

- **做法**：需要「先登出再断言」的 4 条（TC-LOGOUT-002/003、TC-REFRESH-004、TC-ME-003）仍写在各自 YAML 里，但带一个 `setup: logout` 字段；`test_auth_tokens.py` 只挑**没有 setup** 的用例，`test_auth_session_flow.py` 只挑**有 setup** 的用例，执行时先
  用同一个 session 调一次 `/api/auth/logout/`，再交给 `execute_case` 断言。
- **理由**：期望值（状态码 / schema / 文案）留在 YAML —— 符合 `tests/AGENTS.md`「用例用 YAML 编写」的约定，也让同一份文案不会被两处维护；只有「步骤」这一件 loader 表达不了的事落到 Python。
- **备选**：给 loader 加通用 `steps` 列表（把单请求模型改成步骤机）—— 为 4 条用例引入一套新语法与解析分支，违背「简单胜于复杂」，已否；把这 4 条写成纯 Python 断言 —— 期望值散到 py 里，与其它 32 条不一致，已否。

### D2 · 认证分流沿用 `auth: none|required`

- **做法**：refresh/logout/me 的 YAML 里标注 `auth`，驱动按标注分给 `api_session`（无令牌）或 `auth_session`（`Bearer`）。
- **理由**：`test_devices.py` 已经这么分（`test_devices_unauthenticated` / `test_devices_authenticated`），复用既有模式，新驱动读起来与老驱动一致。
- **备选**：每个 YAML 一个驱动文件 —— 文件数翻倍、marker 重复，已否。

### D3 · 令牌类用例的输入来自 fixture 占位符，而不是写死

- **做法**：`tests/api/conftest.py` 新增 `admin_tokens` fixture（现场以种子账号登录一次，返回 `{access, refresh}`），驱动把它塞进 `execute_case` 的 ctx，YAML 里写 `{{admin_refresh_token}}` / `{{admin_access_token}}`。
- **理由**：令牌 1 小时后过期，写死在 YAML 里第二天必红；fixture 现场登录保证任何时候都能跑。
- **备选**：YAML 里写 `{{unique_username}}` 那样现场注册再取令牌 —— 注册会留下垃圾用户，登录 admin 更轻，已否。

### D4 · TC-LOGIN-016 按实测行为断言 200，并同步修正 PRD 口径

- **做法**：用例期望 `200` + `auth_success`；PRD 待设计表那行由「401 / 密码不 trim」改为「200 / 密码被 trim，与注册侧 strip 一致」；文档中写明该差异的来龙去脉。
- **理由**：登录 `LoginSerializer.password` 用 DRF CharField 默认 `trim_whitespace=True`，注册 `RegisterSerializer` 显式 `strip()` —— **两侧行为一致**（密码首尾空格等价于无空格）。把 PRD 里那句「密码不 trim」当契约去断言 401，会把一个自洽的实现判成缺陷。
- **备选**：断言 401 并改后端（加 `trim_whitespace=False`）—— 属行为变更，会改变「密码含首尾空格」用户的登录结果，须单独评估与回归，本次已与用户确认不做。

### D5 · 并发同名注册用两线程 + 断言状态码集合

- **做法**：`test_auth_register_concurrency.py` 用 `ThreadPoolExecutor(max_workers=2)` 同时注册同一个随机用户名，断言 `sorted(status) == [200, 409]`，并校验 409 那条的 message 为「用户名已存在」。
- **理由**：唯一性以**数据库唯一约束**为权威（`apps/accounts` 契约：`api.create_user()` 捕获 `IntegrityError` → `ConflictError` → 409）。两线程并发正好验证「校验层不判重」也不会出现 500。
- **备选**：顺序注册两次（已有灰盒单测 `test_register_uniqueness.py` 覆盖）—— 测不到并发竞态，已否。

## 模块防火墙自检

- 本变更**只新增/修改 `tests/` 下的测试与文档**，不改任何 `apps/` 代码：无跨 App import、无写库、无 `api.py` 调用、无接口与字段变更、无迁移。
- 用例只通过 HTTP 打真实后端（`http://localhost:8766`），不 import 被测内部实现，保持黑盒边界。
- 与既有 `tests/api` 三层断言机制、marker（`api` / `auth`）、fixture 命名保持一致。

## Risks / Trade-offs

- [新增用例需要后端已启动，无后端时整层红] → 与既有 20 条同命（`tests/api` 本就是 live server 层）；文档运行方式里已写明前置 `:8766`。
- [并发用例在调度极端情况下可能出现意外状态码] → 已实测一个 200 一个 409；实现后重复跑 3 次确认稳定；若哪天两个都成功，说明 DB 唯一约束失效，这条用例正是守卫。
- [登出类用例会吊销某个会话] → `auth_session` 是 function 级 fixture，每次现场登录新建 `sid`，只吊销它自己，不影响开发者浏览器里的会话。
- [PRD 正被其它会话并发编辑] → 改 PRD 前先重读目标行，只改与本次用例状态相关的行，diff 保持最小。
- [「未覆盖清单」收缩后仍有 2 条（LOGOUT-005 / ME-004）] → 已在文档中写明归属层与替代覆盖，不假装已覆盖。

## Open Questions

- TC-ME-004（账号已删 → 404）是否需要单独的集成层用例：留给后续决定，不影响本次验收（文档已登记去向）。
