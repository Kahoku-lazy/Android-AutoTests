---
name: trep-v1-0-phase0-implemented
description: TREP v1.0 Phase 0 内部接口抽象已完成 (2026-07-10)
metadata: 
  node_type: memory
  type: project
  originSessionId: 823d96a4-f98d-41e8-84da-b465406cb1aa
---

# TREP v1.0 Phase 0 实施完成

**日期**: 2026-07-10
**范围**: 内部接口抽象，零风险 — 不改 App 结构、不改 URL 前缀、前端向后兼容

## 四项改动

### 0.1 _broadcast → asyncio.gather + 2s 超时
- `callbacks.py`: 把串行 `for consumer in clients` 改为 `asyncio.gather` 并发广播
- 每个 send 包裹 `asyncio.wait_for(..., timeout=2.0)`
- 超时/异常自动 unregister 消费者，不再阻塞后续消费者

### 0.2 seq 序号机制
- `callbacks.py`: WsTestCallback 新增 `_seq: dict[str, int]` per-run_id 计数器
- `_broadcast` 自动注入 `msg["seq"]`，`on_run_finished` 清理
- 前端 `useTaskWebSocket.js`: ws.onmessage 检测 seq gap → console.warn + 标记 `_seqGapDetected`

### 0.3 移除 TestRunner.run() 设备锁定
- `runner.py`: 删除 `acquire_device`/`mark_device_busy` 调用（行 163-166）
- 删除 finally 中 `mark_device_idle`/`release_device` 调用（行 237-243）
- 移除 `from apps.device_pool.api import acquire_device, release_device`
- 设备生命周期完全由 views.py 管理

### 0.4 心跳 + 监控/快照端点
- `runner.py`: TestRunnerCallback 新增 `on_heartbeat`；TestRunner 新增 `_heartbeat()` 协程（每 5s）
- `callbacks.py`: WsTestCallback 实现 `on_heartbeat`
- `views.py`: 新增 `run_monitor` (GET /monitor/:run_id) + `run_snapshot` (GET /run/:id/snapshot)
- `urls.py`: 新增 2 条路由，共 12 条
- 前端: `applyWsMessage` 处理 heartbeat 类型，更新 `_lastHeartbeat` 和 `_connectionHealthy`

## 验证结果
- `python manage.py check`: 0 issues
- `npx vite build --mode development`: ✓ built in 7.94s
- curl 新端点: monitor + snapshot 正确返回 404（不存在的 run_id）
- curl 旧端点: active、tasks 正常返回数据
- 浏览器: test-runner 页面正常渲染，6 个任务卡片、5 个状态标签页

**Why**: 按 TREP v1.0 协议渐进式重构，Phase 0 先优化内部接口，为后续提取调度器 App 打基础。

**How to apply**: Phase 1 提取 test_scheduler App 时可复用 seq 机制和心跳模式。
