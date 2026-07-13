# 代码 Review 规则

> 每次代码改动后强制执行此检查清单。关联架构：`项目技术架构/当前实现架构方案.md`
> 版本：v3.0 · 日期：2026-07-01

---

## 严重度标签

| 标签 | 含义 | 处理 |
|:--:|------|------|
| 🔴 MUST | 阻断项，必须修复才能合并 | 修复 → Re-review |
| 🟡 SHOULD | 建议项，强烈建议修复 | 修复或记录理由 |
| 🟢 NIT | 微小建议，不阻塞 | 记录，后续改进 |

---

## 一、模块边界检查

| # | 检查项 | 通过标准 | 违规示例 | 等级 |
|:--:|--------|---------|---------|:--:|
| 1 | 改动范围 | 改动文件在对应模块目录内，不跨域污染 | 任务说"改元素导出"但动了 `device_pool/api.py` | 🔴 |
| 2 | service 层隔离 | 无 `from apps.X.service import ...` 跨 App 导入 | `from apps.device_pool.pool import DevicePool` | 🔴 |
| 3 | 跨模块写操作 | 跨 App 的 INSERT/UPDATE/DELETE 必须走该模块的 `api.py` 函数 | `Device.objects.update(status='ONLINE')` 在 test_runner 代码里 | 🔴 |
| 4 | 跨模块读操作 | ✅ 允许跨 App `from apps.X.models import Y` + `Y.objects.filter(...)` | — | ✅ |
| 5 | AgentScope Tool | Tool 调用 Django API 走 ORM 或 `api.py`，不走 HTTP | Tool 里用 `requests.post('http://localhost:8765/...')` | 🔴 |
| 6 | AgentScope 边界 | Tool 文件在 `agentscope_service/tools/`，不放在 `apps/` 下 | 在 `apps/element_locator/` 里写 AgentScope Tool | 🔴 |

---

## 二、API 契约检查

| # | 检查项 | 通过标准 | 等级 |
|:--:|--------|---------|:--:|
| 7 | api.py 函数签名 | 新增参数 → 给默认值。不删除/重命名已有参数 | 🔴 |
| 8 | 端点路径规范 | 前缀匹配模块：`/api/{domain}/*` | 🟡 |
| 9 | 响应格式 | 统一 `{"ok": true, "data": {...}}` 或 `{"ok": false, "error": "..."}` | 🔴 |
| 10 | 响应状态码 | 200(成功) / 201(创建) / 400(参数错) / 401(未授权) / 404(不存在) | 🟡 |

---

## 三、数据安全检查

| # | 检查项 | 通过标准 | 等级 |
|:--:|--------|---------|:--:|
| 11 | 表名前缀 | 新表使用模块前缀：`el_` / `dp_` / `cm_` / `tr_` / `rg_` / `ai_` | 🔴 |
| 12 | 敏感信息泄露 | 代码/日志/注释中无明文密码、Token、API Key | 🔴 |
| 13 | SQL 注入防护 | Django ORM 参数化查询，无原始 SQL 拼接用户输入 | 🔴 |
| 14 | JWT Token 有效期 | Access ≤ 1h，Refresh ≤ 7天，使用 `SECRET_KEY` 签名 | 🔴 |

---

## 四、前端边界检查

| # | 检查项 | 通过标准 | 等级 |
|:--:|--------|---------|:--:|
| 15 | 跨模块组件 | 无 `import XPanel from '@/modules/device-pool/components/...'` 在其他模块 | 🔴 |
| 16 | API 调用 | `api.js` 只调本模块的后端端点 | 🔴 |
| 17 | 路由懒加载 | 新增路由使用 `() => import(...)` | 🟡 |
| 18 | 无硬编码 URL | 所有 URL 来自 `api-client.js` 的 baseURL 配置 | 🟡 |
| 19 | AI 模块主题隔离 | AI 助手使用 animal-island-vue 组件，不反向污染业务模块 | 🟡 |

---

## 五、文件结构检查

| # | 检查项 | 通过标准 | 等级 |
|:--:|--------|---------|:--:|
| 20 | 后端 App 目录 | 含 `__init__.py` / `apps.py` / `models.py` / `views.py` / `urls.py` / `admin.py` / `api.py` / `permissions.py` / `migrations/` | 🔴 |
| 21 | AgentScope 目录 | 含 `tools/` / `teams/` / `rag/`，工具文件在 `tools/{domain}_tools.py` | 🔴 |
| 22 | 前端模块目录 | 含 `index.vue` / `routes.js`，可选 `api.js` / `composables/` | 🟡 |
| 23 | AppConfig 注册 | `config/settings.py` 的 `INSTALLED_APPS` 已注册 | 🔴 |
| 24 | URL 注册 | `config/urls.py` 包含 `include('apps.{name}.urls')` | 🔴 |
| 25 | 前端路由注册 | `frontend/src/router.js` 导入模块 routes | 🔴 |
| 26 | 侧边栏注册 | `AppSidebar.vue` 的 `navItems` 有对应菜单项 | 🔴 |
| 27 | 临时文件 | 无 `*.tmp.*` 残留文件 | 🟢 |

