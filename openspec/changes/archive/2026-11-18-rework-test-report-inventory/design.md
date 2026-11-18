# Design: rework-test-report-inventory

## Context

动机见 proposal.md - Why。方案需要的现状事实：

- **两条报告链路在「完成时」都已把定位写进 DB**：
  - SOP：`task_runner.run_task_async` 正常收口时经 `_report_locator` 把 `report_run/report_name/report_path` 写进 `Task.result`（JSON 文本）；取消/异常路径不写定位，引擎侧也不产 HTML（`run_sop` 在事件流正常走完后才 `recorder.finish → HtmlReportRenderer.save`）。
  - 智能体：`assistant_threads._run_turn` 仅在 DONE 时 `finish_message(report_id=…)`；`report_id` 是 `logs/agents/assistants/<assistant_id>/<thread_id>/` 下的时间戳目录名。取消/异常轮次虽然 `finally` 里落了文件，但消息上无登记。
- 用例身份冻结在 `Task.case_identity`，展示文案由 `task_list/case_identity.py` 的 `case_identity_label/rows` 统一产出；`bug_manager/api.py` 已有跨 App 复用该模块的先例。
- 前端 `/reports` 与 `/agent-reports` 路由均未挂进 `router.ts`，侧栏无入口；`report-generator` 模块代码仍在（775 行单文件页面）。
- 读取通道已就位：SOP 走 `AgentReportView`（`REPORT_ROOT` 白名单，JSON 返回正文）；智能体走 `AssistantThreadLogFileView`（一次性 ticket，`FileResponse` 直出 HTML，规格 `assistant-log-ticket`）。
- 约束：`report_generator` 只读、不写业务表；跨 App 只读 Model 或对方 api.py；`platform-load-budget` 对 `/api/reports` 的扫描上限 1000 / 返回上限 500 继续适用；engines 零改动；前端 Doodle Craft 令牌与共享件复用。

## Goals / Non-Goals

**Goals:**

- 用「DB 登记即索引」重建报告列表：一次请求聚合两来源，元数据全部来自库内，无磁盘扫描。
- 前端报告台账页挂回路由与侧栏，查看报告完全复用既有通道。
- 同批清理无调用方的遗产代码与死表，收敛规格漂移。

**Non-Goals:**

- 不改报告生成链路（engines、task_runner、assistant_threads 一行不动）。
- 不新增报告读取端点、不做报告级运营功能（备注/保留策略/删除）。
- 不修复与本变更无关的既有规格漂移（如 `ai-task-publishing`、`frontend-l2-page-region` 里对已下线 `/tasks/:id` 的引用）。
- 不做服务端分页；沿用 BUG 单/旧报告页「服务端限量返回 + 前端分页」口径。

## Decisions

### D1. 数据源：DB 登记驱动，不扫磁盘、不建新表

列表 = 「带定位的终态 Task」∪「带 report_id 的助手消息」。

- **备选 B（扫磁盘）**：目录名里没有任务 ID/用例名/助手名，终究要回库 join；目录无限增长每次全扫；取消的智能体轮次有文件无登记，扫出来反而违反「仅已完成」。放弃。
- **备选 C（新建报告登记表）**：两处登记已经是索引，第三份索引带来双写一致性与存量回填成本，当前无报告级功能诉求。放弃；将来若出现报告备注/保留策略再立项。
- 代价：文件被手工删除时列表行仍在 → 打开时既有端点返回 404，前端按「报告不存在」提示（TaskBoard 已有同款处理）。接受。

### D2. 聚合落点：report_generator 新增只读聚合模块，退役 task_list/task_reports.py

- 新模块 `backend/apps/report_generator/report_inventory.py`：只读 `task_list.Task`、`ai_assistant.AIAssistantThread/AIAssistantMessage/AIAssistant` 四张 Model，复用 `task_list.case_identity` 两个纯函数（bug_manager 先例）。视图只分发，聚合逻辑不进 views。
- **备选（续写 task_list/task_reports.py）**：该模块是旧任务卡聚合 + 已下线详情流程的载体，`build_task_flow/report_cache_meta` 全仓无调用方；把智能体报告查询塞进 task_list 会让任务域背上助手域职责。整体退役，`case_identity.py` 保留。
- `report_generator` 与 `report-generator` 前后端 AGENTS.md 的「列表读 task_reports」契约段随实现同步更新。

### D3. 查询形状与限量

- SOP 侧：`Task.objects.filter(status__in=[completed, success, failed]).only(轻量列).order_by("-finished_at")[:1000]`，Python 侧解析 `result` JSON 取定位（与 `bug_manager._report_locator` 同款做法；`result` 是 TextField，不做 DB 侧 JSON 提取），无定位的行丢弃。
- 智能体侧：`AIAssistantMessage.objects.filter(role="assistant").exclude(report_id="").select_related("thread").order_by("-created_at")[:1000]`；助手名按 `assistant_id` 集合一次批量查名片，缺失回落空串。
- 两来源合并后按生成时间倒序，`source/keyword/start_date/end_date` 在服务端过滤，返回 ≤500 行；`summary` 对过滤后集合计数。关键字匹配：SOP 行匹配 `case_label/task_title/task_id`，智能体行匹配 `assistant_name/assistant_id`。
- 不联表读智能体大字段（名片只取 `assistant_id/display_name`），满足 platform-load-budget。

