# API Conventions — Android-AutoTests

## 端点总览 (50 REST + 2 WebSocket)

### element-locator `/api/elements/` — 14 端点

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|:--:|
| POST | `/api/elements/dump` | dump 当前页面 UI 层级 | ✅ |
| POST | `/api/elements/action` | 在设备上执行操作（点击/滑动/输入） | ✅ |
| GET | `/api/elements/device-info` | 获取设备信息（分辨率/版本） | ✅ |
| GET | `/api/elements/screenshot` | 获取当前截图（base64） | ✅ |
| GET | `/api/elements/pages` | 列出所有已保存页面 | ✅ |
| POST | `/api/elements/pages/create` | 创建新页面记录 | ✅ |
| POST | `/api/elements/pages/clear` | 清空所有页面和元素 | ✅ |
| GET | `/api/elements/pages/<page_id>` | 获取页面详情 | ✅ |
| GET | `/api/elements/pages/<page_id>/items` | 获取页面下的元素列表 | ✅ |
| POST | `/api/elements/pages/<page_id>/elements` | 向页面添加元素 | ✅ |
| POST | `/api/elements/items/<el_id>` | 更新元素（别名/tags/备注） | ✅ |
| GET | `/api/elements/flows` | 列出所有页面跳转流 | ✅ |
| POST | `/api/elements/flows` | 创建页面跳转流 | ✅ |
| POST | `/api/elements/flows/<flow_id>` | 删除页面跳转流 | ✅ |

### device-pool `/api/devices/` — 12 端点

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|:--:|
| GET | `/api/devices/` | 列出所有设备及状态 | ✅ |
| POST | `/api/devices/scan` | 扫描 ADB 设备 | ✅ |
| POST | `/api/devices/<serial>` | 连接设备（注册到设备池） | ✅ |
| POST | `/api/devices/<serial>/disconnect` | 断开设备连接 | ✅ |
| POST | `/api/devices/<serial>/activate` | 激活设备（设为 ONLINE） | ✅ |
| POST | `/api/devices/<serial>/lock` | 锁定设备（分配用户） | ✅ |
| POST | `/api/devices/<serial>/release` | 释放设备 | ✅ |
| GET | `/api/devices/current` | 当前用户锁定的设备 | ✅ |
| POST | `/api/devices/heartbeat` | 设备心跳上报 | ✅ |
| GET | `/api/devices/queue` | 查看全局排队状态 | ✅ |
| POST | `/api/devices/<serial>/queue` | 加入设备等待队列 | ✅ |
| POST | `/api/devices/<serial>/queue/leave` | 离开设备等待队列 | ✅ |

### case-manager `/api/cases/` — 5 端点

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|:--:|
| GET | `/api/cases/definitions` | 列出所有用例定义 | ✅ |
| GET | `/api/cases/definitions/<case_id>` | 获取单个用例详情 | ✅ |
| POST | `/api/cases/definitions` | 创建/更新用例定义 | ✅ |
| POST | `/api/cases/export/yaml` | 导出用例为 YAML | ✅ |
| GET | `/api/cases/exports` | 列出已导出文件 | ✅ |
| GET | `/api/cases/exports/<filename>` | 下载 YAML 导出文件 | ✅ |

### test-runner `/api/runner/` — 6 端点

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|:--:|
| POST | `/api/runner/run` | 启动测试执行（async） | ✅ |
| POST | `/api/runner/run/<run_id>/stop` | 停止指定运行 | ✅ |
| GET | `/api/runner/run/<run_id>/status` | 查询运行状态和结果 | ✅ |
| GET | `/api/runner/runs` | 列出历史运行记录 | ✅ |
| GET | `/api/runner/active` | 列出当前活跃运行 | ✅ |
| POST | `/api/runner/run-step` | 执行单步操作（调试用） | ✅ |

### report-generator `/api/reports/` — 3 端点

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|:--:|
| GET | `/api/reports/` | 列出所有报告 | ✅ |
| GET | `/api/reports/<filename>` | 下载报告文件 | ✅ |
| GET | `/api/reports/<filename>/content` | 在线查看报告内容 | ✅ |

### ai-assistant `/api/ai/` — 28 端点