---

## 六、文档同步检查

| # | 检查项 | 通过标准 | 等级 |
|:--:|--------|---------|:--:|
| 28 | 架构方案 | 新增/删除模块 → 更新 `项目技术架构/当前实现架构方案.md` §2.2 | 🔴 |
| 29 | 命名标准 | 新增表/端点 → 更新 `命名统一标准.md` | 🔴 |
| 30 | AgentScope Tool | 新增 Tool → 更新 `项目技术架构/当前实现架构方案.md` Tool 清单 | 🟡 |

---

## 七、命名检查

> 完整命名规范见 [`命名统一标准.md`](命名统一标准.md)，此处为速查清单。

| # | 检查项 | 通过标准 | 等级 |
|:--:|--------|---------|:--:|
| N1 | 文档目录名 | `kebab-case`：`element-locator/` | 🔴 |
| N2 | Python 包名 | `snake_case`：`element_locator/` | 🔴 |
| N3 | 数据库表名 | `{前缀}_{snake_case}`：`el_elements` | 🔴 |
| N4 | Django Model 类名 | `PascalCase` 不带前缀：`class Element(Model)` | 🟡 |
| N5 | API URL | `/api/{domain}/*`，kebab-case 资源名 | 🟡 |
| N6 | JSON 字段名 | `snake_case`：`page_id`, `created_at` | 🟡 |
| N7 | Python 函数 | `snake_case` 动词开头：`lock_device()` | 🟡 |
| N8 | JS 变量 | `camelCase`：`testDefinitions`, `fetchDevices()` | 🟡 |
| N9 | Vue 组件文件 | `PascalCase.vue`：`ChatView.vue` | 🟡 |
| N10 | Vue 路由路径 | `kebab-case`：`/ai-assistant/chat/:agentId` | 🟡 |

---

## 八、Python 专项检查

| # | 检查项 | 通过标准 | 等级 |
|:--:|--------|---------|:--:|
| P1 | Type Hints | 公开函数（`api.py`）的入参和返回值有类型标注 | 🟡 |
| P2 | 异常处理 | 捕获具体异常类型；catch 后有处理（日志/降级/重抛） | 🔴 |
| P3 | async/await | 异步函数正确使用 `await`，不在 async 中同步阻塞 | 🟡 |
| P4 | 上下文管理 | 文件/连接/锁使用 `with` 语句管理生命周期 | 🟡 |
| P5 | AgentScope Tool schema | `input_schema` 为合法 JSON Schema；`call()` 返回 `ToolChunk` | 🔴 |

---

## 九、AI 辅助审查专项

| # | 检查项 | 通过标准 | 等级 |
|:--:|--------|---------|:--:|
| AI-1 | 幻觉检测 | 无不存在的方法/类/API 调用。import 路径真实存在 | 🔴 |
| AI-2 | 过度设计 | 无为了"可能的未来"而引入的设计模式，遵循 YAGNI | 🟡 |
| AI-3 | 风格一致 | 与项目已有代码风格一致，不引入新的代码风格 | 🟡 |
| AI-4 | 错误处理 | 所有边界情况有健壮的错误处理，无裸 `try: pass` | 🔴 |
| AI-5 | AgentScope 版本 | Tool/Agent API 与 `agentscope==2.0.3` 兼容，参数名匹配 | 🔴 |

---

## 十、Review 结论

```
判定规则:
  无 🔴 且 无 🟡 → ✅ APPROVED
  无 🔴 但有 🟡 → 🔄 NEEDS_REVISION（或 APPROVED + 记录理由）
  有 🔴 → 🔄 NEEDS_REVISION
  方案根本问题 → ❌ REJECTED
```

### Review 报告模板

```markdown
## Code Review Report — {日期} {模块}
**Status**: ✅ APPROVED | 🔄 NEEDS_REVISION | ❌ REJECTED

### Summary
### 🔴 Must Fix
- **[文件:行号]** [问题] → [修复建议]
### 🟡 Should Fix
### 🟢 Nice to Have
### Strengths
### Recommendations
```

---

## 变更记录

| 版本 | 日期 | 变更摘要 |
|------|------|----------|
| v1.0 | 2026-06-30 | 初始版本，26 项检查，7 大类 |
| v1.1~v2.0 | 2026-06-30 | 引入三级严重度；新增 Python/AI 专项；`modules/`→`apps/` |
| v3.0 | 2026-07-01 | 裁剪废弃模块；新增 AgentScope Tool 专项(P5, AI-5)；移除 DRF 检查；新增 AI 模块边界(19) |
