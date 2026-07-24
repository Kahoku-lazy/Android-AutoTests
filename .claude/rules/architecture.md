# Architecture — Android-AutoTests

AI 驱动的 Android UI 自动化测试平台，前后端分离，HTTP REST + WebSocket 通信。

**前端**：Vue 3 + Vite + Element Plus，9 模块，Doodle Craft 极简几何主题
**后端**：Django + Daphne + Channels，9 App，JWT 鉴权
**AI**：AgentScope 2.0 (FastAPI)，38 Tool，Redis 消息总线，ChromaDB RAG
**设备**：uiautomator2 + ADB，28 种步骤类型

## 关键架构约束

- **AgentScope 依赖 Redis**：Redis 不可用时 AgentScope 无法启动，AI 对话降级到 Django 阻塞模式
- **前端 Proxy**：`/api` `/ws` → `:8765` (Django)，`/agentscope` → `:8000` (AgentScope)
- **JWT 共享**：Django + AgentScope 共享 `SECRET_KEY`
- **写操作收敛**：所有写操作必须通过 `api.py`，禁止直接 ORM INSERT/UPDATE/DELETE（只读 ORM 查询除外）
- **模块通信**：跨 App import Model（只读）+ api.py（复杂写），禁止跨 App import service/内部实现
- **新增 App 注册**：`settings.py` INSTALLED_APPS + `config/urls.py` include + `router.js` import + `AppSidebar.vue` navItems 各 1 行
