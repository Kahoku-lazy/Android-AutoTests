---
name: test-runner-currentthreadexecutor-root-cause
description: 后台任务不执行的根因：CurrentThreadExecutor 在 HTTP 响应后失效
metadata: 
  node_type: memory
  type: project
  originSessionId: 823d96a4-f98d-41e8-84da-b465406cb1aa
---

# CurrentThreadExecutor 导致后台任务不执行

**发现日期**: 2026-07-10
**严重级别**: 🔴 P0 阻塞

## 根因

`asgiref.sync.sync_to_async` 默认使用 `thread_sensitive=True`，在 Daphne 异步视图的请求上下文中会捕获一个 `CurrentThreadExecutor`。HTTP 响应返回后，该 executor 被销毁。当后台任务（`delayed_execute` → `_execute_tests`）调用 `@sync_to_async` 装饰的函数时，抛出：

```
RuntimeError: CurrentThreadExecutor already quit or is broken
```

导致整个后台任务链断裂：`start_run()` 失败 → 设备锁泄漏 → TaskCard 不更新。

## 修复

`apps/test_runner/views.py` 中所有 `sync_to_async` 调用改用 `thread_sensitive=False`：

```python
from asgiref.sync import sync_to_async as _original_sta

def _sta(fn):
    return _original_sta(fn, thread_sensitive=False)

_bg_sync = _sta          # @_bg_sync 装饰器
sync_to_async = _sta      # sync_to_async(func)(args) 内联调用
```

这样强制使用默认线程池而非请求级 CurrentThreadExecutor。

## 验证

修复后完整链路正常：
- `POST /api/runner/run` → `delayed_execute` → `_execute_tests` → `start_run()` 创建 TestRunRecord → `runner.run()` 执行用例 → `dp_release_device OK`
- 执行时长 ~35s（1 轮 × 9 步）
- 设备正确释放：ONLINE

**Why**: 这是阻塞平台核心功能的 P0 缺陷。所有通过 HTTP 创建的任务都无法执行，设备锁泄漏导致后续任务全部排队。

**How to apply**: 所有在异步视图中使用 `sync_to_async` 的后台任务都必须显式设置 `thread_sensitive=False`。应写一条代码审查规则。
