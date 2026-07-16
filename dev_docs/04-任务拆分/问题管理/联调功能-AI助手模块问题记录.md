# AI 助手模块问题记录

> 状态：🔴 待修复 · 日期：2026-07-13 · 模块：ai_assistant / agentscope_service / 前端 AI 助手 · 范围：views / models / api / agent_factory / tools / ChatView / AgentDetail

---

## 概览

对 AI 助手三层（Django 后端 + AgentScope 服务 + Vue 前端）全面代码审查，发现 **43 个问题**（7 个 CRITICAL、9 个 HIGH、14 个 MEDIUM、13 个设计缺陷）。

---

## 🔴 CRITICAL：安全漏洞 / 认证失效

### 1. 所有端点无认证
**位置**：`gateway/middleware.py:68-74`

中间件有 dev fallback：无 token 时不返回 401，而是设 `request.user_id = None` 后放行。`views.py` 所有增删改端点均不检查 `request.user_id`（仅 `me` 端点读取）。

**修复方向**：删除 fallback，无 token 返回 401。

### 2. 权限模块未接入
**位置**：`permissions.py` → `views.py`

`permissions.py` 定义了 `check_agent_owner` 等完整权限函数，但从未被 `views.py` 导入使用。

**修复方向**：在每个 view 入口调用对应权限检查。

### 3. JWT 黑盒完全失效
**位置**：`shared/auth/jwt_auth.py:21-39`

- `create_access_token` / `create_refresh_token` 从不生成 `jti` claim
- `blacklist_token` 依赖 `jti`，无 `jti` 则永不黑名单
- 黑名单为内存 `set()`，重启消失

**修复方向**：生成 `jti` claim；黑名单迁 Redis。

### 4. 头像路径穿越
**位置**：`views.py:525-528` — `serve_avatar`

```python
fpath = AVATAR_DIR / filename   # filename 直接来自 URL 路径
```

`/api/ai/avatars/../../../config/settings.py` 可读任意文件。

**修复方向**：`Path(filename).name` 取纯文件名，拒绝含 `..` 或 `/` 的参数。

### 5. 用户身份已认证即丢弃
**位置**：`agent_factory.py:258` + `factory.py:59-72`

- `build_agent_from_db(user_id=...)` 从不使用 `user_id`
- `build_business_tools(user_id=...)` 从不传给 Tool
- 所有 Tool 是模块级单例，对用户盲

**修复方向**：Tool 实例化时注入 `user_id`，`check_permissions` 检查 `context.user_id`。

### 6. PRD 文件工具路径穿越
**位置**：`prd_tools.py:81,267`

`ParsePRDTool` 和 `DesignTestCasesFromPRDTool` 接受任意 `file_path`，LLM 可被诱导读取 `/etc/passwd`、`.env` 等。

**修复方向**：限制 `file_path` 到工作区目录内，拒绝绝对路径和 `..`。

### 7. 前端 XSS — LLM 输出无过滤渲染
**位置**：`ChatView.vue:1546-1550`

`marked()` 渲染后直接 `v-html` 插入 DOM，无 `DOMPurify`。LLM 若输出 `<script>` 或 `<img onerror=...>` 即执行。

**修复方向**：`DOMPurify.sanitize(marked.parse(text))`。

---

## 🟠 HIGH

### 8. Token 类型不校验
**位置**：`gateway/middleware.py`

中间件不区分 access/refresh token，refresh token 可直接当 access token 用。

### 9. `reveal_api_key` 无认证
**位置**：`views.py:211`

任何人知道 agent_id 即可获取完整解密 API key（首次调用）。

### 10. `decrypt_key` 明文回退
**位置**：`api.py:104-114`

解密失败时若值以 `sk-`/`fk-` 开头直接返回明文，加密体系被架空。

### 11. `list_available_models` 从前端接收裸 API key
**位置**：`views.py:832-838`

前端发送 raw API key 到后端，再转发第三方 API。不必要地多一次传输。

### 12. Fernet 密钥从 SECRET_KEY 确定性派生
**位置**：`api.py:90-92`

无盐、无 rotation。泄露 `SECRET_KEY` = 全部 API key 解密。

