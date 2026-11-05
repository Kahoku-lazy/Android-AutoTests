## 1. 设备状态与当前设备

- [x] 1.1 `backend/apps/device_pool/manager.py`：`update_device_status()` 加 10 秒 TTL 缓存与双检锁，真实扫描拆到 `_sync_device_status()`；新增 `reset_status_sync_cache()`。
- [x] 1.2 `backend/apps/device_pool/views.py`：`/devices/current` 的 ADB 探测抽成 `_probe_current_device()` 并缓存 10 秒。
- [x] 1.3 `frontend/src/modules/task-list/composables/useTaskPublish.ts`：挂载时只预拉智能体（KB 级响应），设备列表改为打开弹窗才加载（避免页面挂载即触发 ADB 同步）。

## 2. 报告

- [x] 2.1 `backend/apps/task_list/views.py`：运行中报告 2 秒短缓存（键含 max_seq），终态保持 600 秒。
- [x] 2.2 `backend/apps/task_list/task_reports.py`：报告列表去 `select_related`、只取展示列、扫描 1000 / 返回 500、线路名 SQL 侧 JSON 提取。

## 3. 串口日志

- [x] 3.1 `frontend/src/modules/serial-log/helpers/log-port-lines.ts`：默认 tail 2000 → 500（选项保留 1000/2000/5000）。
- [x] 3.2 `frontend/src/modules/serial-log/composables/useLogPorts.ts`：`refreshLines` 加在途守卫。
- [x] 3.3 `backend/apps/serial_log/views.py`：`reconcile()` 10 秒节流（列表与日志行共用）。

## 4. 列表与首屏

- [x] 4.1 `backend/apps/case_manager/api_projects.py`：项目列表 `annotate(Count("cases"))`，`serialize_project` 优先读注解。
- [x] 4.2 `backend/apps/workflow/api.py`：原型列表 `annotate(Count("documents", filter=支持类型))`。
- [x] 4.3 `frontend/src/modules/ai-assistant/index.logic.ts`：`onActivated` 仅在已加载过时刷新，消除首挂载双请求。

## 5. 验证

- [x] 5.1 后端相关测试：`tests/api/test_devices.py`、`tests/api/test_task_report*.py`、`tests/api/test_task_event_flow.py`、`tests/api/test_serial_log_api.py` 全绿。 实测：37 passed。另有 5 条 case/workflow 用例失败，已用 `git stash` 只回退本变更文件复跑，确认是 HEAD 上已存在的失败（`create_definition` 签名与 workflow digest 结构），与本变更无关。
- [x] 5.2 前端目标测试：`npx vitest run tests/task-list tests/serial-log tests/ai-assistant --maxWorkers=2` 全绿。 实测：25 文件 / 177 passed。
- [x] 5.3 实测对比：`/devices/` 167→**42ms**（10s 内二次请求）、`/devices/heartbeat/` 130–208→**47ms**、`/devices/current/` 508→**44ms**（缓存命中）、`/reports/` 51→**29ms**、`/cases/projects/` 56→**38ms**；`list_projects` 与 `list_prototypes` 各 **1 条查询**（原 1+P），`build_report_list` **4 条固定查询**。
- [ ] 5.4 `python run.py check` 阻塞项全绿（当前受并行登录页改名影响，见变更说明）；`openspec validate optimize-hot-endpoints --strict` 通过。 现状：`validate --strict` 通过；门禁 22/23，唯一失败仍是 `LoginView.hero.spec.ts` 的旧品牌断言（外部未提交改动）。
