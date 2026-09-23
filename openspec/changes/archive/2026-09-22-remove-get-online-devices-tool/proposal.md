## Why

设备管理分类下有 `get_online_devices` 与 `list_devices` 两个查设备的工具，但二者口径不一致：`list_devices` 走设备可见性规则（`is_device_visible`）、字段语义化、值保留原生类型；`get_online_devices` 直接过滤 `status=ONLINE`、**完全不过可见性**，且返回值经 `_model_to_dict` 把所有字段 `str()` 化（`id` 变 `'1'`）。结果是同一个"查在线设备"的能力有两份实现、一个绕开权限规则；而 Agent 的 SOP 只需 `list_devices`（它能覆盖 ONLINE 过滤，且 serial/status 都在）。本变更把该工具从平台工具面移除。

## What Changes

- 从 AI 工具注册表删除该工具：`apps/ai_assistant/tools.py` 的函数、`TOOLS` 条目、`TOOL_META` 条目（设备管理分类由 9 个变 8 个）。
- 引擎侧角色工具子集同步：`engines/ai/agentscope/config.py` 的 `VISION_TOOLS` 删该条目（否则是死引用）。
- 仓库内工具手册同步：`engines/ai/skills/platform-tools-manual/SKILL.md` 删表格行、修正数量与分类、并把**既有的 `ocr_page` 漂移一并补齐**（该手册原写「12 个 / 设备管理 9」，漏了视觉识别分类，实际 13 个）。修正后为「12 个 / 设备管理 8 + 设备检查器 1 + 视觉识别 1 + 工作流 2」。
- 前端工具名常量：`frontend/src/modules/ai-assistant/constants.ts` 的 `PLATFORM_TOOL_NAMES` 删该条目。
- 设备三角色系统提示词（DB 数据）同步：**更新迁移 0038 种子**，并新增一个数据迁移做**短语级条件替换**——仅当字段仍含平台原文短语时才把 `get_online_devices` 换成 `list_devices`；用户已改写掉的、或整段重写的提示词 MUST NOT 被改动。
- 测试与 spec 同步：用 `list_devices`（同为无参只读工具）替换测试与 spec 场景里的样例工具。
- **BREAKING（工具面）**：`get_online_devices` 不再是可调用平台工具，调用将返回 404；Agent 与调试页需改用 `list_devices`。
- **不**删 `apps/device_pool/api.py::get_online_devices`——它是设备域内部辅助（`engine_adapter.resolve_device_serial`、`ui_pipeline`、`model_test` 在用），与本次要删的 AI 工具同名但不同物。

## 关联文档

- PRD-00（需求总纲，AI 工具箱增量）
- 前置变更：`add-platform-tool-debug`、`manage-device-assistant-prompts`（提示词种子来源）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `ai-platform-tool-debug`: 「调试页按 schema 收集入参并展示结果」里「无参只读工具执行成功」场景的样例工具由已删除工具改为 `list_devices`。

## Impact

- 后端：`apps/ai_assistant/tools.py`、新增 `apps/ai_assistant/migrations/0039_*.py`（数据替换）、`apps/ai_assistant/migrations/0038_aiagent_device_prompts.py`（种子文本）
- 引擎：`engines/ai/agentscope/config.py`（VISION_TOOLS）
- 技能文档：`engines/ai/skills/platform-tools-manual/SKILL.md`
- 前端：`frontend/src/modules/ai-assistant/constants.ts`
- 测试：`tests/graybox/unit/test_ai_platform_tool_debug.py`、`frontend/tests/ai-assistant/p0/useToolDebug.spec.ts`、`frontend/tests/ai-assistant/p0/ToolboxPanel-tool-debug.spec.ts`
- **不动**：`apps/device_pool/api.py`（含同名函数及其调用方）、工具箱分类定义、设备可见性规则
- 数据库：无 schema 变更；一个可逆的数据迁移（仅 `ai_agents` 自有表）
