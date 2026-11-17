## Context

动机见 proposal.md - Why。方案需要的当前状态与约束：

- **消费面实测**：全仓对页面流的业务消费点只有 `backend/apps/dashboard/views.py` 的 `WorkflowDocument` 计数（stats `workflow.total`）与前端仪表盘 KPI 卡；AI 工具（`list_page_flows` / `get_page_flow` / `save_page_flow` / `create_page_flow`）已在此前退役变更中删除，`engines/` 对页面流零代码引用（grep 实证）。
- **数据实测**：`manage.py shell` 计数 `wf_prototypes` / `wf_directories` / `wf_documents` 均为 **0 行**。
- **工作树现状**：存在大量未提交的并行改动（SOP 工作流功能、ai_assistant 重构、ops 后台）。`tests/arch/unit/test_api_path_callers.py` 实测 **2 failed**：① 例外清单指向已不存在的 `test_workflow_single_path.py`（页面流遗留，本单修复）；② 11 条路由解析失败（agent-reports / ai/agents / ops / reports，并行改动造成，本单不修）。`openspec/openapi.yaml` 亦带并行未提交差异。
- **同名陷阱**：`engines/ae_harness/workflow/`、`engines/backend_bridge/workflow/`、ai_assistant 的 `AISopWorkflow` / `sop-workflows` 是 SOP 编排，与页面流无关，禁止误删。
- **提交纪律**：单主干 Kahoku、Conventional Commits、逐文件暂存（禁 `git add -A`）、CI 6 job 全绿是质量闸门。

## Goals / Non-Goals

**Goals:**

- 页面流代码、接线、测试、门禁登记、规格引用全部归零；删除后全仓 grep `page_flow` / `页面流` / `modules/workflow` / `apps.workflow` 在**现役代码与主规格**中零命中（历史迁移与 archive 除外）。
- 本单范围内的门禁断言恢复可过（arch 例外清单、扫描下限、表前缀、openapi workflow 段、体积白名单）。
- 不留死选择器（`.workflow-workbench`）、死依赖（`@vue-flow/*`）、死契约字段（stats `workflow`）。

**Non-Goals（设计级边界）:**

- 不修 arch 门禁中 11 条与页面流无关的路由失败（并行改动造成）。
- 不整份重新生成 openapi 基线（避免混入并行 schema 差异）。
- 不触碰并行变更文件、历史迁移、archive。
- 不整份退役遗留 AI 规格（另立单）。
- 不重新生成 project-viz 看板快照。

## Decisions

**D1 删表顺序：先迁移后删目录。** 在 `backend/apps/workflow/` 仍存在时新增 `0007_drop_tables.py`（`RunSQL` `DROP TABLE IF EXISTS wf_documents / wf_directories / wf_prototypes`，注意 FK 顺序：先 documents 再 directories 再 prototypes），跑 `python manage.py migrate workflow` 确认三表消失，**然后**删 App 目录、INSTALLED_APPS、路由、TAGS。理由：Django 需要 App 在册才能加载并应用其迁移；retire-inspector-and-element-locator 已验证该模式。备选「直接删目录留孤儿表」——否：库里留死表、`django_migrations` 记录悬空。reverse 为 no-op 并注明数据不可恢复（0 行，无实际损失）。

**D2 仪表盘契约：整键删除，前后端同批。** 删 `_workflow_stats()` 与 stats 的 `workflow` 键、前端 KPI 卡、`DashboardStats` / `ZeroStats` 的 `workflow` 字段、`useDashboardStats` 映射，三个测试文件同步。理由：需求方已确认 BREAKING；保留恒 0 死字段违背「同步删除所有代码」。备选「保留字段恒 0」——否：死契约。同一提交落地，`test_dashboard_load_budget` 的 TOP_LEVEL_KEYS 同步删键守住形状。

