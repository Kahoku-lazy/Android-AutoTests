---
name: ai-assistant-security-findings
description: AI 助手模块 43 个安全问题（含 7 CRITICAL）— 认证绕过/路径穿越/XSS/JWT黑盒失效/权限未接入。AI 每次改动必须检查的项。
metadata: 
  node_type: memory
  type: project
  originSessionId: f1410bd3-1472-4dd6-9403-e8f5d0bdfa1f
---

## AI 助手模块安全清单（每次改动必须检查）

> 来源：全模块代码审查发现 43 个问题。每次修改 `ai_assistant` / `agentscope_service` / 前端 AI 助手代码时逐项检查。

### 🔴 每次改动必查（7 项）

| # | 检查项 | 当前状态 | 修复方向 |
|:--:|------|:--:|------|
| 1 | **认证中间件 dev fallback**：`gateway/middleware.py` 无 token 时返回 401 还是设 `user_id=None` 放行？ | 🔴 待修复 | 删 fallback |
| 2 | **头像路径穿越**：`serve_avatar` 的 `filename` 来自 URL，是否限制为纯文件名？ | 🔴 待修复 | `Path(filename).name`，拒绝 `..` |
| 3 | **前端 XSS**：`ChatView.vue` 的 `marked()` + `v-html` 是否经过 `DOMPurify`？ | 🔴 待修复 | `DOMPurify.sanitize(marked.parse(text))` |
| 4 | **JWT 黑盒**：`create_access_token` 是否生成 `jti`？黑名单是否持久化（Redis）？ | 🔴 待修复 | 生成 jti；黑名单迁 Redis |
| 5 | **PRD 文件工具路径穿越**：`prd_tools.py` 是否限制了 `file_path` 在工作区目录内？ | 🔴 待修复 | 拒绝绝对路径和 `..` |
| 6 | **用户身份贯穿**：Tool 的 `check_permissions` 是否检查了 `context.user_id`？ | 🔴 待修复 | 注入 user_id 到 Tool |
| 7 | **decrypt_key 明文回退**：解密失败时是否 fallback 返回原文？ | 🔴 待修复 | 删除回退逻辑 |

### 🟠 新增代码时必查

| # | 检查项 |
|:--:|------|
| 8 | Token 类型是否校验（access vs refresh）？ |
| 9 | `reveal_api_key` 是否验证了调用者身份？ |
| 10 | API key 是否通过 POST body 明文传输（应走加密存储）？ |
| 11 | 错误消息是否泄露了 `str(e)` 实现细节？ |
| 12 | HITL 取消是否发送了 DENY 给后端（否则流永久挂起）？ |
| 13 | 消息保存失败是否静默吞错？ |
| 14 | 文件上传是否绕过了 JWT 拦截器？ |

### 设计层面（重构时参考）

- `permissions.py` 定义了完整权限函数但从未被 `views.py` 使用 → 接入
- `serializers.py` 全部函数未使用 → 接入或删除
- `dashboard_views.py` 已弃用但保留全实现 → 删除或移归档
- Provider→baseURL 映射在 5 处重复 → 抽取为 `provider_registry.py`
- Tool 注入忽略 agent 级配置 → 按 `ai_tools` 表过滤
- `_staged_cases` 模块级 dict 跨 session 泄露 → 改为实例属性

**How to apply:** 修改 `ai_assistant` 相关代码后，逐项核对上表。CRITICAL 项未修复前不得合并。
