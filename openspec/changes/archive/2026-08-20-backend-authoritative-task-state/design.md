## Context

前端 `taskUtils.deriveTaskStatus`（`frontend/src/modules/test-runner/composables/taskUtils.ts:30-48`）与后端状态语义平行实现，含同一漂移补丁。后端 `task_views.task_card_list` 已在下发前调用 `repair_queued_terminal_drift()` 自愈 DB，故 `display_state` 面向的是"已自愈后"的行数据；对内存中未刷新的脏行，判定逻辑仍按漂移语义容错（与 repair 一致）。

## Goals / Non-Goals

**Goals:**

- `display_state(tc)` 成为"任务处于什么状态"的唯一判定入口（后端）
- REST 列表携带权威 `state` 字段（四值：running/queued/done/idle），旧字段全保留
- `DEVICE_ENGINE` 接线（settings → session 工厂）

**Non-Goals:**

- 不改前端（Step 6 切消费方、删 `deriveTaskStatus`）
- 不动 WS 事件协议（progress 事件不承载任务状态，列表 REST 为唯一载体）
- 不做 executor 会话化/业务锁联动（另行评估，不在本序列）

## Decisions

- **四值口径**：`running/queued/done/idle`——与前端现有 `deriveTaskStatus` 返回值一一对应，使 Step 6 切换为纯删减；`done` 携带 outcome 供展示分桶（completed vs 其他终态）
- **判定顺序**（与前端现状语义逐条对齐）：running 标志 → queued+终态漂移 → queued → 终态 outcome → idle
- **字段共存**：`state` 与 `status/outcome/running` 并存一个版本周期，Step 6 后前端不再读 status/running 推导
- **settings 接线**：`DEVICE_ENGINE = "airtest_u2"`（settings.py）+ session 工厂 `get_device_engine(getattr(settings, "DEVICE_ENGINE", DEFAULT_ENGINE))`

## 模块防火墙自检

- 无新增跨 App import；settings/session 均为既有模块内改动
- 无 ORM 写路径变化（display_state 纯读）；前端零改动
- 通过

## Risks / Trade-offs

- [display_state 与 repair 语义漂移] → 判定逻辑从 repair 的 outcome__in 集合直接引用 `TaskOutcome.terminal_values()`，单测覆盖漂移用例
- [旧前端读 status/running 与新 state 并存期不一致] → 两者同源（同一次查询序列化），无并发不一致窗口；Step 6 立即切换
- [settings 缺省] → getattr 兜底 DEFAULT_ENGINE，未配置环境不炸
