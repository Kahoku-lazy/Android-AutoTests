## Why

尾斜杠约定收紧为「唯一写法」的变更（`enforce-trailing-slash`）声称已「更新全部调用方：前端 api 层」，
但**认证链路被漏掉了**：`frontend/src/shared/api/auth.ts` 的 4 个调用与 `frontend/src/shared/api-client.ts:33`
的刷新调用仍是无尾斜杠形式。对运行中的后端（:8766）实测，这 5 个端点**全部 404**：

```
POST /api/auth/login      404      POST /api/auth/login/      400 {"status":false,"message":"请输入用户名和密码"}
POST /api/auth/register   404      POST /api/auth/register/   400 同上
POST /api/auth/refresh    404      POST /api/auth/refresh/    401 刷新令牌无效或已过期
POST /api/auth/logout     401(被鉴权门遮住)   POST /api/auth/logout/   401 请先登录
POST /api/auth/me         401(被鉴权门遮住)   POST /api/auth/me/       401 请先登录
```

用户可见症状不是 404，而是弹窗「目标不存在，请刷新页面后重试」（Django 的 404 页是 HTML，
`formatApiError` 取不到 `data.message`）。次生影响：`me()` 失败被 `useAuthUser` 的 catch 吞掉，
`isSuperuser` 恒为 `false`，导致 AI 助手的管理入口与工具调试页的写操作**永久禁用**。

**根因不是「漏了 5 行」，而是前后端之间没有任何东西校验这件事**：

| 本该拦住它的东西 | 为什么没拦住 |
|---|---|
| `tests/api/case/login.yaml` | 用的是 `/api/auth/login/`（带斜杠）—— 测后端，看不到前端字面量 |
| `tests/graybox/unit/test_api_path_convention.py` | 只遍历 `get_resolver()` 的路由表，纯后端侧 |
| `tests/e2e/test_example_e2e.py::test_login_and_enter_dashboard` | 就是这条链路，但需要 `TEST_ADMIN_PASSWORD` + 前后端在跑 → 默认 skip |
| 全仓 `tests/` | 实测 **0 处** 读 `frontend/` 源码 |

所以本次不只修路径，还要补上**默认就会跑**的一致性守护。

## What Changes

- **修正 5 处前端路径字面量**：`shared/api/auth.ts`（login/register/logout/me）与 `shared/api-client.ts`（refresh）
- **新增默认单测** `tests/graybox/unit/test_frontend_api_paths.py`：扫描 `frontend/src` 中所有 HTTP 调用路径字面量，
  逐条对 Django 路由表 `resolve()`，断言「带尾斜杠」且「能命中」；秒级、不依赖运行中的服务
- **新增鉴权姿态一致性断言**（同一测试文件）：认证端点满足 `AllowAny` ⟺ `authentication_classes` 为空
- **补 `tests/AGENTS.md`**：记录「测试读取前端源码做契约对拍」这一新范式及其边界

**Non-goals**：

- 不改后端路由、视图、中间件 —— 后端侧是本次约定的正确基线
- 不引入前端测试基建（本仓 `frontend/src` 下 0 个 spec/test 文件、无 vitest 配置）；
  用 Python 侧静态读取替代，而不是为了这一条断言新建一套运行器
- 不处理其余缺口：校验文案双写（G2）、响应形状无 serializer（G3）、登录 401 走全局刷新（G5）
- 不把「鉴权姿态」断言推广到全仓 —— 本次只覆盖认证端点，全仓现状未实测，推广前需先扫描

## 关联文档

- `dev_docs/ARCH_PRD/ARCH-00-平台总体架构.md` —— 平台分层与网关约束（本次改动的上位约束）
- `apps/AGENTS.md` §1.3 契约规则、`apps/accounts/AGENTS.md` §路径约定 —— 本次修正的契约来源
- `dev_docs/DEV_TEST/接口文档/API-认证.md`（如存在）—— 端点契约
- 说明：模板所指的 `dev_docs/文档编号对照表.md` 在本仓不存在，相关文档实际位于 `dev_docs/ARCH_PRD/`

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `api-path-convention`：新增「前端调用面与路由表的一致性由默认测试守护」。该能力现有需求
  「端到端调用方遵循唯一写法」在本变更前**处于被违反状态**（前端认证链路未带尾斜杠），本次修正并补上守护。
  注：该能力的基线规格尚未归档（`enforce-trailing-slash` 未 archive），其 delta 已存在于该变更目录下。
- `auth-session`：新增「认证端点显式声明鉴权姿态」—— 认证端点的 `AllowAny` 与空
  `authentication_classes` 必须成对出现，避免公开端点误继承鉴权、受保护端点误开放。

## Impact

- **前端**：`frontend/src/shared/api/auth.ts`（4 处路径）、`frontend/src/shared/api-client.ts`（1 处路径）
- **测试**：新增 `tests/graybox/unit/test_frontend_api_paths.py`；`tests/AGENTS.md` 追加一节
- **不涉及**：后端代码、数据库、迁移、API 形状、依赖、构建配置
- **BREAKING**：无。修正后前端行为与既有后端契约一致；后端零改动
- **验收**：登录、注册、续期、登出、身份五个入口恢复可用；新守护测试在默认单测套件中通过
