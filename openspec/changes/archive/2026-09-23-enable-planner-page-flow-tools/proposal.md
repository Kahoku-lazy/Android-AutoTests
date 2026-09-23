## Why

设备执行链路的 planner 工具子集是**空的**：`engines/ai/agentscope/config.py` 里 `DEVICE_PLANNER_TOOLS = []`，注释称「页面流代码重构中，规划模型不再读取页面流」。但仓库内工具手册一直写着「planner 用 DEVICE_PLANNER_TOOLS（list_page_flows / get_page_flow）读页面流」——**手册与代码长期不一致**。查证：全仓归档里**零处**记录过这次清空（未走 OpenSpec），所以没有决策依据可循。本次让代码符合手册：planner 真的拿到这两个工具；并补上「去用」的那一半——只装配工具而提示词零处提及，模型很可能一次都不调。

## What Changes

- `DEVICE_PLANNER_TOOLS` 由 `[]` 改为 `["list_page_flows", "get_page_flow"]`，并修正注释（不再声称「不再读取页面流」）。
- 补一条**子集守卫**：三个角色的工具子集 MUST 只引用已注册工具。理由是装配按名取子集且**对缺失名静默跳过**（`AgentRole._select_tools`），拼错或改名后不会报错、只会静默少装配。
- 手册该句由此变为**准确**，无需改动（这也是本变更选择方式的理由）。
- **同时**给 planner 默认提示词加一条指引（在「步骤要求」第 7 条后追加第 8 条）：规划前先用 `list_page_flows` 查看平台有哪些页面流文档（每条含目录路径与层级），需要某篇细节再用 `get_page_flow` 读取语义摘要。现网 planner 提示词（1123 字）**零处**提到页面流，只装工具不足以让它被使用。
- 指引的两条下发路径**同单交付**：新装的种子（迁移 `0038` 的 `_SNAPSHOT_PLANNER`）与存量库（新增迁移 `0041`，**短语级条件插入 + 可逆**）。管理员已改写过的提示词 MUST NOT 被覆盖。
- **不**改 executor / verifier 的提示词（它们已含页面流/截图相关表述）。
- **不**改 `react_config`：`ReActConfig.max_iters` 默认 **50**，planner 的 ReAct 循环本来就足以调工具（executor 显式设 8）。

## 关联文档

- PRD-00（需求总纲，AI 工具箱增量）
- 手册真相源：`engines/ai/skills/platform-tools-manual/SKILL.md`（该句为本变更的依据）
- 前置变更：`expand-page-flow-listing`（`list_page_flows` 改为全量 + 目录层级）

## Capabilities

### New Capabilities

- `ai-device-planner-tools`: 设备执行链路 planner 的工具子集与默认提示词——规划阶段可读页面流文档（列表与语义摘要），默认提示词含阅读指引并随迁移下发到存量库，且三角色子集不得引用未注册工具。

### Modified Capabilities

（无）

## Impact

- 引擎：`engines/ai/agentscope/config.py`（`DEVICE_PLANNER_TOOLS` 内容与注释）
- 数据库：`apps/ai_assistant/migrations/0038_aiagent_device_prompts.py`（planner 种子文本）+ 新增 `0041_*.py`（存量库条件插入，可逆）；无 schema 变更
- 测试：新增 `tests/graybox/unit/test_ai_role_tool_subsets.py`（三角色子集守卫 + planner 含页面流工具）；`test_device_prompts.py` 补迁移逻辑用例（纯函数、零 DB 写）
- 手册 / 前端：无（手册该句因本变更而变准）
- **不动**：executor 的 `VISION_TOOLS`（14 个）、verifier 的 `VERIFIER_TOOLS`（`screenshot_page`）、executor/verifier 的提示词、提示词的读写接口（`ai-device-prompts` 能力）
