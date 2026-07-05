# 模块测试方案 — 执行引擎

> 关联子PRD：`02-PRD需求/子PRD/04-test-runner.md` · 版本：v1.0 · 日期：2026-06-30

---

## 1. 测试范围

| 类型 | 内容 |
|------|------|
| 接口测试 | 4 REST + 1 WebSocket |
| 流程测试 | 正常执行、中途停止、压力测试 |
| 异常测试 | 步骤失败、设备断开、超时 |

---

## 2. 执行 API 测试

| 编号 | 用例 | 方法 | 预期 |
|:--:|------|------|------|
| TR-API-01 | 开始执行 | POST /api/runner/run | 201，返回 run_id |
| TR-API-02 | 执行缺少用例 | POST /api/runner/run (case_ids=[]) | 400，提示至少选一个用例 |
| TR-API-03 | 查询执行状态 | GET /api/runner/status/{id} | 200，含 progress/total/passed/failed |
| TR-API-04 | 查询不存在的 run | GET /api/runner/status/{fake} | 404 |
| TR-API-05 | 停止执行 | POST /api/runner/stop/{id} | 200，状态变为 STOPPED |
| TR-API-06 | 停止已完成执行 | POST /api/runner/stop/{id} | 400，提示不可停止 |

---

## 3. 执行流程测试

| 编号 | 用例 | 场景 | 预期 |
|:--:|------|------|------|
| TR-FLOW-01 | 单用例单次 | 1 case × 1 loop | 步骤全部 PASS，WebSocket 推送每条结果 |
| TR-FLOW-02 | 多用例循环 | 2 cases × 10 loops | 20 次执行全部完成，报告统计正确 |
| TR-FLOW-03 | 中途停止 | 执行中 → STOP | 当前步骤完成后终止，状态 STOPPED |
| TR-FLOW-04 | 步骤失败 | 某步 click 元素不存在 | 该步骤 FAIL，继续执行下一步 (非 fatal) |
| TR-FLOW-05 | 致命失败 | start_app 失败 | 该 case 终止，继续下一个 case |
| TR-FLOW-06 | 全部步骤 PASS | 6 步全通过 | 报告 status=COMPLETED, pass_rate=100% |

---

## 4. 压力测试

| 编号 | 用例 | 循环次数 | 预期 |
|:--:|------|:--:|------|
| TR-STRESS-01 | 轻度压力 | 100 | 全部完成，无超时 |
| TR-STRESS-02 | 中度压力 | 1000 | 数据库不膨胀，内存稳定 |
| TR-STRESS-03 | 重度压力 | 10000 | 可执行，考虑分批写入 |

---

## 5. WebSocket 进度推送

| 编号 | 用例 | 消息 | 预期 |
|:--:|------|------|------|
| TR-WS-01 | 步骤开始 | `type:step_start` | 含 step_index/type/description |
| TR-WS-02 | 步骤结果 | `type:step_result` | 含 status/duration/error |
| TR-WS-03 | 循环进度 | `type:progress` | 含 current/loop/total |
| TR-WS-04 | 执行完成 | `type:complete` | 含 summary (total/passed/failed) |

---

## 6. 异常测试

| 编号 | 用例 | 场景 | 预期 |
|:--:|------|------|------|
| TR-ERR-01 | 设备中途断开 | 执行中拔 USB | 当前步骤标记 FAIL，执行终止，设备释放 |
| TR-ERR-02 | 应用崩溃 | 执行中 App crash | crash 步骤 FAIL，后续步骤 SKIP |
| TR-ERR-03 | ADB 服务宕掉 | adb kill-server | 执行暂停，提示 ADB 不可用 |
| TR-ERR-04 | 重试成功 | retry_click 第一次失败 | 自动重试 3 次，第 2 次成功 |

---

## 变更记录

| 版本 | 日期 | 变更摘要 |
|------|------|----------|
| v1.0 | 2026-06-30 | 基于子PRD v1.0 输出，覆盖 6 API + 6 流程 + 3 压力 + 4 WS + 4 异常 |
