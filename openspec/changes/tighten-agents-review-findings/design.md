## 背景

复盘结论（见对话）：`workflow/` 的设备侧遵守「workflow 只编排、不建角色」，用例侧不遵守；注释漂移可量化（17 个 `module-summary` + 一批缺失段），文档路径也有三处指向已迁移的位置。

## 决策

### D1：成对装配放在包根 `case_roles.py`，不放在 workflow、也不塞进 tools_config

三个候选落点：

| 落点 | 问题 |
| --- | --- |
| `workflow/case_goal_workflow.py`（现状） | 直接违反红线；workflow 既编排又装配 |
| `agent_builders.py` | 需要 import `ArtifactStore`（workflow 的数据契约），方向反过来 |
| `tools_config.py` | 它是「工具分配」入口，不该负责建角色 |

因此新增 `engines/agents/case_roles.py`：只做**角色成对装配**这一件事，依赖 `agent_builders`（建角色）与 `tools_config`（取产物工具），不依赖 workflow 的任何模块名，只按 `store` 对象的存在使用它（结构化传参，无类型耦合）。

`add_tool` 是异步方法，所以函数为 `async`，调用方 `await`。

### D2：`case_goal_workflow` 只保留编排

改为 `writer, verifier = await build_case_authoring_roles(store, requirement_text=..., )`，删除三处装配 import。这样「一个文件里要么编排、要么装配」的边界重新成立，且与设备侧的工厂注入范式对齐。

### D3：模块功能只改文字，不动行为

17 个模块逐个按「本模块做什么」重写一句，避免编号列表、调试命令、类名。不改任何代码、不加字段，`版本`/`修改时间` 也不动（纯注释准确性修正，避免无意义的版本噪声）。

### D4：文档对齐现实，不对齐规划

根 `AGENTS.md` 的技能/提示词/MCP 三处改成**当前真实存在**的位置（`config/data/skills`、`config/data/prompts` + `role_sys_prompts.py`、无 `mcp_config/`）。技能当前未装配是另一个待办，不在文档里写成「已可用」。

## 风险

| 风险 | 处置 |
| --- | --- |
| 移动装配后循环导入 | `case_roles` 在模块级只 import `agent_builders` 与 `tools_config`；`tools_config` 对 `workflow.tools` 的导入本就是运行期延迟导入，链路不变 |
| 装配行为发生变化（例如只读标记丢失） | 新函数逐字照搬原三行调用（`read_only` / `requirement_text` 原样传），并用测试断言两边工具集与只读性 |
| 文档改动与实现再次漂移 | 只写「路径 + 唯一入口」，不重复描述行为；行为细节留在模块 docstring |
