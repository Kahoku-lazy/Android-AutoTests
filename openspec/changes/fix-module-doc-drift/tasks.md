# Tasks: fix-module-doc-drift

> 每条任务格式：**位置 → 复核 → 改法 → 完成判据**。复核结果与 proposal 里的审计结论不一致时，**以复核为准**并在 `design.md` 记录差异。

## 0. 前置

- [ ] 0.1 **硬门控（需求方 2026-11-23 指定：合并后再跑）**：`align-backend-docs-with-code` 已合并进主干且已归档。
  验证：`git log --oneline --grep align-backend-docs-with-code` 有合并提交；`openspec list` 中该变更不再列为进行中。
  **未满足则本变更一行不写**——两单改同一批 `.agents/docs/**`，前置未合并时改文本只会制造冲突。
- [ ] 0.2 目标文件存在性：`.agents/docs/tests/**` 与 `.agents/docs/engines/**` 下的目标文件 `Test-Path` 逐条为真（前置合并后路径才稳定）

## 1. A 组 · tests 文档（7 条）

- [ ] 1.1 **A1** `tests_integration_and_api.md`「接口测试脚本与模块映射」表
  - 复核：`Test-Path tests/device/api/test_inspector.py tests/api/case/inspector.yaml`；`Get-ChildItem tests/device/api`
  - 改法：两个文件都无 → 确认设备检查器是否已退役（查 `openspec/specs/**` 与 `backend/apps/device_pool`）；已退役则**删整行**并在表下注明退役去向，未退役则补真实落位
  - 完成判据：表中每行脚本/YAML 路径 `Test-Path` 为真，或显式标注「已退役」
- [ ] 1.2 **A2** `tests_directory_conventions.md` 迁移状态表 `engines/agents/{unit,e2e}` 行
  - 复核：`Get-ChildItem tests/engines -Directory -Recurse -Depth 2`
  - 改法：按实际目录重写（当前应为 `engines/ae_harness/unit`、`engines/backend_bridge/unit`、`engines/device/unit`，无 e2e）
  - 完成判据：表中 `engines/*` 行与实测目录一一对应
- [ ] 1.3 **A3** 同表 `knowledge/{unit,integration}`
  - 复核：`Get-ChildItem tests -Directory` 找 `knowledge*`
  - 改法：目录名改为实际（当前为 `knowledge_search`），正文「大模块」列表同步
  - 完成判据：全文 grep `knowledge/config` 之外无 `tests/knowledge/` 口径
- [ ] 1.4 **A4** 同表 `models/{unit,integration}`
  - 复核：`Test-Path tests/models/integration`
  - 改法：不存在则删 integration
  - 完成判据：表中每个 `{unit,integration}` 组合都真实存在
- [ ] 1.5 **A5** `tests_unit_and_contract_parity.md`「之所以放在 Python 侧」理由句
  - 复核：`Select-String frontend/package.json -Pattern '"test'`；`(Get-ChildItem frontend/tests -Recurse -Filter *.spec.ts).Count`
  - 改法：改为「前端有独立 runner（vitest + `frontend/tests/**/*.spec.ts`），但 `frontend/src` 下无 spec；『路径能否被后端解析』只有后端能答」，保留原结论
  - 完成判据：理由句不再声称「前端没有测试运行器」
- [ ] 1.6 **A6** 同篇第 4 条举例 `frontend/src/modules/ai-assistant/api/toolbox.ts`
  - 复核：`Get-ChildItem frontend/src/modules/ai-assistant/api`
  - 改法：找现行等价调用点换例子（注意「调用与字面量分处两行」的示范价值）；无等价点则删例子
  - 完成判据：举例文件 `Test-Path` 为真
- [ ] 1.7 **A7** `tests_directory_conventions.md` 的 `reports/` 口径 + `tests/AGENTS.md` 索引同一条规范
  - 复核：`Test-Path reports`、`Test-Path tests/reports`
  - 改法：统一为 `tests/reports/`（两处同步），若根 `reports/` 确由运行产生则写成「根 `reports/`（运行时产物，未入库）」
  - 完成判据：两处口径一致，且与 `.gitignore` 实际一致

## 2. B 组 · engines 文档（7 条）

- [ ] 2.1 **B1** `engines/AGENTS.md` 职责段「`engines/agents/` 正在退役」
  - 复核：`Test-Path engines/agents`；`Test-Path openspec/changes/archive/2026-11-17-retire-engines-agents`
  - 改法：改为「已于 2026-11-17 退役（`openspec/changes/archive/2026-11-17-retire-engines-agents`），目录不得重建」，与红线「禁止恢复」对齐
  - 完成判据：文中不再出现「正在退役」与未归档的 change 路径
