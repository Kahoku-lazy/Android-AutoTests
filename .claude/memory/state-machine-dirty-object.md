---
name: state-machine-dirty-object
description: 状态机写入 DB 后调用方持有脏对象导致 InvalidTransition → 孤儿 Run + 二次调度 → 前端计数跨 run 累加
metadata: 
  node_type: memory
  type: project
  originSessionId: f1410bd3-1472-4dd6-9403-e8f5d0bdfa1f
---

## 状态机脏对象问题

**症状**：任务卡片进度超 100%（如 102/100），实际被执行了两轮完整 `loop_count`。

**根因链**：
1. `enqueue()` 写 DB（`status=queued`）但调用方对象仍为 `idle`
2. `dequeue(脏对象)` → `_validate(idle→running)` 抛出 `InvalidTransition`
3. 回退时创建孤儿 `TestRunRecord`（TaskCard 未被升到 `running`，卡在 `queued`）
4. `finalize(queued→done)` 再次 `InvalidTransition`，结果已入库但状态未变
5. `_schedule_next_queued` 再次取出仍为 `queued` 的卡片 → 第二轮满轮执行
6. 前端不重置计数 → `pass+fail` 跨 run 累加 → 超 100%

**修复模式**：

```python
# ✅ enqueue 后刷新调用方对象
sm.enqueue(tc_card, dev_serial)
tc_card.refresh_from_db(fields=["status", "outcome", "running"])
return sm.dequeue(tc_card, ...)
```

```python
# ✅ dequeue 防御：用 DB 最新实例校验
fresh = TaskCard.objects.select_for_update().get(pk=tc_card.pk)
_validate(fresh, "running", "")
```

```python
# ✅ finalize 兜底：queued 态有结果时先补 queued→running→done
if tc_card.status == "queued" and has_results:
    _save_transition(tc_card, "running")
_save_transition(tc_card, "done")
```

**前端加固**（防御层，不替代后端修复）：
- 新 `runId` 绑定时 `initTaskProgress()` 清零
- 展示 `Math.min(pass+fail, total)` / `Math.min(100, progress)`

**How to apply:** 涉及状态机 + ORM 写入时，**写入后必须 `refresh_from_db()` 再传给下游**。`_validate()` 必须用 DB 最新实例而非调用方入参。`finalize` 必须有兜底逻辑处理卡在中间态的记录。