**认证**（5 端点，无需认证）：

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/ai/auth/login` | 用户登录 |
| POST | `/api/ai/auth/register` | 用户注册 |
| POST | `/api/ai/auth/refresh` | 刷新 JWT token |
| POST | `/api/ai/auth/logout` | 登出（token 加入黑名单） |
| GET | `/api/ai/auth/me` | 获取当前用户信息 |

**Agent 管理**（12 端点）：

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/ai/agents` | 列出所有智能体 |
| POST | `/api/ai/agents/create` | 创建智能体 |
| GET | `/api/ai/agents/<agent_id>` | 获取智能体详情 |
| POST | `/api/ai/agents/<agent_id>/update` | 更新智能体配置 |
| POST | `/api/ai/agents/<agent_id>/delete` | 删除智能体 |
| GET | `/api/ai/agents/<agent_id>/conversations` | 列出智能体的对话列表 |
| POST | `/api/ai/agents/<agent_id>/conversations/create` | 创建新对话 |
| POST | `/api/ai/agents/<agent_id>/test` | 测试智能体连接 |
| GET | `/api/ai/agents/<agent_id>/models` | 获取可用模型列表 |
| POST | `/api/ai/agents/<agent_id>/register-scope` | 注册到 AgentScope |
| GET | `/api/ai/agents/health` | 全部智能体健康检查 |
| GET | `/api/ai/models/detect` | 检测所有模型连接 |

**对话 & 消息**（8 端点）：

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/ai/conversations/<conv_id>/messages` | 获取对话消息列表 |
| POST | `/api/ai/conversations/<conv_id>/send` | 发送消息（阻塞模式兜底） |
| POST | `/api/ai/conversations/<conv_id>/stream` | 启动 SSE 流式对话 |
| POST | `/api/ai/conversations/<conv_id>/save-message` | 保存消息到数据库 |
| POST | `/api/ai/conversations/<conv_id>/confirm-result` | 发送用户确认结果（HITL） |
| POST | `/api/ai/conversations/<conv_id>/create-scope-session` | 创建 AgentScope 会话 |
| POST | `/api/ai/conversations/<conv_id>/rename` | 重命名对话 |
| POST | `/api/ai/conversations/<conv_id>/delete` | 删除对话 |

**任务**（2 端点）：

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/ai/conversations/<conv_id>/tasks` | 列出对话关联的任务 |
| GET | `/api/ai/conversations/<conv_id>/tasks/<run_id>` | 获取单个任务详情 |

**文件**（3 端点）：

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/ai/upload-avatar` | 上传智能体头像 |
| POST | `/api/ai/upload-file` | 上传并解析文件 |
| GET | `/api/ai/avatars/<filename>` | 获取头像文件 |

### WebSocket — 2 路由

| 路径 | 消费者 | 说明 |
|------|--------|------|
| `/ws/screenshot` | `ScreenshotConsumer` | 2fps 截图流推送 |
| `/ws/test-run/<run_id>` | `TestRunConsumer` | 测试执行实时状态推送（6 种消息类型） |

### AgentScope FastAPI `/agentscope/*`

AgentScope 框架自动注册的动态路由（内部 API，前端通过 Vite proxy 转发），包括 `chat`、`sessions`、`agent`、`credential` 等。

## API 交互规则

### 请求格式

- **Content-Type**：`application/json`（除文件上传用 `multipart/form-data`）
- **鉴权**：`Authorization: Bearer <JWT>`（除 `/api/ai/auth/*` 外全部需要）
- **CSRF**：所有业务视图使用 `@csrf_exempt`（前后端分离，JWT 鉴权替代 CSRF）

### 响应格式

```json
// 成功
{"ok": true, "data": {...}}

// 失败
{"ok": false, "error": "错误描述"}
```

### 跨域来源规则

| 来源 | 方式 | 规则 |
|------|------|------|
| **Vue 前端** | HTTP → Django view | JWT 鉴权，业务数据通过 `request.body` JSON 传递 |
| **AgentScope** | Tool → Django ORM/API | 同进程直接调用，不走 HTTP，通过 `db_helper.run_sync()` 异步桥接 |
| **Django Admin** | ORM → DB | 管理员专用，走 Django 内置 session 认证 |

### 写操作收敛原则

```
前端只能通过 Django View 写数据 → View 调用 api.py 函数写 DB
AgentScope Tool 只能通过 api.py 函数写数据 → 同进程直接调用
禁止任何组件直接 ORM INSERT/UPDATE/DELETE（只读 ORM 查询除外）
```

## 新增 App 时的框架注册（4 个文件各 1 行）

| 文件 | 操作 |
|------|------|
| `config/settings.py` | `INSTALLED_APPS` 加 1 行 |
| `config/urls.py` | `include('apps.{name}.urls')` |
| `frontend/src/router.js` | `import` 模块路由汇总 |
| `frontend/src/shared/components/AppSidebar.vue` | `navItems` 加菜单项 |

## 技术细节

- **阻塞操作**：uiautomator2 调用是阻塞的 — Django 同步视图在 Daphne 工作线程中运行
- **async 视图**：仅 `POST /api/runner/run` 使用 `async def`，通过 `asyncio.create_task()` 后台执行
- **Channels**：开发环境优先 Redis（`channels_redis`），不可用时回退 InMemoryChannelLayer
- **CORS**：开发环境 `CORS_ALLOW_ALL_ORIGINS = True`
- **SSE**：AgentScope 流式对话通过 Vite proxy 转发 `/agentscope-stream` → `:8000`
