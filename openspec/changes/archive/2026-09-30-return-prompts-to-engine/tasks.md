# 变更：提示词收回引擎（前端不再展示）

## 1. 提示词归位（引擎唯一真相源）

- [x] 1.1 `engines/ai/agents/config.py` 写入三份提示词正文（取自收回当时库中运行版本，逐字保留）；验证：与 `temps/_db_prompts.json` 逐字相等，长度 planner 1337 / executor 2038 / verifier 2071
- [x] 1.2 `engines/ai/agents/model.py`：`RoleSpec.prompt` 由留空占位改为三份常量；`AgentRole` 缺省取 `spec.prompt`；三个角色类各自带上自己的提示词。验证：装配出的三角色 `system_prompt` 分别等于对应常量（离线校验 11 项全通过）
- [x] 1.3 拆掉注入通道：`engines/ai/base.py` 删 `TaskRequest.system_prompts`；`engines/ai/agents/engine.py` 与 `apps/ai_assistant/engine_adapter.py` 同步；`build_device_models(system_prompts=...)` 入参删除。验证：`manage.py check` 无问题；`test_request_carries_no_system_prompts` 断言该字段不存在
- [x] 1.4 `apps/ai_assistant/management/commands/ui_pipeline.py` 去掉 `system_prompts=` 实参。验证：`ruff check` 通过

## 2. 后端接口面与数据面下线

- [x] 2.1 `apps/ai_assistant/models.py` 删三列与 `AIDevicePromptArchive`；`api.py` 删提示词读写与存档（154 行）；`urls.py` 删六个端点与视图导入；删 `views_prompts_drf.py`。验证：`manage.py check` 无问题、`makemigrations --check` 无变更
- [x] 2.2 新增迁移 `0051_drop_device_prompts`（删三列 + 删存档表）。验证：`makemigrations --check --dry-run` 报「No changes detected」
- [x] 2.3 收回前落存档：`dev_docs/DEV_TEST/设计方案与报告/AI设备提示词收回存档.json`（三份正文 + 存档行，含 kind/时间/操作者）。验证：文件存在、三份正文长度与实际一致
- [x] 2.4 `app/ai_assistant/model_debug.py`：删 `role_prompt`，调试装配改用角色 `spec.prompt`，调试配置不再下发 `prompt`。验证：`test_config_carries_no_prompt` 与 `test_debug_role_mounts_role_tool_subset` 断言通过

## 3. 前端不再展示

- [x] 3.1 装配台来源定义删 `prompt`；`ToolboxPanel.vue` 删面板渲染与导入。验证：`vue-tsc` 无类型错误、`eslint` 0 error
- [x] 3.2 模型调试页删「系统提示词」折叠块与相关响应式变量、导入。验证：该页不再含 `prompt` 读取；用例改为断言「不展示提示词」
- [x] 3.3 删除 `DevicePromptPanel.vue` / `DevicePromptHistoryDrawer.vue`（含样式）/ `useDevicePrompts.ts`；`constants.ts` 与 `api/toolbox.ts` 删提示词常量与六个接口函数。验证：全模块无残留引用
- [x] 3.4 `frontend/src/modules/ai-assistant/AGENTS.md` 由「六源」改「五源」并写明提示词为引擎常量、前端不展示

## 4. 规格与文档

- [x] 4.1 删除 `openspec/specs/ai-device-prompts/`（该能力整体作废）
- [x] 4.2 `ai-engine-protocol`：提示词改「随引擎走」；`ai-model-debug`：不再展示提示词、配置不下发
- [x] 4.3 `ai-device-planner-tools` / `ai-executor-output` / `ai-verifier-output`：提示词来源由「迁移改库」改为「引擎常量」
- [x] 4.4 `dev_docs/DEV_TEST/接口文档/API-AI助手.md` 删六节与总览六行、补「不下发提示词」。验证：全仓 `device-prompts` 零命中（历史归档除外）

## 5. 测试同步

- [x] 5.1 删 `tests/graybox/unit/test_device_prompts.py`、`test_ai_device_prompt_archive.py`
- [x] 5.2 新增 `test_ai_planner_page_flow_guidance.py` 承接迁移插入逻辑（锚点 / 幂等 / 可逆 / 种子）四条用例
- [x] 5.3 同步 `test_ai_model_debug.py` / `test_ai_engine_config.py` / `test_ai_task_title_attach_dispatch.py` / `test_ai_debug_log_check.py`
- [x] 5.4 前端删三个提示词用例文件并改 `useModelDebug.spec.ts` / `model-debug-log-check.spec.ts` 夹具

## 6. 关单验证

