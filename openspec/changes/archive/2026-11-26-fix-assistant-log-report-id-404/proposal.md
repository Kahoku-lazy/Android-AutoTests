# Proposal: fix-assistant-log-report-id-404

## Why

`tests/ai_assistant/api/test_assistant_thread_logs.py::test_unknown_report_is_404` 在 HEAD 上稳定失败：
带 `report_id="../secret"` 且**不带 ticket** 请求 `GET /api/ai/assistants/threads/<id>/logs/<report_id>`，
响应是 **401**，用例断言 **404**。

根因是**校验顺序**，不是漏了校验：

```
AssistantThreadLogFileView.get()
  1. thread 不存在 → 404
  2. thread 还在跑 → 409
  3. consume_log_ticket(...)  ← 没票就在这里 401
  4. resolve_thread_report()  ← report_id 的边界校验在这里（永远走不到）
```

`resolve_thread_report()`（`services/assistant_threads.py:95-101`）本身有完整防护：
`Path(report_id).name != report_id`、`.`/`..`、以及 `root not in folder.parents` 都会返回 None。问题是它排在换票之后。

两个实际后果：

1. **既定用例红**：该用例是「非法报告编号必须 404 且不回显路径」的守卫，现在守卫失效。
2. **非法 id 会烧掉一次性 ticket**：攻击面是「诱导用户点一个伪造链接，票被消耗，正常打开反被拒」。这是可被利用的可用性问题。

## What Changes

- 把「报告编号是否合法」抽成纯函数（规则沿用 `resolve_thread_report` 现有的两条：`Path(id).name == id` 且不是 `.`/`..`），
  由 `resolve_thread_report` 与视图**共用**同一处判定，禁止两套正则/规则并存。
- `AssistantThreadLogFileView.get()` 里把该判定**前移到 `consume_log_ticket()` 之前**：
  非法 `report_id` 直接 **404**，且**不消费 ticket**。
- 合法 `report_id` 的语义**不变**：无票 / 过期票 / 已用票仍是 401；票有效但报告不存在仍是 404。
- **不动 spec 文本**：`assistant-log-ticket` 规格未约束该错误码，本变更只是让实现回到既定用例与既有边界规则，属缺陷修复而非能力变更。

## Capabilities

### New Capabilities

（无 —— 修的是实现顺序，规格未变）

### Modified Capabilities

（无）

## Impact

- **代码**：`backend/apps/ai_assistant/views_drf.py`（`AssistantThreadLogFileView.get()`）、
  `backend/apps/ai_assistant/services/assistant_threads.py`（提取纯函数，`resolve_thread_report` 改为复用）。
- **测试**：`tests/ai_assistant/api/test_assistant_thread_logs.py` —— 现有 `test_unknown_report_is_404` 转绿；
  另补一条「非法 id 不消耗 ticket」。
- **行为变化**：仅「非法 report_id + 无票」从 401 改为 404。
- **回退**：还原这两个文件即可。

## 关联文档

- 来源：`align-backend-docs-with-code` / `assistant-release-eval` 归档时的门禁复跑（`test_unknown_report_is_404` 在干净 HEAD worktree 上复现）
- 规格：`openspec/specs/assistant-log-ticket/spec.md`（无 delta）
