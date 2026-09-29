## Why

平台工具调试页（`/ai-assistant/toolbox/tools/:toolName`）的参数表单目前只显示英文参数名（如 `keyword`、`at`、`serial`），用户必须自己猜每个参数是干什么的。工具函数的 docstring 里其实已经写好了中文说明，但 schema 没有把它下发，前端也就无从展示。需要让参数以「中文名（english_name）+ 必填/可选标签」呈现，并保留英文名可对照，便于使用与排查。

## What Changes

- 参数 schema 新增**中文短名**（`label`）与**中文说明**（`hint`，取自工具 docstring 的 `Args:` 段），未知参数回退英文名、没有说明则留空
- 调试页参数标签改为 **「中文名（english_name）」**，其后跟**必填 / 可选**标签与类型；英文名 MUST 保持可见（便于对接口与排查）
- 说明以悬浮提示呈现，不把长文铺在表单里
- 中文名由**后端集中维护**（参数名 → 中文短名，支持工具级覆盖），前端只渲染，不硬编码任何中文映射
- 现有候选下拉（`serial` 的候选设备）与本地校验文案行为不变

## 关联文档

关联需求编号 **PRD-08（AI 助手 · 设备操控）**；本次来源为需求方在工具箱评审时提出的补充要求：「工具箱的参数，前端页面需要按照功能使用中文命名，然后管理对应的参数英文名称……例如 keyword 参数以『日志关键词搜索（keyword）』并跟一个可选标签」。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `ai-platform-tool-debug`: 入参 schema 契约新增中文名与中文说明字段；调试页参数标签的显示口径改为「中文名（英文名）+ 必填/可选」

## Impact

- **代码**
  - `apps/ai_assistant/tools.py`：参数标签表 + docstring `Args:` 说明解析，`get_tool_debug_schema` 下发 `label` / `hint`
  - `frontend/src/modules/ai-assistant/ToolDebugPage.vue`：参数标签渲染改为「中文名（english）」，说明走悬浮提示
  - `frontend/src/modules/ai-assistant/api/toolbox.ts`：参数 DTO 增加 `label` / `hint`
  - `frontend/src/modules/ai-assistant/AGENTS.md`：模块说明补一句参数标签口径
- **数据**：不新增表、不写库
- **测试范围**：后端单测（schema 下发 label/hint、未知参数回退、docstring 解析）+ Python 侧前端契约对拍（调试页模板使用了 `label` 且保留英文名与必填/可选）；前端门禁走 `vue-tsc` + `eslint` + `prettier`