- [x] 6.1 `python manage.py check` → 无问题；`makemigrations --check --dry-run` → No changes detected
- [x] 6.2 `python -m ruff check engines/ai apps/ai_assistant tests` → All checks passed；`ruff format --check` → 全部已格式化
- [x] 6.3 `python tools/gen_arch_stats.py --check-boundaries` → 零违规
- [x] 6.4 `npx vue-tsc --noEmit` → 无类型错误；`npx eslint src/modules/ai-assistant` → 0 error；`prettier --check` 五个改动文件 → 通过
- [x] 6.5 相关后端用例：100 passed / 9 failed / 6 errors；失败的 9 项与报错的 6 项在改动前的 HEAD 上**同样失败**（沙箱无权读 site-packages/distro 造成的环境问题，非本次改动引入），与本改动相关的断言全部通过
- [x] 6.6 本地库迁移：`python manage.py migrate ai_assistant`（删三列 + 删存档表）。**实测已于本地库应用**：`showmigrations ai_assistant` 0051 为 `[X]`；探针查库确认 `ai_agents` 无 `prompt*` 列（共 28 列）、无 `ai_device_prompt%` 表；库为本机 MySQL `android_autotests`（127.0.0.1:3306）。存档件 `dev_docs/DEV_TEST/设计方案与报告/AI设备提示词收回存档.json` 在（20,674 字节，含 planner 1337 / executor 2038 / verifier 2071 字与一条存档记录）。**本机无需再执行**；本机之外的库（测试 / 生产）部署时按同一迁移各跑一次

## 7. 顺带记录：引擎目录改名

- [x] 7.1 `engines/ai/agentscope/` → `engines/ai/agents/`（git 记为改名）：注册表路径、apps 与 tests 全部引用、架构守卫同步
- [x] 7.2 架构测试补断言：旧目录名不得再出现。验证：`pytest tests/arch/test_channels.py` 6 项通过
- [x] 7.3 引擎注册名 `agentscope` 与 `settings.AI_ENGINE` 保持不变（不改部署面）

## 8. 追补：调试页现场清理与规格去重（同批收口）

- [x] 8.1 本单 delta `specs/ai-model-debug/spec.md` 去重「单角色调试对话」：整条 REMOVED（Reason 写明三处条款已被「调试对话按该角色真实装配运行」「需要设备的角色须先选定设备并获得一次性授权」「调试对话不设前端等待上限」取代且与实现相反；Migration 写明改看哪三条），并 ADDED 新条「单角色调试对话的输入与留痕约束」承接仍有效的约束（引擎侧系统提示词 / 不落库 / 回复展示与可读错误）。口径：`openspec validate` 拒绝 MODIFIED 丢场景，故不能只删场景「对话不触碰真机」。验证：`openspec validate 2026-09-30-return-prompts-to-engine --strict` 通过（已跑，输出 is valid）
- [x] 8.2 同 delta 的「调试页按三层组织并分组展示」：③ 参考数据写实为「设备（该角色是否需要设备、需要时为可用设备候选）+ Skill 目录路径」，补「参考数据区展示设备与 Skill 目录」场景且该区不得为空。验证：`openspec validate --strict` 通过（已跑，输出 is valid）
- [x] 8.3 `frontend/src/modules/ai-assistant/api/toolbox.ts`：删 `ModelDebugRoleConfig.prompt` 死字段（后端已不下发、全模块零读取）。验证：`npx vue-tsc --noEmit` 无输出（无类型错误）
- [x] 8.4 `frontend/src/modules/ai-assistant/ModelDebugPage.vue`：删「调试对话不挂载这些工具……不触碰真机」文案，改为如实描述（挂该角色真实工具、会真实操作所选设备），文案入 `constants.ts` 唯一真相源（`MODEL_DEBUG_ASSEMBLY_NOTE`；顺带把设备空态与 Skill 空态两句硬编码文案也收进常量）；并删掉对话空态里那条「只输出你收到的系统提示词的第一行」示例——它会让模型把提示词原文复述到页面上，与「前端不展示提示词正文」的口径相抵，改用例随之恢复「整页不得出现系统提示词四字」的严格断言。验证：该页不再含旧文案与那条示例，`prettier --check` / `eslint` / `vue-tsc` 通过，相关用例 43 passed
- [x] 8.5 同页「参考数据 · 有哪些资产」区落地，并按规格对齐三层编号（规格口径：角色带=①、生效装配=②、参考数据=③；页面原把生效装配标为①、参考数据标为②，对话栏原误标为③）：设备块（需要设备的角色给出可用设备候选，不需要的如实说明该角色不需要设备）+ Skill 目录路径清单，整区只读。验证：新增两条用例（设备候选仅在线且未占用 / 规划角色如实说明并列目录路径），三层结构断言改走 `MODEL_DEBUG_LAYER_TITLES`
- [x] 8.6 前端用例同步：`frontend/tests/ai-assistant/p0/useModelDebug.spec.ts`（新文案、新 DTO、新增两条参考数据用例）；并修正该文件里一条过宽断言——「不展示系统提示词」原断言整页文本不得含「系统提示词」四字，而对话空态的一条提问示例正含这四字（属提问示例、非提示词正文），故改为断言「无提示词区块 + 不渲染提示词正文锚点」。验证：`npx vitest run tests/ai-assistant/p0/useModelDebug.spec.ts tests/ai-assistant/p0/model-debug-log-check.spec.ts` → 43 passed
- [x] 8.7 拆逻辑层（加 8.5 后页面到 507 行，超前端 500 行硬门禁）：新增 `composables/useModelDebugFolding.ts` 承接思考过程 / 工具分组的折叠态与切角色重置，页面降到 477 行；顺带清掉删提示词块后留下的死代码——页面里已无引用的 `renderSkillMarkdown` 导入，以及样式表里三个无人使用的类（`.md-group-head--toggle` / `.md-prompt-meta` / `.md-md`，全仓 grep 仅样式表自身命中）。验证：`npx eslint src/modules/ai-assistant` → 0 error；`prettier --check` 样式文件通过；页面行数 477（≤500）