**D3 openapi 基线：手工删 workflow 段。** 删除 13 条 `/api/workflow/*` path、8 个 Workflow* schema、`DocTypeEnum`（page_flow 枚举，若仅 workflow 引用）、workflow tag 与 settings TAGS 项。不跑 `spectacular` 整份再生成。理由：工作树基线带并行未提交差异，整份再生成会把并行 schema 混入本单提交，违反「只提交本变更文件」。验证：`check_gates.py --only openapi-schema,openapi-coverage`；若 coverage 因并行 URLconf 改动仍红，如实记录归属，不修。

**D4 共享资产保留，只清死代码。** `--c-workflow` 令牌（tokens.css）、AppCard `COLOR_TONE`、sketchCard cycle 色板、motion.css、DoodleNote、WorkbenchHeader 默认渐变、git-branch 图标注册均有模块外消费点（grep 实证 10+ 处），**保留**。仅删 `shared/styles/workbench-theme.css` 的 `.workflow-workbench` 选择器族（模块删除后零消费）与 `modules/workflow/tokens.css`（随模块）。`StatsCard.vue` 的 `pale` 色映射在仪表盘 KPI 卡删除后若零消费则一并清理（实施时 grep 确认）。

**D5 误放测试：原拟迁移，实施后裁定删除。** `tests/page_flow/unit/test_xpath_text_matches.py` 被测对象是 `engines.device.android.AndroidControl`，原计划迁至 `tests/device/unit/` 保留。实施中发现被测方法 `get_text_matches` 已在 engines 历史重构（ff836e34 / ded6e62e，均已提交）中删除，用例迁移前即失效（AttributeError）。经需求方 2026-11-17 确认：删除该失效用例，不在 device/unit 留红用例；`tests/page_flow/` 整目录删除。

**D6 arch 契约测试同步。** `test_api_path_callers.py`：删两条指向已不存在文件的页面流负向例外（修复当前红因①）；docstring 的 `workflow-http-envelope` 引用改为 `api-path-convention`；`MIN_PER_SURFACE["frontend"]` 按实施后实测重登记（删 `workflow/api.ts` 17 个调用点后实测约 44，下限取 ~95%）。`test_channels.py`：业务前缀清单删 `/api/workflow`。11 条无关失败不修、不掩盖。

**D7 规格 delta 与 Purpose 分工。** 21 份 delta（6 退役 + 15 修改）已随本单产出；MODIFIED 携带完整更新块。校验器禁止 MODIFIED 静默丢弃既有场景名，因此随模块消失的场景一律**保留原场景名、改写为退役守护断言**（零残留检索 / 不再归入退役类别），并按本仓先例加「场景名沿自变更前」注释（如 `识别工作流意图` / `Canvas destructive actions` / `原型列表查询数恒定`）；仍有效的契约换用现役承载页举例（用例管理新建项目弹层、在线设备 entry 卡）。4 份主规格的 Purpose 仍指向页面流（`ai-device-planner-tools` / `ai-intent-routing` / `frontend-doodle-sketch-card` / `frontend-l3-container`），按 schema 指令在 **apply 阶段直接编辑主 spec 的 Purpose**（delta 不承载 Purpose）；退役的 6 份主 spec 在 archive  sync 后按 OpenSpec 口径删除文件。

**D8 依赖卸载。** `npm uninstall @vue-flow/core @vue-flow/background @vue-flow/controls @vue-flow/minimap`（frontend 目录），lockfile 随命令更新；卸载前 grep 确认 `@vue-flow` 在 `src/` 零残留。

**D9 提交策略。** 单个 Conventional Commit：`refactor(workflow): 退役页面流模块，同步删除前后端代码与规格引用`（沿用 retire 系列先例的 refactor 类型）。逐文件暂存本单范围清单内的文件；暂存前 `git status` 核对不混入并行改动。推送后 CI 全绿受并行改动阻塞——如实汇报，不强行修无关失败。

## 模块防火墙自检

