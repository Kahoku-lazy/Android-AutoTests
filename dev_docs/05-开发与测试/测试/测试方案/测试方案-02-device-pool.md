# 模块测试方案 — 设备管理

> 关联子PRD：`02-PRD需求/子PRD-02-device-pool.md` · 版本：v1.0 · 状态：⏳ v2 计划 · 日期：2026-06-30

---

## 1. 测试范围

| 类型 | 内容 |
|------|------|
| 接口测试 | 5 个 REST API |
| 状态机测试 | ONLINE → BUSY → ONLINE / OFFLINE |
| 并发测试 | 多用户竞争锁定 |
| 边界测试 | 超时释放、心跳断开、设备热插拔 |

---

## 2. 接口测试

| 编号 | 用例 | 方法 | 预期 |
|:--:|------|------|------|
| DP-API-01 | 扫描设备 | POST /api/devices/scan | 200，返回发现的设备列表 |
| DP-API-02 | 获取设备列表 | GET /api/devices | 200，含状态/锁定用户/最后在线 |
| DP-API-03 | 锁定空闲设备 | POST /api/devices/{serial}/lock | 200，状态变为 BUSY |
| DP-API-04 | 锁定已被占设备 | POST /api/devices/{serial}/lock | 409，提示"设备被 {user} 占用" |
| DP-API-05 | 释放设备 | POST /api/devices/{serial}/release | 200，状态变为 ONLINE |
| DP-API-06 | 释放非自己设备 | POST /api/devices/{serial}/release | 403，提示无权限 |
| DP-API-07 | 查看排队 | GET /api/devices/queue | 200，返回队列位置 |
| DP-API-08 | 设备不存在 | POST /api/devices/fake/lock | 404 |

---

## 3. 状态机测试

| 编号 | 用例 | 操作 | 预期状态变化 |
|:--:|------|------|------------|
| DP-FSM-01 | 正常锁定 | ONLINE 设备 → lock | ONLINE → BUSY |
| DP-FSM-02 | 正常释放 | BUSY 设备 → release | BUSY → ONLINE |
| DP-FSM-03 | 超时释放 | BUSY 超过 TTL | BUSY → ONLINE (系统自动) |
| DP-FSM-04 | 心跳断开 | ONLINE 设备 stop adb | ONLINE → OFFLINE |
| DP-FSM-05 | 心跳恢复 | OFFLINE 设备 start adb | OFFLINE → ONLINE |

---

## 4. 并发测试

| 编号 | 用例 | 场景 | 预期 |
|:--:|------|------|------|
| DP-CONC-01 | 两人抢同一设备 | 用户A+B 同时 lock | 一个成功(200)，一个排队(202) |
| DP-CONC-02 | 释放后队列消费 | 队列中有B → A释放 | B 自动获取锁定 |

---

## 5. 边界测试

| 编号 | 用例 | 场景 | 预期 |
|:--:|------|------|------|
| DP-EDGE-01 | 热插拔 | 执行中途拔 USB | 当前步骤完成后释放，设备变 OFFLINE |
| DP-EDGE-02 | 无设备扫描 | adb devices 为空 | 返回空列表，不崩溃 |
| DP-EDGE-03 | 重复释放 | 对 ONLINE 设备 release | 幂等，返回 200 |
| DP-EDGE-04 | 队列超时 | 排队 >10 分钟未获取 | 队列项自动过期 |

---

## 变更记录

| 版本 | 日期 | 变更摘要 |
|------|------|----------|
| v1.0 | 2026-06-30 | 基于子PRD v1.0 输出，v2 开发时对照执行 |
