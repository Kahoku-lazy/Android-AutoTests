# 模块测试方案 — 平台认证与基础

> 关联：`02-PRD需求/实际需求文档.md` M8 · 版本：v1.0 · 日期：2026-07-01

---

## 1. 测试范围

| 类型 | 内容 |
|------|------|
| 接口测试 | 5 个 Auth 端点 + 路由守卫 |
| 前端测试 | 登录页 / 路由跳转 / 退出 |
| 安全测试 | JWT 过期 / 黑名单 / 刷新 |
| 边界测试 | 错误密码 / 重复注册 / 无 token |

---

## 2. 认证 API 测试

| 编号 | 用例 | 方法 | 路径 | 输入 | 预期 |
|:--:|------|------|------|------|------|
| AUTH-01 | 正常登录 | POST | /api/ai/auth/login | admin/admin123 | 200，access_token + refresh_token |
| AUTH-02 | 错误密码 | POST | /api/ai/auth/login | admin/wrong | 401，"Invalid credentials" |
| AUTH-03 | 注册新用户 | POST | /api/ai/auth/register | newuser/pass123 | 200，返回 token |
| AUTH-04 | 重复注册 | POST | /api/ai/auth/register | admin/pass123 | 409，"already exists" |
| AUTH-05 | 刷新 Token | POST | /api/ai/auth/refresh | refresh_token | 200，新 access_token |
| AUTH-06 | 错误刷新 | POST | /api/ai/auth/refresh | access_token | 401，"Not a refresh token" |
| AUTH-07 | 退出登录 | POST | /api/ai/auth/logout | Bearer access_token | 200 |
| AUTH-08 | 退出后重用 Token | GET | /api/ai/auth/me | 已退出 token | 401（黑名单） |

---

## 3. 路由守卫测试

| 编号 | 用例 | 操作 | 预期 |
|:--:|------|------|------|
| AUTH-UI-01 | 无 token 访问 | 直接访问 /ai-assistant | 自动跳转 /login |
| AUTH-UI-02 | 有 token 访问 | 登录后访问 /ai-assistant | 正常进入 |
| AUTH-UI-03 | 已登录访问 /login | 带 token 打开 /login | 自动跳转 /dashboard |
| AUTH-UI-04 | 退出后 | 点击退出 → 再访问 /ai-assistant | 跳转 /login |
| AUTH-UI-05 | token 过期 | 手动删 localStorage access_token | 跳转 /login |

---

## 4. 前端测试

| 编号 | 用例 | 操作 | 预期 |
|:--:|------|------|------|
| AUTH-UI-06 | 登录页 UI | 访问 /login | 动森主题 Card + 输入框 + 登录按钮 |
| AUTH-UI-07 | 用户名预填 | 访问 /login | 输入框预填 admin |
| AUTH-UI-08 | 注册切换 | 点击"没有账号？去注册" | 按钮文字变为"注册" |
| AUTH-UI-09 | 侧边栏用户名 | 登录后 | 显示登录用户名 |
| AUTH-UI-10 | 退出按钮 | 点击侧边栏"退出" | 清 token → 跳转 /login |

---

## 5. 边界与安全测试

| 编号 | 用例 | 场景 | 预期 |
|:--:|------|------|------|
| AUTH-SEC-01 | 无 token 请求 API | 不带 Authorization 访问 /api/ai/agents | 401 |
| AUTH-SEC-02 | 伪造 token | Authorization: Bearer fake | 401 |
| AUTH-SEC-03 | 过期 token | 使用过期 access_token | 401 |
| AUTH-SEC-04 | 跨服务 JWT | Django 签发 → AgentScope 验证 | 通过（共享 SECRET_KEY） |
