# API-00-认证 — 登录接口测试用例

> 文档：`API-00-认证.md` · 实现：`auth_views.py::login`

| 编号 | 测试点 | 分类 | 场景 | 请求类型 | 请求地址 | 域名信息 | 请求参数 | Content-Type | 鉴权 | 请求体 | 期望 HTTP | 期望响应 | 说明 |
|:--:|:--:|:--:|------|:--:|------|------|------|:--:|:--:|------|:--:|------|------|
| TC-LOGIN-001 | 登录接口 | 功能 | 正常登录 | POST | /api/ai/auth/login | http://localhost:8765 | username, password | application/json | 无需 | `{"username":"admin","password":"admin123"}` | 200 | `status=true`, `access_token`, `refresh_token`, `user` | — |
| TC-LOGIN-002 | 登录接口 | 功能 | 用户名含首尾空格 | POST | /api/ai/auth/login | http://localhost:8765 | username, password | application/json | 无需 | `{"username":" admin ","password":"admin123"}` | 200/401 | 取决于 Django `authenticate()` 行为 | 后端不 trim |
| TC-LOGIN-003 | 登录接口 | 校验 | 用户名和密码均为空 | POST | /api/ai/auth/login | http://localhost:8765 | username, password | application/json | 无需 | `{"username":"","password":""}` | 400 | `请输入用户名和密码` | 第一个校验分支 |
| TC-LOGIN-004 | 登录接口 | 校验 | 用户名为空 | POST | /api/ai/auth/login | http://localhost:8765 | username, password | application/json | 无需 | `{"username":"","password":"admin123"}` | 400 | `请输入用户名` | `not username` |
| TC-LOGIN-005 | 登录接口 | 校验 | 密码为空 | POST | /api/ai/auth/login | http://localhost:8765 | username, password | application/json | 无需 | `{"username":"admin","password":""}` | 400 | `请输入密码` | `not password` |
| TC-LOGIN-006 | 登录接口 | 校验 | 用户名为纯空白 | POST | /api/ai/auth/login | http://localhost:8765 | username, password | application/json | 无需 | `{"username":"   ","password":"admin123"}` | 400 | `用户名不能为空白` | `not username.strip()` |
| TC-LOGIN-007 | 登录接口 | 校验 | 用户名超过 150 字符 | POST | /api/ai/auth/login | http://localhost:8765 | username, password | application/json | 无需 | `{"username":"<151个a>","password":"admin123"}` | 400 | `用户名过长，最多150个字符` | `len(username) > 150` |
| TC-LOGIN-008 | 登录接口 | 校验 | 用户名 150 字符（边界内） | POST | /api/ai/auth/login | http://localhost:8765 | username, password | application/json | 无需 | `{"username":"<150个a>","password":"admin123"}` | 401 | `用户名或密码错误` | 校验通过但用户不存在 |
| TC-LOGIN-009 | 登录接口 | 校验 | 缺少 username 字段 | POST | /api/ai/auth/login | http://localhost:8765 | username, password | application/json | 无需 | `{"password":"admin123"}` | 400 | `请输入用户名` | `data.get` 默认空串 |
| TC-LOGIN-010 | 登录接口 | 校验 | 缺少 password 字段 | POST | /api/ai/auth/login | http://localhost:8765 | username, password | application/json | 无需 | `{"username":"admin"}` | 400 | `请输入密码` | `data.get` 默认空串 |
| TC-LOGIN-011 | 登录接口 | 校验 | 空请求体 | POST | /api/ai/auth/login | http://localhost:8765 | username, password | application/json | 无需 | `{}` | 400 | `请输入用户名和密码` | 两者默认空串 |
| TC-LOGIN-012 | 登录接口 | 校验 | JSON 格式非法 | POST | /api/ai/auth/login | http://localhost:8765 | username, password | application/json | 无需 | `not a json` | 400 | `请求格式错误` | `json.JSONDecodeError` |
| TC-LOGIN-013 | 登录接口 | 认证 | 密码错误 | POST | /api/ai/auth/login | http://localhost:8765 | username, password | application/json | 无需 | `{"username":"admin","password":"wrong"}` | 401 | `用户名或密码错误` | 安全：不区分失败原因 |
| TC-LOGIN-014 | 登录接口 | 认证 | 用户名不存在 | POST | /api/ai/auth/login | http://localhost:8765 | username, password | application/json | 无需 | `{"username":"no_such_user","password":"admin123"}` | 401 | `用户名或密码错误` | 安全：防用户名枚举 |
| TC-LOGIN-015 | 登录接口 | 认证 | 用户名和密码均错误 | POST | /api/ai/auth/login | http://localhost:8765 | username, password | application/json | 无需 | `{"username":"no","password":"wrong"}` | 401 | `用户名或密码错误` | 统一返回 401 |
| TC-LOGIN-016 | 登录接口 | 安全 | SQL 注入 — username | POST | /api/ai/auth/login | http://localhost:8765 | username, password | application/json | 无需 | `{"username":"admin' OR '1'='1","password":"admin123"}` | 401 | `用户名或密码错误` | Django ORM 参数化防注入 |
| TC-LOGIN-017 | 登录接口 | 安全 | SQL 注入 — password | POST | /api/ai/auth/login | http://localhost:8765 | username, password | application/json | 无需 | `{"username":"admin","password":"' OR '1'='1"}` | 401 | `用户名或密码错误` | 同上 |
| TC-LOGIN-018 | 登录接口 | 安全 | XSS — username | POST | /api/ai/auth/login | http://localhost:8765 | username, password | application/json | 无需 | `{"username":"<script>alert(1)</script>","password":"admin123"}` | 401 | `用户名或密码错误` | 不存 DB，无实际风险 |
| TC-LOGIN-019 | 登录接口 | 安全 | 超长密码 1MB | POST | /api/ai/auth/login | http://localhost:8765 | username, password | application/json | 无需 | `{"username":"admin","password":"<1MB>"}` | 401 | `用户名或密码错误` | 验证服务不崩溃 |
| TC-LOGIN-020 | 登录接口 | 安全 | 暴力破解 5 次连续错误 | POST | /api/ai/auth/login | http://localhost:8765 | username, password | application/json | 无需 | 同用户连续 5 次错误密码 | 401 | 均为 `用户名或密码错误` | ⚠️ 当前无频率限制 |
