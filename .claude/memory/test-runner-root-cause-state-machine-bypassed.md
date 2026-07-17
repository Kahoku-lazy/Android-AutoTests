---
name: test-runner-root-cause-state-machine-bypassed
description: "执行引擎\"改了多次还是用不了\"的根因——state_machine被架空+u2阻塞无超时+前端静默吞错"
metadata: 
  node_type: memory
  type: project
  originSessionId: 6c4ba830-229b-432d-9a45-6fdab50ee7eb
---

## 修复状态(2026-07-09 已完成)

P0-1~P0-4 已修复并验证:
- P0-1:views.py 所有裸 `.update(status)` 已改走 state_machine(enqueue/dequeue/complete/fail/cancel),统一 idle→queued→running。shell 断言验证:原子驱动、status/running 恒一致、非法转换被拦截。
- P0-2:device_connect.py 把 u2 `HTTP_TIMEOUT` 从 300→20s(卡死操作快速失败);u2_recovery.is_u2_crash 补超时关键词+类型识别;adapter.click 容错。注:u2 的 `DeviceError` 继承自 u2 自定义的 `BaseException(Exception)`,能被 `except Exception` 捕获(勿被源码 `class DeviceError(BaseException)` 误导)。
- P0-3:views.py 3 处 fire-and-forget create_task 改走 `_spawn_bg`(保存引用+异常日志);delayed_execute 按 run_id 可被 stop 取消。
- P0-4:index.vue/TaskDetail.vue 写操作 catch 改为 ElMessage.error(删除失败不再假成功);高频自动保存用 console.error 避免 toast 刷屏。

**未验证**:P0-2 的"真实 u2 卡死时停止 20s 内生效"需连真机;当时无设备,仅验证了代码正确性。下次有设备时应实测:执行长等待用例→点停止→确认 ≤20s 变 done/stopped。

## 根因(历史记录)

执行引擎不是某个单一 Bug,而是设计断层叠加的系统性问题。核心矛盾:**`state_machine.py`(258行)设计完善但从未被接入主执行路径**——`views.py` 中所有 TaskCard 状态转换都是 `TaskCard.objects.filter().update()` 直写 DB,完全绕过状态机的 `enqueue()/dequeue()/complete()/fail()`。

## 六大断裂点

1. **状态机被架空**(最严重) — state_machine.py 的全量方法只有 `recover_orphans()` 被调用(apps.py 启动恢复),enqueue/dequeue/complete/fail 从未被主路径使用
2. **u2 阻塞无超时导致停止按钮失效** — u2 同步调用卡死时 `adapter.stopped()` 检查点永远走不到,停止按钮点下去没反应
3. **asyncio.create_task fire-and-forget** — 3 处不保存 task 引用,无法取消/监控
4. **队列非持久化** — `_device_queue = {}` 纯内存,重启丢失
5. **前端写操作静默吞错** — 8 处 `catch {}` 无 ElMessage.error()
6. **原子性缺失** — TaskCard+TestRunRecord 非同一事务更新

## 修复优先级

P0(必须修):①接入 state_machine 到 views.py 主路径 ②u2 阻塞操作加超时 ③保存 asyncio task 引用 ④前端写操作报错
P1(应该修):⑤队列持久化 ⑥WebSocket 自动重连

**Why:** 多次修改都在修 views.py 里的状态更新逻辑(影子),但从未消除根因(views.py 绕行 state_machine 直写 DB)。只要 TaskCard 的 status/running 还能被任意 `.update()` 绕过状态机直接写入,漂移就是时间问题。

**How to apply:** 修复执行引擎时必须先动 state_machine 的接入,不允许在 views.py 中新增裸 `.update()` 调用。所有 TaskCard 状态转换必须走 state_machine 的命名方法。

相关: [[test-runner-statemachine-not-wired]] [[write-ops-catch-must-report]] [[full-stack-verification-workflow]]
