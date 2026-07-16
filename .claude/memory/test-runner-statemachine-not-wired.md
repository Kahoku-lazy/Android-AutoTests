---
name: test-runner-statemachine-not-wired
description: 执行引擎 state_machine.py 写好了但没接入主路径，导致 status/running 双源不一致 + 崩溃恢复漏僵尸
metadata: 
  node_type: memory
  type: project
  originSessionId: cb149e00-79b9-47cd-8c23-7cb3d75ace4e
---

执行引擎(test_runner)设计文档描述的架构与实现严重脱节（2026-07-09 复查发现）：

1. **state_machine.py 是死代码**：258 行完整的 RunStateMachine(enqueue/dequeue/complete/fail/cancel)，文档 §6 声称"所有状态变更必须通过它、禁止直接 task.status="。但全项目只有 `recover_orphans()` 被 apps.py ready() 调用；views.py 主执行路径全程直接 `TaskCard.objects.filter().update(status=...)`，违反自己的设计原则。

2. **status/running 双源不一致**：TaskCard 有 `status` 字段和 `running` 布尔，两者独立更新会矛盾。实测出现 `status='idle' 但 running=True` 的僵尸卡片。根因：`task_card_save` 接受前端传入的 `running` 但拒绝 `status`（注释"status 后端管理"），前端 `deriveTaskStatus` 又纯用 `running` 判"执行中" → 前端写 running=True、后端 status 停 idle，永久漂移。

3. **崩溃恢复漏僵尸**：`recover_orphans()` 和 views.py `task_card_list` 内联恢复都只查 `status='running'`，漏掉 `status='idle'+running=True`；设备释放只查 `status='BUSY'`，漏掉 `status='ONLINE' 但 occupied_by='runner-*'` 的残留锁。重启后僵尸卡片和残留锁持续存在。

4. **scheduler.py/DeviceScheduler 不存在**（文档列为核心文件，实际 inline 在 views.py）；**无超时/看门狗**（文档 §8问题2 未实现），u2 卡死会阻塞 Daphne worker。

**已正确实现**：_u2_executor 线程隔离(§8问题1)、4张表、10端点、per-device 队列多设备并行。

**2026-07-09 已修复(P0/P1)**：list API 派生 `running=(status=='running')`；save 不接受前端 running；recover_orphans + list 内联恢复补 `Q(status='running')|Q(running=True)`；设备释放去掉 status=BUSY 限制；前端 deriveTaskStatus 移除 caseItems 猜测启发式。已重启+浏览器+真机 E2E 验证：僵尸清零、设备锁释放、idle→running→done 生命周期跑通、UI/DB 一致。

**未修的既有隐患(P1，独立)**：`recover_orphans()` 在 `AppConfig.ready()` 里，**每个 Django 进程启动都会执行**（`manage.py shell`/migrate/任何管理命令）。在 Daphne 有 live run 时跑任何管理命令 → 该进程 ready() 把正在跑的任务判为孤儿、中断并释放设备。修法：ready() 里的恢复只在 ASGI server 进程执行（判 sys.argv 或环境标志）。**教训：调试期间别在 live run 时跑 manage.py shell。**

**How to apply**: 复查"按方案设计的功能是否实现"时，不能只看文件是否存在——要 grep 该模块是否真被主路径 import/调用。状态字段冗余(status+running)必须单一入口原子更新，否则必然漂移。见 [[full-stack-verification-workflow]] [[quality-retrospective-case-manager]]。
