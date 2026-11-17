## 1. 删表迁移（App 仍在册时先行）

- [x] 1.1 新增 `backend/apps/workflow/migrations/0007_drop_tables.py`：`RunSQL` 按 FK 顺序 `DROP TABLE IF EXISTS wf_documents / wf_directories / wf_prototypes`，reverse 为 no-op 并注明数据不可恢复（实测 0 行）。验证：`python manage.py makemigrations --check --dry-run` 无未生成变更
- [x] 1.2 应用迁移并留档：`python manage.py dumpdata workflow --indent 2 -o temps/workflow_backup.json`（0 行空档）→ `python manage.py migrate workflow`。验证：`showmigrations workflow` 全部已应用，且库内查三张表均不存在（shell 查 information_schema / sqlite_master）。**验证结果**：0007 已应用，introspection 查 wf_ 前缀表为 []，留档为 `[]`

## 2. 后端拆除

- [x] 2.1 删除 `backend/apps/workflow/` 整目录（含 migrations、空 AGENTS.md、__pycache__）。验证：目录不存在
- [x] 2.2 `backend/config/settings.py`：INSTALLED_APPS 删 `"backend.apps.workflow"`（同步 App 计数注释）、SPECTACULAR_SETTINGS.TAGS 删 workflow 项。验证：`python manage.py check` 通过
- [x] 2.3 `backend/config/urls.py`：删 `api/workflow/` include。验证：`python manage.py check` 通过，且 `resolve("/api/workflow/prototypes/")` 抛 Resolver404
- [x] 2.4 `backend/apps/dashboard/views.py`：删 `WorkflowDocument` import、`_workflow_stats()` 与 stats 响应的 `"workflow"` 键。验证：`python manage.py check` + `ruff check backend/apps/dashboard` 通过。**验证结果**：本单文件 ruff check / format 全过；`ai_usage.py` 的 I001 属并行改动，不修

## 3. 前端拆除

- [x] 3.1 删除 `frontend/src/modules/workflow/` 整目录（21 个文件）。验证：目录不存在，`frontend/src` 内 grep `modules/workflow` 命中 0
- [x] 3.2 `frontend/src/router.ts` 删 wfRoutes import 与展开；`frontend/src/main.ts` 删 `modules/workflow/tokens.css` 引入。验证：`npm run typecheck` 通过
- [x] 3.3 `frontend/src/shared/components/sidebarNavConfig.ts` 删「页面流」导航项与 MOD_COLORS 的 `/workflow` 项。验证：`npm run typecheck` 通过，该文件 grep `/workflow` 命中 0
- [x] 3.4 仪表盘联动：`modules/dashboard/index.vue` 删「工作流」KPI 卡；`shared/types/dashboard.ts` 删 `workflow` 字段（DashboardStats 与零值结构两处）；`modules/dashboard/composables/useDashboardStats.ts` 删 workflow 零值与映射。验证：`npm run typecheck` 通过。**验证结果**：typecheck 全绿；IconLayers 仍有消费故保留 import
- [x] 3.5 `frontend/src/shared/styles/workbench-theme.css`：删 `.workflow-workbench` 选择器族（保留 `.wb-shell`）；grep 确认全仓 `.workflow-workbench` 零消费；`StatsCard.vue` 的 `pale` 色映射若零消费一并删。验证：`npm run lint:styles` 通过。**验证结果**：pale 零消费已删；style-gates 批3 通过，唯一硬失败 `AppSidebar.style.css:209` 8px 为存量问题（tracked-clean），非本单引入
- [x] 3.6 在 `frontend/` 执行 `npm uninstall @vue-flow/core @vue-flow/background @vue-flow/controls @vue-flow/minimap`。验证：`frontend/src` grep `@vue-flow` 命中 0，package.json 无 vue-flow 依赖，package-lock.json 同步更新。**验证结果**：另清 `vite.config.js` manualChunks 的 vue-flow 分包（实施中发现的遗漏点），`npx vite build` 通过（15.12s）

