## Why

AI 工具箱的平台业务工具目前只能启停，无法在管理面用真实入参跑一遍并查看返回。排查工具契约、设备占用和截图结果必须走完整 Agent 任务，成本高且看不清单次工具输出。需要一条给人用的 JWT 调试链路，直调现有 `tools.py` 函数。

## What Changes

- 装配台每张平台工具卡增加「调试」入口，进入 L2 页 `/ai-assistant/toolbox/tools/:toolName`：展示说明、按 schema 生成入参表单、执行并展示返回（截图工具出图 + 摘要）。
- 新增 JWT 接口：读取工具入参 schema；按工具名 invoke。`user_id` 由服务端从 JWT 注入，请求体不得覆盖。
- 权限：登录用户可进页、可读 schema、可执行只读工具；写工具仅超级管理员可执行，且必须二次确认；非超管进写工具页可看说明与表单，执行按钮禁用。
- 停用的平台工具仍可调试（与「交给助手」启停解耦）。
- **不**把 SPA 接到 `/api/ai/tools/{module}/{action}` 内部令牌网关；不新增 WS；不发 Agent 任务。

## 关联文档

- PRD：`dev_docs/ARCH_PRD/PRD-00-需求总纲.md`（AI 助手 / 工具箱；无独立「工具调试」子 PRD，本变更为工具箱增量）
- ARCH：`dev_docs/ARCH_PRD/ARCH-00-平台总体架构.md`（通道 ① JWT HTTP；通道 ③ 仍为 Agent 进程内调工具；禁止前端走内部网关）
- API：`dev_docs/DEV_TEST/接口文档/API-AI助手.md`（将增补 schema / invoke）
- 主 spec：无既有「平台工具调试」能力；子页导航沿用 `openspec/specs/frontend-doodle-subpage-nav/spec.md`（实现复用，不改需求）

## Capabilities

### New Capabilities

- `ai-platform-tool-debug`: 平台业务工具调试页与 JWT 调用（schema、invoke、只读/写权限、二次确认、结果展示）

### Modified Capabilities

- （无）既有 `available-tools` 启停语义不变；`frontend-doodle-subpage-nav` 需求不变，本页复用 Skill 查看器同款面包屑。

## Impact

- 后端：`apps/ai_assistant/tools.py`（入参 schema + 按名调用）、新建 `views_*_drf.py` + `urls.py`；单测（schema、invoke 只读/写 403、user_id 注入、未知工具 404）；`API-AI助手.md`
- 前端：`ToolboxPanel` 调试按钮、`routes.ts`、新 L2 页 + composable + `api/toolbox.ts`；模块 `AGENTS.md`；组件/composable 单测
- 引擎 / 内部网关 / 迁移：无
