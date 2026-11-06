## Why

平台还有几处「每次打开页面都要等」的热点：设备列表/心跳在请求线程里同步跑 ADB（列表 120–205ms、心跳 130–208ms，无线未就绪时单台可到十几秒，任务清单页挂载也会调它）；运行中任务每 3 秒重建整份报告（3MB / gzip 475KB、构建 420ms）；报告列表无上限且联表取智能体全列；串口日志自动刷新每 5 秒拉 2000 行且无在途守卫；项目/原型的列表按行 `COUNT` 形成 N+1。

## What Changes

- **设备状态同步节流**：`update_device_status()` 10 秒内复用上次 ADB 扫描结果（列表/心跳共用），并发请求只跑一次；`/devices/current` 的 ADB 探测加 10 秒缓存。
- **任务清单页不再预拉设备**：设备与智能体改到「新建任务」弹窗打开时按需加载（弹窗本来就会加载）。
- **报告**：运行中报告加 2 秒短缓存（多查看者共用一次构建，事件序号变化自然换键）；报告列表去 `select_related`、只取展示列、扫描上限 1000 / 返回上限 500。
- **串口日志**：自动刷新默认 2000 行 → 500 行；浏览器端在途守卫；后端 `reconcile()` 10 秒节流（GET 不再每条请求启停监听线程）。
- **列表聚合去 N+1**：项目列表与原型列表的用例/文档数改一次 `annotate(Count)`。
- **AI 助手首屏去重**：`onMounted` 与 `onActivated` 各拉一次列表 → `onActivated` 只在从其它页返回时刷新。
- 不改页面视觉、不改接口路径与响应字段语义（仅新增上限与缓存时效）。

## 关联文档

- PRD：`PRD-平台总需求` 五、非功能约束（可观测与响应性）、一、1.4 产品边界（设备管理 / 任务清单 / 测试报告 / 串口日志）。
- 既有规格：`ai-task-device-dispatch`、`agent-task-flow-report`、`device-log-port-console`、`bug-ticket-management`。

## Capabilities

### New Capabilities

- `platform-load-budget`: 热路径的响应预算——设备状态同步节流、报告短缓存与列表上限、串口日志读取有界、列表计数一次聚合。

### Modified Capabilities

（无）

## Impact

- 后端：`backend/apps/device_pool/{manager.py,views.py}`、`backend/apps/task_list/{views.py,task_reports.py}`、`backend/apps/serial_log/views.py`、`backend/apps/case_manager/api_projects.py`、`backend/apps/workflow/api.py`。
- 前端：`frontend/src/modules/task-list/composables/useTaskPublish.ts`、`serial-log/{helpers/log-port-lines.ts,composables/useLogPorts.ts}`、`ai-assistant/index.logic.ts`。
- 测试：设备/报告/串口/项目/工作流相关既有测试；新增列表计数与缓存行为断言。
- 非目标：ADB 发现改后台任务（本次只做节流）；报告增量协议（`since_seq`）；前端分页/虚拟滚动。