### 13. AgentScope URL 硬编码 HTTP
**位置**：`views.py:924`

`http://127.0.0.1:8000` — API key 解密后以明文 HTTP 发送。

### 14. `base_url` 未校验
**位置**：`agent_factory.py:277-278`

数据库中的 `base_url` 直接传给 SDK，可指向恶意代理截获 API key。

### 15. JWT 默认密钥 `'change-me'`
**位置**：`shared/auth/jwt_auth.py:17-18`

`SECRET_KEY` 未设置时使用已知默认值，任何攻击者可伪造 token。

### 16. HITL 取消不发送拒绝
**位置**：`ChatView.vue:1652-1657`

Cancel 按钮只清 `pendingConfirm`，不通知后端。流永久挂起。

---

## 🟡 MEDIUM

| # | 问题 | 位置 |
|---|------|------|
| 17 | 消息保存失败静默吞错 — 用户看到消息但未持久化 | `ChatView.vue:649-677` |
| 18 | SSE 错误不回退重试 — 直接降级阻塞模式 | `ChatView.vue:679-690` |
| 19 | Thinking block 无过滤渲染 — `v-html` 直接渲染 LLM 思考 | `ChatView.vue:1365` |
| 20 | Mermaid `securityLevel: "loose"` — 扩大 XSS 面 | `ChatView.vue:24` |
| 21 | 文件内容泄露到对话标题 — 标题截取含文件内容 | `ChatView.vue:697-706` |
| 22 | Agent 表单无验证 — 空名称/空 API key 可保存 | `AgentDetail.vue:173-186` |
| 23 | API key 通过 POST body 传输 | `AgentDetail.vue:175-179` |
| 24 | 上传文件不清理 — 磁盘永不清除 | `views.py:667` |
| 25 | `model_name` max_length=100 可能偏短 | `models.py` |
| 26 | `api_key` max_length=500 对 Fernet 输出可能不够 | `models.py` |
| 27 | 错误消息泄露实现细节 — `str(e)` 直接返回客户端 | `views.py` 多处 |
| 28 | `send_message` 不保存 ContentBlocks | `views.py:317 vs 425` |
| 29 | 无速率限制 — login / upload 无保护 | 全局 |
| 30 | Token 黑名单非持久 — 重启后已注销 token 复活 | `jwt_auth.py:24` |

---

## 🟢 设计缺陷

| # | 问题 |
|---|------|
| 31 | 模型无 User FK — 纯单用户，多租户需大改 |
| 32 | JSON 字段存为 TextField 无约束 |
| 33 | `serializers.py` 全部函数未使用 |
| 34 | `dashboard_views.py` 弃用但保留全实现 |
| 35 | `stream_chat` 返回 501 stub |
| 36 | Provider-to-baseURL 映射在 5 处重复且不一致 |
| 37 | `decrypt_key` 每次请求调用，无缓存 |
| 38 | 所有 Tool 权限返回无条件 ALLOW |
| 39 | Tool 注入忽略 agent 级配置，全部 agent 获得全部 tool |
| 40 | `_staged_cases` 模块级 dict 跨 session 泄露 |
| 41 | 文件上传绕过 token 刷新拦截器 |
| 42 | JWTConfig 默认 secret `'change-me'`（AgentScope 侧） |
| 43 | `DesignTestCasesFromPRDTool` 输出含 `traceback.format_exc()` |

---

## 优先修复建议

| 优先级 | 问题 | 修复难度 |
|-------|------|---------|
| P0 | #1 认证中间件 | 低 — 删 fallback |
| P0 | #4 头像路径穿越 | 低 — `Path(...).name` |
| P0 | #7 前端 XSS | 低 — 加 DOMPurify |
| P0 | #6 PRD 路径穿越 | 低 — 路径沙箱 |
| P0 | #3 JWT 黑盒 | 中 — jti + Redis |
| P1 | #5 用户身份贯穿 | 中 — 改 Tool 架构 |
| P1 | #14 base_url 校验 | 低 — 白名单 |
| P1 | #10 decrypt_key 明文回退 | 低 — 删除回退 |
| P1 | #16 HITL 取消不发拒绝 | 低 — 发送 DENY |
