# Tasks: align-backend-docs-with-code

## 1. A 组：平台级文档（先合并，解锁变更②7.1）

- [x] 1.0 文件上移（需求方 2026-11-23 追加）：`backend/apps/AGENTS.md` → `backend/AGENTS.md`，约束面扩到整个 `backend/`（不新增依赖边界条款）。同步 13 文件 14 处引用（8 个 app AGENTS 层级行 + report_generator 的 `../AGENTS.md` + `自测与检测指令.md` ×3 + `README.md` + `tests/arch/unit/test_view_write_convergence.py` docstring）。原文件留跳转桩（工作区 ACL 禁止删除，待清理）。验证：全仓 `backend/apps/AGENTS.md` 仅命中本变更记录与历史归档（历史归档按惯例不改）
- [x] 1.1 `backend/AGENTS.md`（已上移）：WS 段改「当前 0 生产点，新增先走 OpenSpec」；身份段公开路径改「以 _is_public() + 三条显式旁路为准」并列举。验证：与 gateway/routing.py、middleware.py 逐条对照一致
- [x] 1.2 ARCH-平台架构设计.md、PRD-平台总需求.md 的 WS/语音段落同步（只改相关段，逐段 diff）：ARCH §3.3 改写为「0 生产路由」、架构图 websocket 分支、模块表 knowledge-assistant 行、实时性行；PRD 实时性行；另清 ARCH 两处「语音」能力句与 `engines/**/AGENTS.md` 死指针。验证：grep 两文档 `/ws/knowledge-assistant` 命中 **0**
- [x] 1.3 `.agents/docs/frontend/ai_assistant/ai_assistant_style_and_redlines.md`（原 `frontend/src/modules/ai-assistant/AGENTS.md`，已外置）删失实红线「agents.ts 与 TASK_KIND_* 仍被 task-list 引用」，改为「在任务清单侧已无引用、死函数已随退役清扫删除」。验证：`task-list` 零 `ai-assistant` import、前端 `TASK_KIND_` 命中 **0**（均已实测）；**本项合并后方可执行变更②7.1**
- [x] 1.4 `tests/` 收尾（迁移表部分**已移交** `fix-module-doc-drift` 的 A2/A3/A4，本项不再重复改）：只做 `.agents/docs/apps/self_test_and_checks.md` 的业务 marker 删 `test_runner`。验证：该文件 grep `test_runner` 命中 **0**

## 2. A 组：app 级 AGENTS 与 docstring

- [x] 2.1 task_list 模块文档（内容已迁至 `.agents/docs/apps/task_list/task_list_task_lifecycle.md`，更正见 6.5）：删已下线的 report 端点宣称；执行链改 `task_runner → engine_adapter → engines.backend_bridge`；计费改 `task_cost` + `usage_ledger`；依赖方向改 `AssistantRelease` 与 `ai_assistant.api`。验证：`urls.py` 无 `report` 路由、`api.py:13` 导 `task_cost`、`views.py:52` 只读 `AssistantRelease`
- [x] 2.2 模块文档（已迁至 `.agents/docs/apps/ai_assistant/` 与 `usage_ledger/`，更正见 6.5）：ai_assistant 写库表述改「入口只经 api.py，实现层在 services/」；usage_ledger 计价路径改 rates.py 优先 / pricing.json 兜底、厂商改三类、文件表补 rates.py。验证：与 `services/*.py` 的 ORM 写点、`rates.py`、`pricing.py:19,50` 对照一致
- [x] 2.3 **收尾已完成**：① 代码侧 `ops_console/views.py` 端点清单 docstring 补齐 5 条（model-grants / grant-author / revoke-author / grant-operator / revoke-operator，共 11 条）、`ops_console/api.py` `__all__` 补 `set_model_use` / `set_assistant_author`；② 文档侧 `.agents/docs/apps/bug_manager/bug_manager_bug_ticket_ledger.md` 依赖方向补 `TaskEvent` 只读（`extract.py:324-327` 读 `StepInterruptedEvent`）。验证：`pytest tests/ops_console tests/bug_ticket -q` → **85 passed**；`ruff check` + `ruff format --check` 通过
- [x] 2.4 `accounts/apps.py` docstring 改「本应用自有表只有 `acc_token_revocations`（`models.TokenRevocation`，登出吊销记录，落库不依赖 Redis）」；`apps/__init__.py` docstring 改为 12 个业务 app 清单 + 指向 `.agents/docs/apps/` 索引。验证：与 `settings.INSTALLED_APPS` 的 12 条本地模块逐条对照一致；`ruff check` + `ruff format --check` 通过
- [x] 2.5 新建 `.agents/docs/apps/knowledge_search/knowledge_search_retrieval.md`（四张表 / 七个端点 / 评测批次状态机 / 检索实现 / **View 编排待偿债权 R-4 如实登记**），并从索引「暂无模块文档的目录」中移除 knowledge_search 行、加入「模块 → 文档」表。验证：索引 12 行逐条可解析；无文档目录收敛为 case_manager / dashboard / device_pool 三个
- [ ] 2.6 A 组关单：`python run.py check` 退出码 0（含 __all__ 改动）；**提交范围必须含 `.agents/docs/**`（48 个新文件）与 `.gitignore` 的 `/docs/` 锚定**——漏了它们，主干上的索引链接全是死链；逐文件暂存 docs(backend) 提交，推特性分支提 PR，CI 两 job 全绿后合并。验证：`git show --stat` 含 `.agents/docs/` 与 `.gitignore`；干净 clone 上索引链接可解析。
  **2026-11-23 实测（未通过，非本变更引入）**：`run.py check` 19/28，9 项阻塞失败——`ruff-format` / `ruff-lint` / `openapi-schema` / `openapi-coverage` / `vitest` / `vite-build` / `prettier` / `ruff-engines-format` / `vue-tsc`，均落在并行在途改动（如 `engines/ae_harness/knowledge/models.py` 格式、`frontend/tests/**`）上；本变更触及的 5 个 py 文件 `ruff check` + `ruff format --check` 全绿。待那些变更落地后重跑本项

