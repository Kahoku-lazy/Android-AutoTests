# 架构总纲

> 架构层面的硬约束。AI 编码时必须遵守，代码能读到的信息不在此重复。
> 编码规范见 `python-code.md` `frontend.md` `api-conventions.md`。

---

## 一、通信通道（封闭集合）

平台只有五条通道。新增跨组件通信只能复用已有通道，禁止引入新协议。

| # | 通道 | 协议 |
|:--:|------|------|
| ① | 前端 ↔ Django | HTTP REST + JWT |
| ② | Django → 前端 | WebSocket + JWT |
| ③ | 前端 → Django (AI SSE) | SSE + JWT |
| ④ | AgentScope → Django | 进程内直接调用 |
| ⑤ | Django ↔ 设备 | ADB |

```
❌ 禁止引入：gRPC · MQTT · Kafka · RabbitMQ · GraphQL · WebRTC
```

---

## 二、依赖方向

```
✅ 上层 import 下层（ai_assistant → device_pool）
✅ 同层 import api.py 或 Model（test_runner → case_manager.api）
❌ 下层 import 上层（device_pool → ai_assistant）
❌ 同层 import 内部实现（test_runner → case_manager.views）
```

`device_pool` 是唯一底层：禁止 import 任何其他 App。
`dashboard` 和 `ai_assistant` 是聚合层：允许 import 任意下层。
其余 App 是中层：只能 import 底层 + 同层 api.py。

---

## 三、AgentScope 边界

AgentScope 已从独立服务迁移为 Django 进程内模块（`apps/ai_assistant/agent_scope/`），不再有独立 `agentscope_service/` 目录。

```
❌ 禁止 AgentScope 直连数据库
❌ 禁止 AgentScope 直连设备
✅ 所有平台数据通过 Django ORM / api.py 获取（同进程直接调用）
```

---

## 四、dashboard 约束

`dashboard` 是纯聚合层，无自有数据表：

```
❌ 禁止 ORM 写操作（INSERT/UPDATE/DELETE）
✅ 只允许跨模块只读 ORM 查询
```

---

## 五、模块增减

### 新增 App 前检查

必须同时满足：

```
[ ] 有独立的数据主权（新表前缀不在现有 8 组前缀中）
[ ] 有独立的业务逻辑（不是现有模块的 CRUD 子集）
[ ] 不是纯聚合（聚合放 dashboard/views.py）
[ ] 不是纯配置（配置放现有 App 的 models.py）
```

新增必须同步改 4 个文件：

```
config/settings.py    → INSTALLED_APPS
config/urls.py        → include('apps.{name}.urls')
frontend/src/router.js → 新路由
frontend/.../AppSidebar.vue → 新菜单项
```

### 删除模块

必须同步清理：

```
apps/{name}/ + frontend/src/modules/{name}/（整个目录）
config/settings.py → 移除 INSTALLED_APPS
config/urls.py → 移除 include
前端 router.js + AppSidebar.vue → 移除条目
跨模块 import → 移除对已删模块的引用
```

---

## 六、红线

```
1.  前端直连数据库
2.  后端返回 Django Template
3.  跨模块 import 内部实现（views/service/runner/executor/state_machine）
4.  跨模块直接 ORM 写（必须走目标 api.py）
5.  device_pool import 上层模块
6.  dashboard 做 ORM 写
7.  引入五条通道之外的协议
8.  新增 App 不检查 §五 门槛
9.  AgentScope 直连数据库或设备
10. apps/ai_assistant/agent_scope/ 下新增 adapters/ 或 rag/
```
