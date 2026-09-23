## Why

设备提示词在 AI 工具箱里是**直连数据库**的：保存即改写平台智能体的 `prompt_planner/executor/verifier`。当前**没有任何历史或备份**——改错一版、手滑覆盖就回不去，而这三份提示词直接决定设备任务规划/执行/验收的行为，误改代价高。

## What Changes

- 新增**自动存档**：每次提示词写库都留一份历史；同一智能体的自动存档 MUST 只保留**最新三份**，超出删除最旧。
- 新增**永久存档**：手工保存时创建/覆盖**唯一一份**永久存档；永久存档 MUST NOT 参与自动淘汰，除非手工覆盖或手工删除否则不变。
- 「保存」MUST 先二次确认，文案固定为「此次保存会覆盖之前的备份记录，请确认是否覆盖保存」；取消时 MUST NOT 写库、MUST NOT 改动任何存档。
- **退出编辑自动保存**：退出编辑时若内容相对库中已变化，MUST 自动保存并生成一份自动存档；内容未变 MUST NOT 留档。
- **从历史覆盖当前提示词**：超管 SHALL 能选一份历史存档覆盖当前提示词；覆盖前 MUST 先把当前提示词存为一份自动存档（失败则 MUST 中止覆盖）。
- 前端在**设备提示词三个角色下拉头的右上角**新增「保存」「查看历史记录」；历史抽屉列出自动三份 + 永久一份，支持预览、覆盖当前提示词、删除永久存档。
- 存档的列出 / 读取 / 覆盖 / 删除 MUST 仅超级管理员可用。
- **不**改提示词正文读写语义（仍三份一起、任一份为空拒绝、不部分更新）；**不**为其它"直接改库"动作（删 Skill、工具启停等）做备份；**不**做历史播种。

## 关联文档

- PRD-需求总纲（AI 助手条目：工具箱 / 设备提示词）
- PRD-08-AI助手（工具箱·设备提示词增量；总纲登记的模块 PRD，仓库当前缺正文）
- 相关既有能力：`ai-device-prompts`（本单在其上增量）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `ai-device-prompts`: 新增需求——自动存档保留最近三份、永久存档唯一且不被自动淘汰、保存前二次确认、退出编辑自动保存、从历史存档覆盖当前提示词、存档仅超管可用，以及下拉头入口与历史抽屉的界面行为。现有「展示三角色提示词」「仅超管可保存」「登录用户可读取」三条需求语义不变。

## Impact

- 后端：`apps/ai_assistant/models.py`（新模型 `AIDevicePromptArchive`）+ 新迁移 `0042`；`apps/ai_assistant/api.py`（存档写入/保留策略/覆盖流程/删除）；`apps/ai_assistant/views_prompts_drf.py`（历史端点 + `update` 增加 `archive` 参数）；`apps/ai_assistant/urls.py`（路由）
- 前端：`frontend/src/modules/ai-assistant/api/toolbox.ts`（历史接口与 DTO）、`composables/useDevicePrompts.ts`（确认、退出编辑自动保存、历史状态）、`components/ToolboxPanel.vue`（下拉头右上角按钮）、新增历史抽屉组件
- 接口契约：新增历史存档列表/详情/删除/覆盖端点；`POST /api/ai/device-prompts/update` 新增 `archive` 参数（`auto` 缺省 = 写库并记自动档，`permanent` = 覆盖永久档）
- 测试：后端单测（保留三份、永久唯一、覆盖前自动存档、权限、空值拒绝）+ 前端 spec（确认弹窗、退出编辑自动保存、抽屉动作）
- 文档：AI 助手接口文档「设备提示词」段补历史存档端点与语义
- 迁移 / 依赖：1 个新迁移（新表），无新依赖
