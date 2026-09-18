## Why

登录链路梳理图（`temps/login-stack-map`）的 G4 与 G5 两项缺口，都是**前端认证契约与后端事实脱节**：

**G4** —— `frontend/src/shared/types/auth.ts` 的 `AuthTokenData` 声明了
`user?: { id: number; username: string; email?: string }`，但

- 后端 `login` 只返回 `user: {id, username}`，**从不返回 `email`**；`register` 才返回 `email`
- 前端**没有任何地方读这个字段**（`useAuthFlow` 只取 `access_token` / `refresh_token`）

即：一个未被消费的可选字段，用宽泛的形状把两个端点的差异掩盖了。谁将来照着它取值，都会拿到 `undefined`。

**G5** —— `shared/api-auth-interceptors.ts` 的全局 401 处理**不区分端点**：只认 `status === 401`
就去刷新令牌。而登录/注册这类公开端点的 401 意思是**凭证错误**，不是令牌过期。
后果：池里残留旧 refresh token 时，一次密码错误会先白走一次刷新并换掉本地 token。

## What Changes

- **删除 `AuthTokenData.user?`** —— 未被消费，且形状随端点不同；删掉即消除这个"可选字段掩盖差异"的谎言。
  （若将来需要，按端点分别声明准确形状，并由下述守护覆盖）
- **给全局 401 拦截器加公开端点豁免**：`/auth/login`、`/auth/register`、`/auth/refresh` 的 401 直接拒绝，
  不进入刷新流程
- **新增对拍守护** `tests/graybox/unit/test_auth_frontend_contract.py`：
  1. 前端认证 DTO 声明的字段集合 ⊆ 后端对应响应的 key 集合（覆盖 `AuthTokenData` / `AuthRefreshData` / `MeUser`）
  2. 拦截器的公开端点豁免清单 == 网关 `PUBLIC_PREFIXES` 中 `/api/auth/*` 的那一部分
- 更新 `tests/AGENTS.md` §契约对拍测试（断言条数与文件清单）

**Non-goals**：

- **不建共享常量源**、不让前端从后端拉规则 —— 与 `auth-form-validation` 同一取舍
- 不为 `user` 字段补一套按端点区分的类型 —— 没有消费者，属过度设计（需要时再加，守护会保证它准确）
- 不改后端任何代码
- 不处理 G3（响应形状无 serializer）、G7（端点资产目录漂移）—— 独立范围

## 关联文档

- `openspec/specs/auth-response-shape/spec.md` —— 本变更新建的能力
- `openspec/specs/auth-session/spec.md` —— 本次为其新增「公开端点的 401 不触发刷新」
- `temps/login-stack-map/login-stack-map.html` 的 G4 / G5 —— 来源
- `tests/AGENTS.md` §契约对拍测试 —— 既有范式的边界

## Capabilities

### New Capabilities

- `auth-response-shape`：认证端点响应形状与前端 DTO 的一致性约束，以及由默认测试对拍的要求

### Modified Capabilities

- `auth-session`：新增「公开认证端点的 401 不触发全局令牌刷新」

## Impact

- **前端**：`shared/types/auth.ts`（删 1 行字段）、`shared/api-auth-interceptors.ts`（加豁免判断）
- **测试**：新增 `tests/graybox/unit/test_auth_frontend_contract.py`；`tests/AGENTS.md` 追加一条
- **不涉及**：后端代码、数据库、API 形状、依赖
- **BREAKING**：无（删除的是无消费者类型字段；401 行为只影响公开端点，且是纠错）