- [ ] 2.2 **B2** `backend_bridge_role_assembly.md` 目录现状 + 红线 9 的 `events/`
  - 复核：`Get-ChildItem engines/backend_bridge`（含子目录）
  - 改法：按实际重写目录清单（当前应含 `event_log.py`、`workflow/cancel.py`、`models/`），删除 `events/`
  - 完成判据：清单里每项 `Test-Path` 为真
- [ ] 2.3 **B3** `ae_harness_middleware_admission.md` 硬性边界 5「配置只经 `agents/config.py`」
  - 复核：`Test-Path engines/ae_harness/agents/config.py`；grep 现行配置载体
  - 改法：指向现行载体；确无配置入口则写「本层无配置入口，参数由调用方传入」
  - 完成判据：指向的路径 `Test-Path` 为真，或明说无入口
- [ ] 2.4 **B4** `ae_harness_overview.md` 的 `AgenScope`
  - 复核：grep `AgenScope` 全仓
  - 改法：`AgenScope` → `AgentScope`（只改这一个词，版本号等不动）
  - 完成判据：仓库活文档中 `AgenScope` 命中 0
- [ ] 2.5 **B5** `uart_log_serial_capture.md` 相关路径 `engines/agents/tools/tool_serial.py`
  - 复核：`Test-Path engines/agents/tools/tool_serial.py`；grep 现行串口工具封装
  - 改法：删除该行或改指现行封装
  - 完成判据：该行指向的路径 `Test-Path` 为真，或该行已删除
- [ ] 2.6 **B6** `ae_harness_knowledge_kb_retrieval.md` 引用 `openspec/changes/add-knowledge-auto-eval`
  - 复核：`Test-Path openspec/changes/archive/2026-11-18-add-knowledge-auto-eval`
  - 改法：补 `archive/` 路径前缀
  - 完成判据：引用的 change 路径 `Test-Path` 为真
- [ ] 2.7 **B7** `engines/AGENTS.md` 红线「须先在对应子 AGENTS 立项」→「对应模块文档（`.agents/docs/engines/**`）」
  - **前置**：本条改红线措辞，按根 `AGENTS.md` 第 4 条须先提交变更申请并获批
  - 复核：grep `对应子 AGENTS` 全仓
  - 改法：获批后改；未获批则本任务标记 `skipped（未获批）`，docs 里保留原文
  - 完成判据：命中 0（已改）或任务显式标 skipped（未批）

## 3. C 组 · 既有旧路径（`engines/agents` 退役遗留）

- [ ] 3.1 **C1** `.agents/rules/engines-code-style.md` 第 6/17/85/110/122 行
  - 复核：`Test-Path engines/agents`；`Select-String .agents/rules/engines-code-style.md -Pattern "engines/agents/AGENTS"`
  - 改法：改为 `.agents/docs/engines/**` 对应篇；纯过时指路句可删
  - 完成判据：该文件 grep `engines/agents/AGENTS.md` 命中 0
- [ ] 3.2 **C2** `dev_docs/ARCH_PRD/ARCH-平台架构设计.md:168-170` 的 `engines/agents*` 三行
  - 复核：`Get-ChildItem engines`（确认现行分层）
  - 改法：按现行引擎分层重写表格，或把这三种标注为「2026-11-17 退役」
  - 完成判据：该文档 grep `engines/agents/` 的命中处均带退役标注，或已改指现行目录
- [ ] 3.3 **C3** `tests/arch/unit/test_channels.py:76` docstring 的 `engines/agents/rag/AGENTS.md`
  - 复核：`Get-Content tests/arch/unit/test_channels.py -TotalCount 80`
  - 改法：改指 `.agents/docs/engines/ae_harness_knowledge/ae_harness_knowledge_kb_retrieval.md`，或删除该引用
  - 完成判据：`python -m pytest -c tests/pytest.ini tests/arch/unit/test_channels.py -q` 通过，且 docstring 不再指已删文件

## 4. 收口

- [ ] 4.1 重跑全部 17 条复核命令，把「命令 → 实际输出」贴进 PR 说明
- [ ] 4.2 索引链接复检：`.\.venv\Scripts\python.exe temps\check_agents_index_links.py`（9 个索引、0 失效）
- [ ] 4.3 `npx openspec validate fix-module-doc-drift` 通过
- [ ] 4.4 关单：`python -m pytest -c tests/pytest.ini tests/arch/unit -q`（纯文档改动，确认未误伤）+ `git diff --stat` 仅含预期文件
