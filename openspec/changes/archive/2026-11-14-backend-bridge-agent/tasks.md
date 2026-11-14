## 1. 包骨架与路径

- [x] 1.1 新增 `engines/backend_bridge/__init__.py`、`agents/__init__.py`、`reports/__init__.py`、`token_usage/__init__.py`（11 字段 docstring，`类型` 取 `Agent 能力模块`）。验证：`python -c "import engines.backend_bridge"` 成功；docstring 检查 0 error
- [x] 1.2 新增 `reports/paths.py`：`REPORT_ROOT` 唯一常量 + `ensure_run_dir(role)` 创建本次子目录。验证：单测断言 `REPORT_ROOT` 末三级为 `logs/agents/backend_bridge`，且 `ensure_run_dir("ui_executor")` 自动建目录

## 2. 平台角色

- [x] 2.1 新增 `agents/ui_executor.py`：`build_ui_executor(model_short=...) -> (AgentBundle, ObservationMiddleware)`，内部只调 `ae_harness` 的 `create_agent` 与 `build_adb_tools`。验证：单测断言返回的智能体带设备工具、`api_key_env` 非空（无密钥时 skip）
- [x] 2.2 导入守卫：本目录不得 import `ae_harness.assistant` / `ae_harness.workflow` / `django` / `apps` / `backend`。验证：单测扫描本目录所有模块的导入

## 3. 运行入口

- [x] 3.1 新增 `run.py` 的 `UiRunResult`（frozen）：`final_text`、`report_path`、`log_path`、`tokens`、`by_api_key_env`、`usages`。验证：单测构造并断言字段
- [x] 3.2 新增 `run_ui_task(task, *, model_short, report_root=None) -> UiRunResult`：建角色 → 记录器（带观测）→ 跑流 → 收尾 → 出报告 → 返回结果；全程不打印。验证：单测断言返回值字段类型；真机跑一次确认报告产出
- [x] 3.3 报告目录按需创建：`report_root` 不传时用 `REPORT_ROOT`，不存在则创建。验证：单测在临时目录下断言自动创建

## 4. 测试与门禁

- [x] 4.1 新增 `tests/engines/backend_bridge/unit/`（含 `__init__.py`）三个用例文件：路径、角色装配、导入守卫。验证：`python -m pytest -c tests/pytest.ini tests/engines/backend_bridge -q` 全绿
- [x] 4.2 真机冒烟：`run_ui_task("只回复 OK，不要调用工具")` 跑一次，确认 `logs/agents/backend_bridge/<时间戳>/` 下有 jsonl 与 html，且返回值含 token 四类。验证：读产物 + 打印结果
- [x] 4.3 `python -m scripts.docstrings check --path engines/backend_bridge` 归零。验证：0 error / 0 warn
- [x] 4.4 `ruff check` / `ruff format --check`（engines/backend_bridge + tests/engines/backend_bridge）全过。验证：退出码 0
- [x] 4.5 `python run.py check` 与基线对比无新增失败项。验证：失败项集合与基线一致
- [x] 4.6 确认 `engines/ae_harness/` 零改动。验证：`git status` 中无该目录变更

## 5. 报告可读（后端）

- [x] 5.1 `ai_assistant/reports.py`：列表（新在前）与单文件读取，路径白名单校验。验证：`tests/ai_assistant/unit/test_agent_reports.py` 6 个用例全绿
- [x] 5.2 `ai_assistant/views_reports.py` + 路由：`GET /api/ai/agent-reports/`、`GET /api/ai/agent-reports/<run>/<name>/`，信封 `{status,data}` / `{status,message}`。验证：`python manage.py check` 通过；路由已注册

## 6. 用量入账（后端）

