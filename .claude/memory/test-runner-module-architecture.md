---
name: test-runner-module-architecture
description: 执行引擎三层模块化架构设计方案与TREP协议
metadata: 
  node_type: memory
  type: project
  originSessionId: b58dddc1-eb0c-4658-a1c9-1454f8621dfc
---

## 背景

执行引擎当前 3136 行代码全部混在 `apps/test_runner/` 一个 App 里，views.py 单文件 1227 行（3 倍于 400 行上限），调度/执行/查询逻辑不分。

## 三层拆分方案

```
前端显示 (Vue) ←→ HTTP REST + WebSocket ←→ 调度器 (test_scheduler) ←→ Python Callback ←→ 执行器 (test_runner)
```

| 层 | 位置 | 职责 |
|----|------|------|
| 前端显示 | `frontend/src/modules/test-runner/` | 渲染、WebSocket 消费、用户操作，不参与调度/执行 |
| 调度器 | `apps/test_scheduler/`（新建） | 任务排队、设备分配、并发控制、状态机、TaskCard CRUD、WS 路由、协议监管 |
| 执行器 | `apps/test_runner/`（精简） | 用例执行、14 种步骤映射、u2 操作、崩溃恢复，不管设备锁/排队 |

## TREP v1.0 协议（三份）

1. **前端 ↔ 调度器**: HTTP REST，11 个端点（/api/scheduler/*）
2. **调度器 ↔ 执行器**: Python Callback，9 个方法（on_run_started, on_step_result, ...）
3. **调度器 → 前端**: WebSocket JSON，10 种事件类型 + seq 序号

时序约定：① seq 递增序号 ② gather+2s 超时广播 ③ 关键事件 await 确认

## 已实施的前端改动（2026-07-09）

- 默认 Tab 从 "all" 改为 "running"（执行中）
- 移除 "未执行"（notExecuted）分类
- taskBucket 回退值改为 "incomplete"

## 待实施

见 `dev_docs/04-任务拆分/架构师-详细任务计划-TREP-v1.0-protocol.html` 设计方案文档。
四阶段改进策略：阶段 0 内部接口抽象 → 阶段 1 提取 scheduler App → 阶段 2 AgentScope 适配 + 前端适配 → 阶段 3 清理旧代码。

**Why:** views.py 超限 3 倍，AgentScope 绕过调度器直接调 TestRunner，前端 AI 任务不可见，设备状态双重来源。

**How to apply:** 下次对话从阶段 0 开始——在现有 test_runner 内部改 _broadcast 为 gather+timeout、加 seq 序号、runner.py 移除内部设备锁管理。每阶段独立可验证。
