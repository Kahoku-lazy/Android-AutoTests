# Auth Test Cases

> 对应脚本: `scripts/run_auth_tests.py`

## API 接口测试层

### AUTH-API-01: 正常登录

**层次**: API
**脚本函数**: `test_auth_api_01_login_ok()`

**步骤**:
1. POST /api/ai/auth/login admin/admin123
2. 验证 HTTP 200 + access_token 非空

**预期**: 返回 access_token + refresh_token + user 信息

### AUTH-API-02: 错误密码

**层次**: API
**脚本函数**: `test_auth_api_02_wrong_password()`

**步骤**:
1. POST /api/ai/auth/login admin/wrong
2. 验证 HTTP 401

**预期**: ok=False, 401

### AUTH-API-03: Token 刷新

**层次**: API
**脚本函数**: `test_auth_api_03_refresh_token()`

**步骤**:
1. 登录获取 refresh_token
2. POST /api/ai/auth/refresh

**预期**: 返回新 access_token

### AUTH-API-04: 登出

**层次**: API
**脚本函数**: `test_auth_api_04_logout()`

**步骤**:
1. 登录获取 access_token
2. POST /api/ai/auth/logout

**预期**: HTTP 200, ok=True

### AUTH-API-05: 获取当前用户

**层次**: API
**脚本函数**: `test_auth_api_05_me()`

**步骤**:
1. 登录
2. GET /api/ai/auth/me

**预期**: 返回 username, id

## 前端验证层

### AUTH-UI-01: 登录页加载

**层次**: UI
**脚本函数**: `test_auth_ui_01_login_page()`

**步骤**:
1. curl http://localhost:5173/src/views/LoginView.vue
2. 验证 HTTP 200

**预期**: 登录页模块编译成功

### AUTH-UI-02: 无硬编码密码

**层次**: UI
**脚本函数**: `test_auth_ui_02_no_hardcoded_password()`

**步骤**:
1. 检查 LoginView.vue 源码
2. 验证无 `ref('admin123')` 等硬编码密码

**预期**: loginPassword 初始值为空字符串或 undefined
