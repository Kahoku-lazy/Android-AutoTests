## 1. 后端：轮次只下发一份

- [x] 1.1 `backend/apps/task_list/task_reports.py`：`_rounds()` 给每个轮次写入 `round_id`（下标），`_flow_cases()` 改为输出 `round_ids` 而不是内嵌 `rounds`。验证：`GET /api/tasks/142/report/` 的 `data.cases[i]` 无 `rounds` 键，`round_ids` 合计 156。
- [x] 1.2 同一响应里 `data.rounds` 只出现一次完整轮次。验证：响应 9,694,780 B → **4,882,364 B（−49.6%）**。

## 2. 后端：终态缓存 + ETag

- [x] 2.1 `views.py` 的 `TaskReportAPIView` 增加缓存读取：键 `task-flow:{task_id}:{max_seq}`，只对终态任务写缓存，TTL 600s。验证：连续两次请求 **256ms / 230ms**，`data` 深度相等。
- [x] 2.2 响应带 `ETag`（明文信封的 sha1）；`If-None-Match` 命中返回 304 空体。验证：`304`、`len(content)==0`。缓存里直接存「明文 + gzip + etag」，命中不再重渲染。
- [x] 2.3 `running` / `pending` 不写缓存；重跑后 `max_seq` 变化使旧键失效。验证：`test_running_task_flow_is_not_cached` 两次都重建。
- [x] 2.4 重新生成 `openspec/openapi.yaml`（`task_flow_report` 增 304）。验证：`openapi-schema`、`openapi-coverage` PASS。

## 3. 前端：默认折叠 + 轮次分页 + 按需渲染

- [x] 3.1 `TaskDetailPage.vue`：`openCases` 初始只含下标 0；按 `round_ids` 关联 `rounds`，用例展开与轮次展开均改 `v-if`（折叠即不挂载）。验证：12 个用例只有 1 个展开，首屏 `.flow-item` 为 0。
- [x] 3.2 每个用例独立的轮次页码，每页 20 条，展示「第 X / Y 页」与上一页 / 下一页。验证：`task-report-pagination.spec.ts` 6 条用例通过（第 2 页 = 21–40、越界夹取）。
- [x] 3.3 `TaskDetailPage.style.css` 给 `.flow-case` 加 `content-visibility: auto` 与 `contain-intrinsic-size`。验证：滚动无抖动。

## 4. 测试

- [x] 4.1 后端：`test_task_event_flow.py` 改按 `round_ids` 取轮次并断言 `cases` 不再含 `rounds`；`test_report_envelope.py` 新增终态缓存、ETag/304、运行中不缓存三条。验证：18 passed。
- [x] 4.2 前端：`frontend/tests/task-list/p0/task-report-pagination.spec.ts` 覆盖 `caseRoundsById` / `reportPageCount` / `reportPageSlice`。验证：6 passed，`vue-tsc` 无错。

## 5. 验收与门禁

- [x] 5.1 接口实测：缓存命中 **230–256ms**（目标 <300ms 达成）；响应 **4.66MB**（目标 <5MB 达成）。**首次未命中仍约 3.8s 构建 + 0.43s 渲染**——根因是 17.4 万行事件扫描，属 P1「事件入库收敛」范围，不在本变更内。
- [x] 5.2 浏览器实测（Playwright）：首屏 **12.8s → 1.20s**、稳定 **14.8s → 1.67s**、DOM **60,187 → 357**、默认只展开 1 个用例。
- [x] 5.3 `python run.py check`：阻塞项 **20/22 PASS**。2 项红项为并发会话在改的文件，非本变更：`ruff-engines-format` → `engines/agents/messaging/billing.py`；`prettier-ts` → `frontend/src/modules/ai-assistant/helpers/assistant-cards.ts`。本变更文件 `prettier` / `ruff-format` / `ruff-lint` / `vue-tsc` / `vitest` / `vite-build` 全 PASS。
- [x] 5.4 `openspec validate optimize-task-report-payload --strict` 通过后归档。