## 3. B 组：device_pool AGENTS（待变更④合并后）

- [x] 3.1 新建 `.agents/docs/apps/device_pool/device_pool_write_boundaries.md`（按外置范式，不建 `device_pool/AGENTS.md`）：10 个端点、current 指针语义、`GET /current/` 的 ADB 探测 + 10s 缓存副作用、`dp_device_locks` 锁模型（含 `lock_type` 实际有 `user|process|observe` 三种）、observe 链与 `OBSERVE_LOCK_TTL=1800`、写库**现状 vs 目标**双栏。索引加入该模块、从「暂无模块文档」移除，无文档目录收敛为 case_manager / dashboard。
  **偏差登记**：前置 `converge-device-pool-writes-to-api` **尚未合并**，故按当前代码实况写——现状写库在 `manager.py`（20 处 ORM 写），`api.py` 仅 7 个函数；文档内已标注「目标态待该变更合并后重写本节」，合并后须回改，勿两份并存

## 4. 规格收口

- [ ] 4.1 knowledge-assistant-voice REMOVED delta 随本变更 archive 正常收口。验证：`openspec validate "align-backend-docs-with-code"` 通过；archive 后 openspec/specs/knowledge-assistant-voice 不再存在

## 5. 模块文档外置（2026-11-23 需求方追加，已执行）

- [x] 5.1 新建 `.agents/docs/apps/{accounts,ai_assistant,bug_manager,ops_console,report_generator,serial_log,task_list,usage_ledger}/`，写入 11 篇 `{app}_{feature}.md`（accounts 3 篇、serial_log 2 篇、其余各 1 篇）。验证：索引表 11 行逐条可解析到真实文件
- [x] 5.2 `backend/apps/自测与检测指令.md` → `.agents/docs/apps/self_test_and_checks.md`（改名 + 首部标注迁移来源）
- [x] 5.3 `backend/apps/AGENTS.md` 改写为**纯索引**：模块→文档表 + 「暂无模块文档的目录」登记 + 阅读顺序
- [x] 5.4 删除 11 个 app 级 `AGENTS.md`（8 有内容 + 3 个 0 字节）与 `backend/apps/自测与检测指令.md`；`backend/AGENTS.md` 的层级行、关单尾注改指索引与新路径
- [x] 5.5 迁移时落实 2.1/2.2/2.3 的文档侧更正：task_list（backend_bridge / task_cost / AssistantRelease / 无 report 端点）、usage_ledger（rates.py + 三类厂商）、bug_manager（三类问题）、ops_console（补 model-grants / grant-author / revoke-author 共 11 端点）、ai_assistant（写库入口在 api.py、实现在 services/）。**代码侧**（`ops_console/views.py` 端点清单 docstring、`ops_console/api.py` 的 `__all__`）未做，仍归 2.3

## 6. 三棵树同步外置（2026-11-23 需求方追加，已执行）

- [x] 6.1 `frontend/`：15 篇外置文档（`.agents/docs/frontend/**`），`frontend/AGENTS.md` 改为索引，删 6 个有内容 + 4 个 0 字节子 AGENTS.md。验证：索引 24 条相对链接 0 失效
- [x] 6.2 `tests/`：4 篇外置文档（`.agents/docs/tests/**`），`tests/AGENTS.md` 改为索引。验证：链接 0 失效
- [x] 6.3 `engines/`：12 篇外置文档（`.agents/docs/engines/**`），`engines/AGENTS.md` 保留为**索引**（`engines-agents-style-check` 的 `_find_repo_root` 依赖该文件存在），删 12 个子 AGENTS.md。验证：`python -m scripts.check_engines_agents_style`（cwd 技能目录）→ `scanned 91 files; 0 violation(s)`，exit 0
- [x] 6.4 **`.gitignore:114` 的 `docs/` 改为 `/docs/`**：原规则本意是根目录的 Claude 会话目录，未锚定导致 `.agents/docs/**` 全被忽略，索引链接在干净 clone 上成死链。影响面：仓库内仅 `.agents/docs` 一个 `docs` 目录，锚定后无副作用；回退＝改回 `docs/`
- [x] 6.5 清掉本次改造引入的悬空引用：`README.md` 引擎行、`dev_docs/ARCH_PRD/GUIDE-创建Agent清单.md` 必读行、`openspec/specs/agent-harness/spec.md`、`openspec/changes/platform-config-for-knowledge/{proposal,design}.md`、`engines/ae_harness/middleware/observer.py:146` docstring、`engines/AGENTS.md` 顶部重复层级块

## 7. 合并后必做（不阻塞本变更关单）

- [ ] 7.1 本变更合并进主干并 archive **之后**，执行 `openspec/changes/fix-module-doc-drift`：外置文档里 14 处与代码不符的说法（tests 7 条、engines 7 条）逐条对着代码更正。需求方 2026-11-23 指定该顺序——两单改同一批 `.agents/docs/**`，前置未合并时改文本会制造冲突。其中 B7（红线「对应子 AGENTS」指代）须另提变更申请获批。
- [ ] 7.2 `converge-device-pool-writes-to-api` 合并后，回改 `.agents/docs/apps/device_pool/device_pool_write_boundaries.md` 的「写库边界」节：删掉「现状」栏与偏差登记，改为「写库层=api.py，manager/registry/state_machine 为内部实现」。验证：与合并后 `views.py` / `api.py` 的写点逐条对照一致；文档内不再出现「尚未收敛」字样