## 4. 测试同步

- [x] 4.1 `tests/page_flow/unit/test_xpath_text_matches.py` 迁至 `tests/device/unit/`（内容不变，确认目标目录 `__init__.py` 存在），删除 `tests/page_flow/` 目录。验证：`python -m pytest -c tests/pytest.ini tests/device/unit/test_xpath_text_matches.py -q` 通过。**实施发现与裁定**：被测方法 `AndroidControl.get_text_matches` 已在 engines 历史重构（ff836e34 / ded6e62e）中删除，用例迁移前即失效；经需求方 2026-11-17 确认删除该失效用例（design D5 已同步），`tests/page_flow/` 整目录已删
- [x] 4.2 `tests/pytest.ini` 删 `workflow` marker；`tests/AGENTS.md` 模块表删 page_flow 行并同步 marker 说明。验证：`python -m pytest -c tests/pytest.ini --collect-only -q` 无 unknown marker（--strict-markers）。**验证结果**：793 条收集无 marker 错误；22 条收集错误全在并行重构区（AIAgent 改名等），与本单无关
- [x] 4.3 删除 `frontend/tests/workflow/` 目录（6 个 P0 spec）；`frontend/tests/README.md`、`DESIGN-module-classification.md`、`PLAN-module-classification.md` 删 workflow 行，`DESIGN-batch2-3modules.md` 删 workflow 提及。验证：`npm test` 通过（Vitest 按目录自动扫描，无残留引用）。**验证结果**：vitest 74 文件 419 过 / 2 失败，失败均在 `sidebarNavConfig.spec.ts` 的 AI任务/AI功能分组断言（并行删侧栏「测试报告/执行报告」入口未同步 spec），与本单数据分组改动无关；workflow 目录零残留
- [x] 4.4 `tests/arch/unit/test_api_path_callers.py`：删两条指向已不存在文件的页面流负向例外；docstring 的 `workflow-http-envelope` 引用改为 `api-path-convention`；`MIN_PER_SURFACE["frontend"]` 按删除后独立计数实测重登记（~95%）。验证：`pytest tests/arch/unit/test_api_path_callers.py -q` 中例外清单与扫描量用例通过（11 条无关路由失败如实记录归属，不修）。**验证结果**：实测 frontend 57 → 下限 54；例外/扫描量/动词守卫全过；put 动词随页面流消失，动词清单同步收窄并显式注释；resolve 仍余 11 条无关失败（ai/agents、ops、reports，并行改动）。**提交树复核追加**：下限按提交树实测 45 校准 42；动词守卫再收敛为 get/post/patch（提交树 delete 亦零调用点，同随页面流消失）；提交树 arch 其余失败全因并行未提交的 pricing.py 修复未入库（committed pricing 仍 import 已删的 engines.agents → URLconf 导入链断），归属并行
- [x] 4.5 `tests/arch/unit/test_channels.py`：业务前缀清单删 `"/api/workflow"`。验证：`pytest tests/arch/unit/test_channels.py -q` 通过。**验证结果**：TestHttpChannel 全过；TestAgentScopeChannel 失败因 engines/agents 整包已删（已提交历史 c5b2dc23），属存量，不修
- [x] 4.6 `tests/dashboard/unit/test_dashboard_load_budget.py` TOP_LEVEL_KEYS 删 `"workflow"`；`frontend/tests/dashboard/p0/useDashboardStats.spec.ts` 与 `p1/DashboardView.logic.spec.ts` 删 workflow fixture / 断言。验证：`pytest tests/dashboard/unit -q` 与 `npm test` 仪表盘相关用例通过。**验证结果**：四处编辑完成；前端仪表盘用例随 vitest 通过；后端套件因并行 AIAgent 改名致 5 文件收集失败（importing 旧名），待并行收口，非本单引入

## 5. 门禁与工具同步

