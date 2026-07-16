---
name: test-runner-race-conditions
description: 执行引擎 26 个问题中的竞态条件/资源泄漏/静默吞异常模式 — AI 改动 runner 代码时的检查清单
metadata: 
  node_type: memory
  type: project
  originSessionId: f1410bd3-1472-4dd6-9403-e8f5d0bdfa1f
---

## 执行引擎代码审查模式（每次改动检测）

> 来源：全模块审查发现 26 个问题（已修复）。以下模式容易重现，每次改动时必须检查。

### 竞态条件（4 类模式）

| 模式 | 症状 | 修复 |
|------|------|------|
| **check→act 非原子** | 队列任务丢失：`is_device_busy()` 与 `mark_device_busy()` 之间被其他协程插入 | 每设备 `asyncio.Lock` 保护整个 check→dequeue→mark 序列 |
| **DB 写后内存脏对象** | 状态机 InvalidTransition：`enqueue` 写 DB 后调用方对象未刷新 | `refresh_from_db()` 或用 `select_for_update()` 返回的新实例 |
| **预检登记晚于协程启动** | 恢复逻辑看不到新任务：`_preflight_runs` 在 `create_task` 之后登记 | 先登记再 `_spawn_bg` |
| **并发映射删读** | `finalize()` 删映射 vs `list_active()` 读映射 → KeyError | 入口处快照 `client_tid`，映射在 finalize 后再清理 |

### 资源泄漏

| 模式 | 症状 | 修复 |
|------|------|------|
| **异常路径不释放** | 用例加载失败时 DB 设备锁泄漏 | 所有异常分支补 `dp_release_device` + `_schedule_next_queued` |
| **队列不前进** | 设备仍 busy 时过早调度 → `_start_next_queued` 空跑；finally 因 `run_completed=True` 不再调度 | finally 中**无条件** `_schedule_next_queued` |

### 静默吞异常

| 反模式 | 修复 |
|--------|------|
| `except: pass` / `print(e)` | 统一 `logging.getLogger("test_runner.bg").exception()` |
| 适配器各方法错误处理不一致（有的 re-raise，有的吞） | 统一 log + re-raise |
| `executor._do_wait` 绕过适配器直接调 u2 | 改走 `adapter.exists()` / `get_text()` |

### 数据完整性

| 问题 | 修复 |
|------|------|
| `TestResult` 表 0 行：`runner.py` 只写 `state.all_results` 未填充 `run_model.case_results`，`persist()` 遍历空列表 | 每轮迭代 `append(TestResult(...))` 到 `run_model.case_results` |
| 异常时 `run_model.finished_at` 不设置 | except 分支补 `finished_at` |
| WebSocket 鉴权失败无 close code | `close(code=4001, reason=...)` |
| `api.py:persist_results` 死代码 + FK 赋值错误 | 改为接收 `TestRunRecord` 实例 |

**How to apply:** 修改执行引擎代码后，逐项检查：是否有 check→act 间隙？异常路径是否释放设备？try 块内是否 `await` 了可能导致状态不一致的操作？所有 `except` 是否至少打了日志？
