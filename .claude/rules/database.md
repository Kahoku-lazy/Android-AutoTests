# Database — Android-AutoTests

> **获取表结构**：直接 Read 各 App 的 `models.py` 文件，这是唯一真相源。不要依赖任何手工抄录的字段表。

## 表前缀映射

| 前缀 | App | models.py |
|------|-----|-----------|
| `dp_` | device-pool | `apps/device_pool/models.py` |
| `el_` | element-locator | `apps/element_locator/models.py` |
| `cm_` | case-manager | `apps/case_manager/models.py` |
| `tr_` | test-runner | `apps/test_runner/models.py` |
| `rg_` | report-generator | `apps/report_generator/models.py` |
| `ai_` | ai-assistant | `apps/ai_assistant/models.py` |

## 核心规则

### 数据入库（写操作）

```
前端 HTTP → Django View → api.py 函数 → ORM 写入 DB
AgentScope → Tool.call() → api.py 函数 → run_sync() → ORM 写入 DB
Django Admin → ORM → DB（仅管理员）
```

> 所有写操作必须通过 `api.py` 函数，禁止直接 ORM 写入。

### 出库（读操作）

| 场景 | 方式 |
|------|------|
| 同模块内读取 | 直接 ORM 查询 |
| 跨模块读取 | 直接 ORM 查询（读放开） |

### 级联规则（去 models.py 看 `on_delete` 确认）

### 设备状态生命周期

```
(new) → ONLINE ⇄ BUSY → OFFLINE / DISCONNECTED → ONLINE
```

### AI 消息入库路径

```
SSE 流 → save_message (前端调用) → ai_messages 表
      → AgentScope 自动写 Redis (session 状态)
```

## 命名约定

| 层级 | 规范 | 示例 |
|------|------|------|
| 数据库表 | `{prefix}_{snake_case}` | `dp_devices`, `cm_test_definitions` |
| Model 类 | `PascalCase` | `Device`, `TestDefinition` |
| 外键字段 | `{related_name}_id` | `device_id`, `run_id` |