- [x] 5.1 `utils/gen_arch_stats.py`：TABLE_PREFIX 删 `"workflow": "wf_"`。验证：`python utils/gen_arch_stats.py --check-boundaries` 通过。**验证结果**：零违规
- [x] 5.2 `utils/check_openapi_coverage.py`：EXCLUDED 删 `"/api/workflow/"`。验证：脚本可运行且不再引用该前缀
- [x] 5.3 `utils/frontend-whitelist.json`：删 5 条 workflow 体积白名单（含 2 条指向已不存在文件的条目）。验证：`python utils/gen_arch_stats.py --check-frontend` 通过。**验证结果**：workflow 条目清零；唯一超标 `ai-assistant/chat.vue` 505 行为并行新增文件，归属并行
- [x] 5.4 `openspec/openapi.yaml`：手工删 workflow 段（13 条 `/api/workflow/*` path、8 个 Workflow* schema、page_flow 枚举、workflow tag），不整份重新生成。验证：`python utils/check_gates.py --only openapi-schema,openapi-coverage` 无 workflow 相关缺口（若因并行 URLconf 改动仍红，如实记录归属）。**验证结果**：标记式切除 807 行，YAML 可解析，workflow 引用 0；HEAD 版同步切除供部分暂存（保留 HEAD 的 /api/ai/workflows/* 旧端点，属并行删除范围）；门禁仍红因并行新端点 sop-workflows / tool-catalog 未入基线，无 workflow 缺口

## 6. 规格与文档同步

- [x] 6.1 编辑 4 份主 spec 的 Purpose 去掉页面流定位：`ai-device-planner-tools`（改为 log_check 规划契约）、`ai-intent-routing`（去掉工作流类别）、`frontend-doodle-sketch-card`（消费方改为用例项目列表）、`frontend-l3-container`（去掉画布例外子句）。验证：这 4 份文件 Purpose grep「页面流 / workflow」命中 0
- [x] 6.2 `README.md` 模块地图删页面流行并同步 App / 页面计数；`dev_docs/ARCH_PRD/ARCH-平台架构设计.md` 删 workflow 两表行与 Pinia 描述；`dev_docs/ARCH_PRD/PRD-平台总需求.md` mermaid 删 WF 节点。验证：`python utils/gen_arch_stats.py --check-md --doc dev_docs/ARCH_PRD/ARCH-平台架构设计.md` 通过（若该门禁不适用则 grep 复核）。**验证结果**：grep 复核追加清掉 README/PRD/ARCH 三处 wf_ 前缀列举与 ARCH 数据模型 wf_ 行
- [x] 6.3 `backend/apps/自测与检测指令.md` 删 workflow marker 列举；`frontend/AGENTS.md` 删 `@vue-flow` 技术栈项、stores 注释改为现状（事实性描述，非红线条款）。验证：`frontend/AGENTS.md` grep `@vue-flow` 命中 0。**验证结果**：另同步 serial-log 模块 AGENTS.md 的侧栏位置描述（「页面流之后」→「设备管理之后」）
- [x] 6.4 全仓残留扫描：现役代码与主规格中 `page_flow` / `页面流` / `apps.workflow` / `modules/workflow` / `/api/workflow` / `@vue-flow` 命中 0（历史迁移、archive、project-viz 快照、本单 delta 除外）。验证：扫描命令与结果记入关单汇报。**验证结果**：frontend/src、frontend/tests、engines、utils 命中 0；backend 仅历史迁移 0038/0041/0042（设计内保留）；tests 仅历史迁移伴随测试 test_ai_planner_page_flow_guidance.py 与本单显式注释；主规格 21 份待 archive sync 归零；技能举例（doodle-craft SKILL/cards、frontend-change-plan 模板）属文档举例且 doodle-craft 正被并行迭代，本单不动，记入关单汇报

## 7. 全量验证与提交

- [x] 7.1 后端门禁：`python manage.py check` + `python manage.py makemigrations --check --dry-run` + `ruff check backend/apps backend/config` + `python -m pytest -c tests/pytest.ini -m "unit or integration"`。验证：本单范围全过（并行改动造成的失败如实记录归属，确认与本单无关）。**验证结果**：check / makemigrations 通过；本单文件 ruff check+format 全过；pytest 496 过 / 25 失败 / 22 收集错误——失败与错误全数归属并行（role_registry/thread_log 新用例、AIAgent 改名、case_manager 签名、task_list ORM 与模型、engines usage 字段、device 锁行为、serial_log 关键词目录缺失）及存量（engines/agents 删除、android_device dumpsys 参数），零页面流相关
- [x] 7.2 前端门禁：`npm test` + `npm run typecheck` + `npm run lint` + `npx vite build` + `npm run lint:styles`。验证：全部通过。**验证结果**：typecheck ✓、eslint 0 errors ✓、vite build ✓（清 manualChunks 后）；vitest 419 过 / 2 失败（并行侧栏分组断言）；lint:styles 唯一硬失败 AppSidebar.style.css 存量；prettier 门禁范围失败 9+4 文件全为并行（sidebarNavConfig 的 AI 分组单元素数组格式债属并行区域，本单数据分组编辑合规；vite.config.js 引号风格 HEAD 即不合规且不在 CI src/ 范围）
- [x] 7.3 本地门禁：`python run.py check`。验证：结果如实记录——本单范围项通过，并行改动造成的失败列明归属，不掩盖。**验证结果**：14/25 通过；11 失败全数归属并行/存量：ruff-format 13 并行文件、ruff-lint 11 并行文件、pytest-collect 22 并行错误、openapi-schema 并行告警、openapi-coverage 并行新端点、vitest 2 并行断言、prettier 9 并行文件、ruff-engines-format 并行 engines、prettier-ts 4（3 并行+sidebar 并行区域）、vue-file-size chat.vue 并行、engines-agents-retirement 并行新测试 import engines.agents；本单相关门禁（boundary/vite-build/vue-tsc/eslint/dashed-whitelist/cred-*/silent-except/business-asset/mock-data）全绿
- [x] 7.4 人工验收（平台运行时）：侧栏「数据」分组为 设备管理 / 串口日志；仪表盘无「工作流」卡且 stats 响应无 workflow 键；`/workflow` 进 404 页、`/api/workflow/prototypes/` 返回 404。验证：截图或响应记录；平台未运行则记录跳过原因。**验证结果**：平台 ONLINE；进程级 resolve('/api/workflow/prototypes/') → Resolver404 ✓；live vite :5173 侧栏模块无 workflow/页面流 ✓；stats 运行时调用在并行 ai_usage.py:151 崩溃（Task.agent 字段已删 FieldError，并行归属），契约变更经源码（views.py 无 workflow 键）+ DTO + typecheck 验证；后端 live 进程仍跑旧代码，未重启（避免影响并行会话），live 404 待平台下次重启生效
- [x] 7.5 逐文件暂存（对照 design D9 范围清单，`git status` 核对不混入并行改动，禁 `-A`），提交 `refactor(workflow): 退役页面流模块，同步删除前后端代码与规格引用`，push Kahoku。验证：`git show --stat` 仅含本单范围文件；推送后查看 CI 6 job 并如实汇报（全绿待并行改动收口）。**验证结果**：首提交 df45dd86（114 文件 +892/−9466，b63f9caf 基线 + 仅页面流删除，7 重叠文件经 swap/干净工作树暂存核验无误）；唯一缺陷为下限按脏树 57 登记（提交树实测 45）→ 校准 42。修正提交 4a7dd356 误把祖先 7de51919 当并行 HEAD 回退了 7 文件，经 ancestry 核验后以恢复提交还原 df45dd86 内容并保留下限校准；工作树并行未提交内容全程原样保留
