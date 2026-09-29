# 提示词收回引擎（前端不再展示、不再可编辑）

## 为什么

平台设备控制三角色的系统提示词，曾从引擎常量改造成**库表字段 + 前端可编辑**（`2026-09-16-manage-device-assistant-prompts`，并在 `2026-09-23-add-device-prompt-archive`、`2026-09-24-independent-device-prompt-edit` 上叠加了历史存档与逐份编辑）。现在这个决策被**收回**：

1. 提示词属于引擎行为的一部分，应随代码走——与工具子集常量（`VISION_TOOLS` / `VERIFIER_TOOLS`）同层同源，而不是散落在数据库里靠迁移逐条打补丁。
2. 前端不应展示模型系统提示词。展示既暴露内部实现，也让「改提示词」看起来像业务配置；它实际是随版本发布的引擎契约。
3. 并存两处真相源会造成漂移：既有代码写死「引擎常量为空、由 Django 注入」，又有迁移在改动库中正文，任何一处更新都可能对不上。

## 改什么

### 一、提示词回到引擎常量（唯一真相源）

- `engines/ai/agents/config.py`：写入三份提示词正文（`PLANNER_PROMPT` / `VISION_PROMPT` / `VERIFIER_PROMPT`），内容取自**收回当时库中正在运行的那一版**，逐字保留，行为不回退。
- `engines/ai/agents/model.py`：角色自带提示词——`RoleSpec.prompt` 从「留空占位」恢复为真实正文，装配时缺省取本角色 `spec.prompt`。角色与提示词的对应关系重新内聚在角色类里。
- 拆掉 Django → 引擎的提示词注入通道：`TaskRequest.system_prompts` 删除，`build_device_models(system_prompts=...)` 入参删除，`engine_adapter._system_prompts` 删除。

### 二、数据库与接口面下线

- `ai_agents.prompt_planner / prompt_executor / prompt_verifier` 三列删除（迁移 `0051_drop_device_prompts`）。
- `AIDevicePromptArchive` 模型与 `ai_device_prompt_archives` 表删除。
- HTTP 端点整组下线：`GET /api/ai/device-prompts/`、`POST /api/ai/device-prompts/update/`、`/api/ai/device-prompt-archives/*`（列表 / 详情 / 覆盖 / 删档）；`views_prompts_drf.py` 整文件删除；`api.py` 中提示词读写与存档共 154 行删除。
- 收回前把库中三份正文与存档正文落一份存档：`dev_docs/DEV_TEST/设计方案与报告/AI设备提示词收回存档.json`。

### 三、前端不再展示提示词

- 装配台「设备提示词」来源整体下线（工具来源由六源收敛为五源）：`DevicePromptPanel.vue`、`DevicePromptHistoryDrawer.vue`（含样式）、`useDevicePrompts.ts`、`constants.ts` 的提示词常量、`api/toolbox.ts` 的提示词读写与存档六个函数全部删除。
- 模型调试页的「系统提示词」折叠块删除；`GET /api/ai/model-debug/{role}/` 响应不再下发 `prompt` 字段（调试对话仍使用该角色实际提示词，只是不展示正文）。
- 模块约束 `frontend/src/modules/ai-assistant/AGENTS.md` 同步为「五源 + 提示词为引擎常量、前端不展示」。

### 四、顺带记录：引擎目录改名

同批工作区变更中还包含 `engines/ai/agentscope/` → `engines/ai/agents/`（含注册表路径、apps 与 tests 全部引用、架构守卫），一并在此登记。引擎注册名 `agentscope`（`settings.AI_ENGINE`）保持不变——它表达「用的是 AgentScope 框架」，与目录名无关。

## 追补（同批收口）：调试页现场清理与规格去重

删掉调试页「系统提示词」折叠块后，同一页留下三处现场，且与规格里一条**从未删除**的旧要求互相呼应。它们在实现上与本单同源同页，故不拆单，随本单一起收口：

1. **规格去重**：`ai-model-debug` 主规格的「单角色调试对话」仍写着「MUST NOT 挂载或调用任何工具 / MUST NOT 触发真机操作 / 单次请求超时 MUST 为 5 分钟」，与后来加入的「调试对话按该角色真实装配运行」（要求必须挂真实工具子集、MUST NOT 以空工具集运行）、「需要设备的角色须先选定设备并获得一次性授权」、「调试对话不设前端等待上限」三条直接冲突。本单以 delta 把该条整条 **REMOVED**（含 Reason / Migration），并把其中仍然有效的约束（引擎侧系统提示词、不落库、回复展示与可读错误）以 **ADDED** 的新条「单角色调试对话的输入与留痕约束」承接。**以代码事实为准，删的是失真的旧规格文，不是让代码回退。**（口径说明：`openspec validate` 拒绝 MODIFIED 丢场景，故不能只删其中一条场景，只能整条移除后另立新条。）
2. **页面文案**：调试页「生效装配」区底部仍写着「调试对话不挂载这些工具……不触碰真机」——它照抄的正是上面那条从未删除的旧要求，与真实行为（挂该角色真实工具、会真实操作所选设备）相反，且被「调试对话不设前端等待上限且如实描述行为」明令禁止。改为如实描述。
3. **参考数据区与死字段**：删掉提示词折叠块后，「③ 参考数据」区成为空壳（规格要求该区放设备与 Skill 目录）；前端 `ModelDebugRoleConfig` 仍声明 `prompt` 字段，而后端 `build_role_debug_configs` 已不下发、页面与全模块零读取；页面区块编号与规格三层口径不一致（页面把生效装配标为①、参考数据标为②，规格为角色带①/生效装配②/参考数据③）。③ 区按规格填「设备（是否需要设备 / 可用设备候选）+ Skill 目录路径」，死字段删除，编号口径对齐。

**非目标（追补部分）**：不改工具子集与设备池口径（执行模型调试仍可调用设备池工具，属已知取舍）；不补服务端硬超时、不加「停止」按钮、不做费用显示与调试留痕审计——这些是独立的新增能力，另行立项；前端请求的固定等待上限问题同样归那一单。

## 影响面

- 规格：`ai-device-prompts` 整体作废（删除）；`ai-engine-protocol`、`ai-model-debug`、`ai-device-planner-tools`、`ai-executor-output`、`ai-verifier-output` 五份规格中「提示词存库 / 靠迁移下发 / 前端展示」的表述改为「引擎常量 / 不展示」。
- 测试：删除 `test_device_prompts.py`、`test_ai_device_prompt_archive.py` 与三个前端提示词用例文件；`test_ai_planner_page_flow_guidance.py` 承接原文件里与提示词存放位置无关的迁移插入逻辑用例。
- 文档：`dev_docs/DEV_TEST/接口文档/API-AI助手.md` 删除 8.2a~8.2f 六节与总览表六行，模型调试配置接口补「不下发提示词」。
- **不可逆**：库中三列与存档表删除后不能再从库里读回提示词；已落 `AI设备提示词收回存档.json` 作为追溯件。历史迁移（0038~0050）按规矩不动。

## 非目标

- 不改三份提示词的**内容**（逐字沿用收回当时的运行版本，不做措辞优化）。
- 不改工具子集、模型路由、日志证据链路与工作流。
- 不改引擎注册名、环境变量与部署方式。
