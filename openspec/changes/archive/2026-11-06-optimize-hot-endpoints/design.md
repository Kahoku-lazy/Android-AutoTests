## Context

实测（本机）：`/api/devices/` 120–205ms（响应 444B）、`/api/devices/heartbeat/` 130–208ms、`/api/devices/current/` 318–376ms；三者慢的原因是请求线程里同步跑 ADB 子进程/u2 连接（`update_device_status` 102ms、`heartbeat_sync` 131ms 为同等扫描）。任务详情运行中每 3s 重建报告：3.0MB / gzip 475KB / 构建 420ms（5,758 事件、157 轮）。报告列表无上限且 `select_related("agent")`；串口日志自动刷新 5s × 2000 行无守卫。

## Goals / Non-Goals

**Goals:**

- 消除请求线程里的重复 ADB 扫描；报告构建在多查看者间复用；列表查询数与行数解耦。
- 保持响应字段、状态语义与页面视觉不变。

**Non-Goals:**

- 不把 ADB 发现改成后台线程/定时任务（本次只做 10s 节流，改动面最小）。
- 不做运行中报告增量协议 `since_seq`、不做前端分页/虚拟滚动。
- 不动任务详情页的轮询节奏（仍 3s）。

## Decisions

**1. 状态同步用进程内 TTL 缓存 + 双检锁。**

`update_device_status()` 只做节流，真实逻辑抽到 `_sync_device_status()`；10 秒窗口内的列表/心跳共用一次扫描。选缓存而不是后台线程：不引入线程生命周期与 Django 连接问题，失败仍按原逻辑抛给调用方；多进程部署时每个进程最多各扫一次，仍远好于每请求扫一次。`reset_status_sync_cache()` 供测试与显式刷新。

**2. `/devices/current` 只缓存 ADB 探测结果（10s/设备）。**

读分辨率与前台应用要连一次设备，属于展示型信息；10 秒陈旧可接受。前端当前没有调用方，保留接口与语义，避免影响可能的调试用法。

**3. 任务清单页不再挂载即拉设备。**

`useTaskPublish` 原本 `onMounted` 拉 devices+agents，打开弹窗又拉一遍。删掉挂载预拉，全部改由 `watch(dialogVisible)` 触发（打开弹窗才加载 + 30s 轮询）。

**4. 运行中报告 2 秒短缓存，键含最大事件序号。**

键 `task-flow:{id}:{max_seq}` 保证事件增长后自然换键；2 秒内多个查看者共用一次构建。终态仍 600 秒。不改变 gzip/ETag/304 行为。

**5. 报告列表去联表、限上限。**

线路名用 `KeyTextTransform` 从 `route_configs` 提取（同任务清单做法），任务只取展示列；扫描 1000、返回 500 并保留真实汇总计数。

**6. 串口日志三件小事。**

默认 tail 2000→500、前端在途守卫、后端 `reconcile()` 10 秒节流。

**7. 项目/原型计数改 annotate。**

`Count("cases")` / `Count("documents", filter=支持类型)`；`serialize_*` 优先读注解，未注解时回退单条 count（创建/详情路径仍正确）。

**8. AI 助手首挂载去重。**

`onMounted` 拉取；`onActivated` 仅在 `loadedOnce` 后（从其它页面返回）刷新。

## 模块防火墙自检

- 跨 App：`task_reports` 仍只读 `ai_assistant` Model（`AIAgent`），不 import views/service；`case_manager`/`workflow` 只改本 App 查询。
- 写库：本变更只读聚合与缓存；`reconcile()` 的写仍在 `serial_log/api.py`（经 `port_service`），只是降低了调用频率。
- 前端：只改加载时机与轮询守卫。

## Risks / Trade-offs

- [10 秒缓存导致状态最多陈旧 10 秒] → 心跳本就 30 秒一次；用户主动操作（连接/断开/锁定）走写接口后立即落库，不受缓存影响。
- [测试期望每次调用都重新扫描] → 现有设备测试用真实 DB 断言字段；如出现脏读，用 `reset_status_sync_cache()` 在 fixture 里清缓存。
- [运行中 2 秒缓存让极端情况下看到略旧事件] → 轮询 3 秒，最大延迟不超过 5 秒；事件序号变化即换键。
- [报告列表 500 条上限] → 超出部分依赖筛选条件收窄；页面当前数据量远小于上限。
- [串口日志默认 500 行] → 仍然可选 1000/2000/5000，用户可手动调大。