### D4. 查看报告：前端按来源分流，复用两条既有通道

- SOP 行：`fetchTaskReport(run, name)`（task-list/api 已导出）→ blob → 新标签打开，与 TaskBoard/BugDetailDrawer 完全同款。
- 智能体行：`issueLogTicket(threadId, reportId)` → `threadLogUrl(threadId, reportId, ticket)` → 新标签直开 HTML（ticket 通道避免 blob 相对字体问题，规格已定）。
- 跨模块复用对方 `api.ts` 导出函数是既有模式（bug-manager 复用 task-list 的 fetchTaskReport）；不新拼地址、不新增后端端点。

### D5. 前端入口与页面

- `sidebarNavConfig.ts`：ai-tasks 组 items 追加 `{ path: "/reports", icon: <已登记图标>, label: "测试报告" }` 于 `/bugs` 之后；`MOD_COLORS["/reports"]` 已存在（`--c-report`），与同组三色互异。图标名实现时在运行时子集核验（侧栏图标一致性测试兜底）。
- `router.ts`：导入 report-generator 路由（保留 `/reports` 单路由，不注册详情路由）。
- 页面重建为报告台账：WorkbenchHeader + 「报告概览」KPI 三卡 + 「测试报告」分区（FilterTabs 来源筛选 + 关键字/日期 + AppTable 单表 + 前端分页）。身份列按来源切换：SOP → 用例名称 + 任务 ID；智能体 → 助手编号 + 名称。全部走 Doodle Craft 共享件与令牌；单文件超 500 行按规范拆 components/composables/constants。
- 面包屑/返回：本页是侧栏直达的单页工作台（非 Hub 子页），按 `frontend-doodle-subpage-nav` 不伪造祖先链；报告以新标签打开，列表路由不变。

### D6. 遗产退役清单

- 后端：`/api/reports/{filename}` 与 `{filename}/content` 两端点、`Report/ReportTemplate` 模型与 `rg_*` 表（迁移 drop，反向迁移重建空表）、`service.py`、`api.py` 的 `save_report/ReportGenerator` 导出、`task_list/task_reports.py`。
- 前端：`modules/agent-reports/` 整模块 + `frontend/tests/agent-reports/`；`sidebarNavConfig.ts` 的 `/agent-reports` 色项；report-generator 旧页面代码与旧测试重写。
- 后端 `tests/report/` 仅存 .pyc 残骸，随新测试落地清理。

## 模块防火墙自检

- **跨 App import**：report_inventory 只读 `task_list.Task` Model、`ai_assistant` 三张 Model（只读 ✅）；复用 `task_list.case_identity` 纯函数——与 `bug_manager/api.py:18` 同款既有先例，非 service/runner/views；不 import 任何对方 service/views/runner。
- **写库收敛**：本变更零业务写库；唯一 ORM 写是 report_generator 自身退役迁移（drop 本 App 的 rg_* 表），不涉他 App。
- **engines 边界**：零改动；不新增路径常量，读取通道继续用 `REPORT_ROOT/ASSISTANT_LOG_ROOT` 既有白名单。
- **前端**：不直连数据库；报告页只读，无写操作；HTTP 唯一出口走模块 api.ts（复用对方 api.ts 导出为既有模式）。
- **新跨模块依赖**：仅「report_generator 只读 ai_assistant Model」一条新增方向，属全局规则允许的跨 App 读 Model，无需走 api.py；已在上文列明。

## Risks / Trade-offs

- [文件被删/磁盘清理后列表行仍在] → 打开时 404，前端「报告不存在」提示，不影响其它行；不做存在性预检（避免每行 stat）。
- [result JSON 解析在 Python 侧，千行上限内逐行解析] → 与 bug 同步同款口径，扫描上限 1000 兜底；只 `.only()` 轻量列 + result，不读大字段。
- [BREAKING 信封变更] → 前后端同批切换，`/api/reports` 无外部消费方（旧前端页已不可达）；CI 契约测试同批更新。
- [drop rg_* 表不可逆数据] → 两表全仓无写入方、确认为空表后才 drop；反向迁移重建表结构，回滚不丢业务数据（业务数据本就不在其中）。
- [助手名片删除后名称缺失] → 编号照常显示、名称回落空串，规格已定场景。
- [取消的智能体轮次有文件却不进台账] → 有意为之：与「仅正常完成登记」一致，符合需求 3；对话栏内仍可按既有日志列表查看。

## Migration Plan

1. 后端：新聚合模块 + 视图重写 + 退役迁移（`makemigrations` 后人工核对 drop 语句）→ `manage.py check` / `makemigrations --check` / 相关单测接口测。
2. 前端：页面重建 + 路由挂载 + 侧栏增项 + agent-reports 退役 → typecheck / lint:styles / vitest。
3. 本地门禁 `python run.py check`，逐文件暂存提交，推送 Kahoku 后确认 CI 6 job 全绿。
4. 回滚：git revert 对应提交 + 反向迁移重建 rg_* 空表；报告生成链路未动，回滚无运行态风险。

## Open Questions

（无——图标具体名、组件拆分粒度等属实现期可定细节，不改规格与方案。）