- **跨 App import**：本单只删除既有 import（dashboard → workflow.models），不新增任何跨 App 依赖；删除后 dashboard 对 workflow 零依赖。
- **禁止跨 App service/runner/consumer/state_machine import**：无新增，不触碰。
- **写库收敛 api.py**：删表迁移是 `RunSQL` DDL（退役先例同口径），非业务 DML；本单不新增任何业务写路径。
- **前端不直连数据库；仪表盘不做写操作**：仪表盘仅删只读统计键与 KPI 卡，保持只读。
- **依赖方向**：`engines/` 对页面流零引用，无依赖方向变化；不触碰 AGENTS.md 红线 / 禁止事项 / 准入清单 / 依赖边界条款——仅同步事实性描述（frontend 技术栈 `@vue-flow` 项、stores 注释、tests 模块表），已经需求方确认。
- **钱与配额口径**：不涉及。

## Risks / Trade-offs

- [门禁因并行改动仍红，CI 无法全绿] → 如实记录失败归属（本单修页面流相关项，11 条无关失败留待并行收口）；需求方已知情确认并行推进。
- [openapi coverage 因并行 URLconf 改动红] → 手工删 workflow 段保证本单不新增缺口；并行差异如实记录，不整份再生成。
- [仪表盘前后端不同步窗口] → 同一提交落地；`test_dashboard_load_budget` + 前端 `useDashboardStats.spec` 双侧守形状。
- [共享令牌误删牵连其它模块] → 删除前 grep `--c-workflow` / `workflow-workbench` / `@vue-flow` 消费清单；只删零消费的死选择器与模块私有文件。
- [迁移顺序错误留孤儿表] → 严格 D1 顺序；`showmigrations workflow` 全绿 + 库内查三表不存在后再删目录。
- [扫描下限拍脑袋致假失败] → `MIN_PER_SURFACE` 以实施后独立计数实测重登记（~95%），不直接调低了事。
- [回滚] → `git revert` 该提交即可恢复全部代码与规格；三表可经历史迁移 0001–0006 重建（0 行，无数据损失）；RunSQL reverse 为 no-op 已在迁移注明。

## Migration Plan

1. **删表**：App 在册时加 `0007_drop_tables.py` → `python manage.py migrate workflow` → 验证三表消失（`showmigrations` + 库内查表）。
2. **后端拆除**：删 `backend/apps/workflow/` 目录；注销 INSTALLED_APPS / urls / Swagger TAGS；dashboard 删 `_workflow_stats` 与 `workflow` 键。
3. **前端拆除**：删 `frontend/src/modules/workflow/`；拆 router / main.ts / sidebarNavConfig 接线；删仪表盘 KPI 卡与 DTO / 映射字段；清 workbench-theme 死选择器；`npm uninstall` 四个 VueFlow 包。
4. **测试与门禁同步**：迁移误放测试；删 `tests/page_flow/` 与 `frontend/tests/workflow/`；pytest.ini marker；arch 两测试；仪表盘 3 测试；gen_arch_stats / check_openapi_coverage / frontend-whitelist / openapi 基线。
5. **规格与文档同步**：21 份 delta 已在单内；apply 时编辑 4 份主 spec Purpose；README / ARCH / PRD / 自测指令 / frontend/tests 规划文档 / AGENTS.md 事实性描述。
6. **验证**：`manage.py check` + `makemigrations --check --dry-run` + ruff（相关路径）+ `pytest -c tests/pytest.ini -m "unit or integration"` + 前端 `npm test` / `typecheck` / `lint` / `vite build` + `python run.py check`（并行失败如实记录归属）。
7. **提交**：逐文件暂存 → `refactor(workflow): ...` → push Kahoku → 确认 CI（全绿待并行收口）。

回滚：`git revert` + 历史迁移重建三表（0 行）。

## Open Questions

无——删除范围、误放测试归属、遗留规格处理、并行推进、看板快照五项决策均已由需求方确认。