- [x] 6.1 `usage_ledger/api.record_run_usages`：幂等键「来源:执行ID:轮次」，厂商由密钥名推断，单条失败不阻断。验证：`tests/usage_ledger/unit/test_record_run_usages.py` 5 个用例全绿（含幂等与脏数据）
- [x] 6.2 时间戳按 `USE_TZ` 决定是否带时区，与账本其它写入一致。验证：SQLite（USE_TZ=False）下三例写入通过

## 7. 触发入口与收尾

- [x] 7.1 `ai_assistant/management/commands/run_ui_agent.py`：跑一次 → 出报告 → 入账，打印报告路径与四类 token。验证：`python manage.py check` 通过；命令已注册
- [x] 7.2 修复存量阻塞：`engines/agents/config/config.ini` 三个路径由 `temps/engines/...` 改为 `engines/...`。验证：`manage.py check` 通过，`django-check` / `pytest-collect` / `ruff-format` 三个门禁由 FAIL 转 PASS

## 8. 执行报告历史页（前端）

- [x] 8.1 新增 `frontend/src/modules/agent-reports/`：`types.ts` / `constants.ts` / `api.ts` / `helpers/report-meta.ts` / `index.vue` / `index.style.css` / `routes.ts` / `AGENTS.md`。验证：`npm run typecheck` 通过
- [x] 8.2 页面走 Doodle Craft 默认：`WorkbenchHeader` + `DoodleNote` 列表 + `DoodleBtn`，三态用 `SkeletonCard` / `ErrorState` / `EmptyState`。验证：`npm run lint:styles` 中本模块 0 违规
- [x] 8.3 报告正文以 blob URL 新窗口打开，不用 `v-html` 注入。验证：代码审查 + 模块 AGENTS 红线
- [x] 8.4 注册路由（`/agent-reports`）与侧栏入口（AI 功能组末位，模块色 `--c-report`）。验证：`tests/shared/p0/sidebarNavConfig.spec.ts` 6 例全绿
- [x] 8.5 新增纯函数单测 `tests/agent-reports/p1/report-meta.spec.ts`（字节格式化 / 相对时间 / 微倾轮转 / 运行名拆时间）。验证：7 例全绿

## 9. 接入 AI 助手对话（聊天）

- [x] 9.1 `engines/backend_bridge/session.py`：会话层——同一连接复用一个角色，逐轮各出一份报告，设备序列号随消息带上。验证：`tests/engines/backend_bridge/unit/test_session.py` 4 例全绿
- [x] 9.2 `engines/backend_bridge/result.py`：把 `UiRunResult` 抽出，避免会话与入口互相导入。验证：`test_run.py` 仍全绿
- [x] 9.3 `ai_assistant/platform_agents.py`：平台卡片清单、键判定、一轮对话 + 用量入账。验证：`tests/ai_assistant/unit/test_platform_agents.py` 5 例全绿
- [x] 9.4 `WorkflowListView` 合并平台卡片；`WorkflowStreamView` 命中平台键走平台会话，否则回退引擎侧。验证：单测断言清单同时含 `android_ui` 与 `platform_ui`；`manage.py check` 通过
- [x] 9.5 真机：`stream_turn("只回复 OK")` 返回 `OK`，账本写入 `agent:20261114_211723:1`（5047 token / ¥0.00041172）。验证：`ModelUsage` 查询
- [x] 9.6 前端零改动确认：聊天页 `v-for="card in workflows"` 渲染卡片与下拉，无 key 白名单、无写死 `android_ui`；默认选中仍是 `cards[0]`（平台卡排在末位，老用户行为不变）。验证：`grep android_ui frontend/src` 无命中
- [x] 9.7 端到端真机：真实视图层 `GET /api/ai/workflows/` 返回两张卡（`android_ui` / `platform_ui`），`POST /api/ai/workflows/platform_ui/stream/` 返回 `data: HI`。验证：Django 视图直调 + 真实模型

## 10. 平台验收（真机 + 真实浏览器）

