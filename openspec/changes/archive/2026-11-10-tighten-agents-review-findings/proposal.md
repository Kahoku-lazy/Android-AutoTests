## Why

`engines/agents` 设计复盘（2026-11-09）确认两处问题，均不改变对外行为，故不涉及规格：

1. **workflow 违反自身边界**：`engines/agents/AGENTS.md` 红线写着「workflow 禁止创建角色、配置提示词或绑定工具」，设备侧遵守（`platform_run` 只传工厂函数），但用例编写侧没有——`workflow/case_goal_workflow.py` 直接 `build_case_writer()` / `build_case_verifier()`，并往两个角色的 toolkit 上挂产物工具。同一目录两种范式，后来者很难判断哪条才对。
2. **注释与文档漂移**：`engines/agents` 全包文档检查 100 error，其中 17 个模块的「模块功能」不是一句话职责（`platform_run` 写成「取消正在跑的 SOP 事件流」、`ui_auto_workflow` 写成类名、`fold` 写成「一次折叠的产出」、`event_sink` 只写了接收方）；根 `AGENTS.md` 仍写着已不存在的 `skills/`、`prompts/`、`prompt_config.py`，`engines/agents/AGENTS.md` 表里还留着不存在的 `mcp_config/`。

## What Changes

- **用例角色成对装配移出 workflow**：新增 `engines/agents/case_roles.py`，提供 `build_case_authoring_roles(store, *, requirement_text)`，一次建好编写/验收角色并挂上产物工具；`case_goal_workflow` 只调用它，不再 import `build_case_writer` / `build_case_verifier` / `build_case_artifact_tools`。
- **模块「模块功能」逐条改成一句话职责**（17 个模块），与实现一致；不改变任何代码行为。
- **文档对齐现实**：根 `AGENTS.md` 的技能/提示词/MCP 三处路径与文件名；`engines/agents/AGENTS.md` 的 `mcp_config/` 行。

## Acceptance

1. `workflow/case_goal_workflow.py` 源码里不再出现 `build_case_writer` / `build_case_verifier` / `build_case_artifact_tools`；两个角色的装配只经 `case_roles.build_case_authoring_roles`。
2. `build_case_authoring_roles` 返回的角色已挂好产物工具：编写角色可写、验收角色只读。
3. `engines/agents` 文档检查的 `module-summary` 由 17 降到 0；根 `AGENTS.md` 与 `engines/agents/AGENTS.md` 不再出现不存在的路径。
4. `python run.py check` 通过；相关 pytest 全绿。

## Capabilities

### New Capabilities

无（纯重构与文档，`skip_specs: true`）。

## Impact

- 引擎：新增 `engines/agents/case_roles.py`；`engines/agents/workflow/case_goal_workflow.py` 改为只做编排。
- 文档：根 `AGENTS.md`、`engines/agents/AGENTS.md`、17 个模块的模块 docstring。
- 测试：新增「workflow 不得建角色」的契约断言与「成对装配已挂工具」的装配断言；既有 `test_case_goal_workflow.py` 应继续绿。
- 不在本期：技能断路的修复、`workflow/` 拆包、`event_sink` 拆分（复盘里的其它项，另行立单）。