- [x] 10.1 事件面板接上：`engines/backend_bridge/event_log.py` 按引擎侧同样的分段标记写过程行，`read_session_events` 无需改动即可读到。验证：`tests/engines/backend_bridge/unit/test_event_log.py` 5 例全绿；浏览器面板显示 5 行
- [x] 10.2 修掉报告接口的双重信封：View 只返回负载本体（`{reports}` / `{report}`），错误改抛 DRF 异常，信封由全局渲染器统一包。验证：真实 HTTP 返回 `{status,data:{reports}}`
- [x] 10.3 前端契约同步：`api.ts` 读 `data.reports` / `data.report.content`。验证：`npm run typecheck` 通过
- [x] 10.4 启动平台并做接口验收：清单两张卡、一轮对话 `data: OK`、事件流 5 行、报告列表与正文（86 KB）、越权路径被拒。验证：`temps/platform_acceptance_probe.py`
- [x] 10.5 浏览器验收：选「UI 执行（平台）」→ 发消息 → 回复出现 → 「模型事件」面板显示 5 行过程；执行报告页 8 张卡，「查看报告」新窗口打开完整 HTML。验证：`temps/browser_shots/*.png`
- [x] 10.6 token 入账确认：真实库 `ai_usage_records` 中 `source=agent` 共 5 行，最新 `agent:20261114_212847:1`（5045/2/4864，5047 token，¥0.00028628）。验证：`ModelUsage` 查询

## 11. 事件面板 L3 与卡片上线日期

- [x] 11.1 事件记录升级为全量颗粒度：思考全文、阶段结论全文、工具入参与输出全文都进日志，增量仍在内存折叠。验证：`tests/engines/backend_bridge/unit/test_event_log.py` 7 例全绿
- [x] 11.2 修正工具负载取值：真实 `ToolCallEndEvent` / `ToolResultEndEvent` 不带名字与负载，改为按 id 从开始事件与增量累积；带图片时标注张数。验证：真机面板出现 `工具入参 adb_app_state {"package": "com.govee.home"…}` 与 `工具结果 adb_app_state success {"status": true…}`
- [x] 11.3 回复窗口给最终结论：一轮的回复取最后一个文本块正文。验证：真机回复为「### 完成说明 …」
- [x] 11.4 两张编排卡片加上线日期：引擎侧 `2026-11-11`、平台侧 `2026-11-14`，接口透出 `released_at`。验证：`GET /ai/workflows/` 两张卡都带日期
- [x] 11.5 前端卡片展示日期并给最新那张标「最新」；默认选中项不变。验证：浏览器截图中 `上线于 2026-11-14` 带「最新」徽标，`android_ui` 仍在首位
- [x] 11.6 事件行支持长文本折行。验证：`tests/ai-assistant/p1/workflow-cards.spec.ts` 6 例 + 浏览器面板折行

## 12. 去掉引擎侧 Android UI 控制角色

- [x] 12.1 `engines/agents/workflow/single/catalog.py` 清空卡片清单（保留清单与键校验），引擎侧编排不再出现在对话页。验证：`list_single_agents()` 返回空；`GET /ai/workflows/` 只剩 `platform_ui`
- [x] 12.2 `session_for` 默认键改为空串，不再保留 `android_ui` 字面量。验证：清单为空时按连接建会话直接报错
- [x] 12.3 单测对齐：引擎侧断言清单为空且未知键报错；平台侧断言清单只有平台卡。验证：`tests/engines/agents/unit/test_single_agent_workflow.py` 8 例、`tests/ai_assistant/unit/test_platform_agents.py` 5 例全绿
- [x] 12.4 前端「最新」徽标只在两张以上时显示，单卡不再标注。验证：`npm run typecheck` + 浏览器截图只剩一张卡且无徽标
- [x] 12.5 `workflow/single/AGENTS.md` 标注清单当前为空、平台角色已迁到 `engines/backend_bridge`。验证：文档与代码一致
