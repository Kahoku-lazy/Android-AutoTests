## Why

上一单已把 `BaseRole` 收缩到「配置 + 运行 + 中断」。按同一口径再核一遍，仍有一类成员不属于它：**往工具包里挂技能**（`register_skills`）及其 5 个只服务它的私有辅助（`_basic_tool_group` / `_tool_group` / `_skill_sources` / `_resolve_skill_dir` / `_source_dir`）。这是**工具装配**，不是"智能体的配置/运行/中断"。

它们的天然归属就是 `engines/agents/tools_config.py` —— 该模块已经拥有角色工具包的构造（`build_executor_toolkit` / `build_verifier_toolkit`）、技能目录名表（`EXECUTOR_SKILLS_NAMES`）、以及 `ToolGroupSpec.skill_dirs`；甚至连"相对路径按仓库根解析"的 `resolve_skill_dirs` 与 `_REPO_ROOT` 都已经在那里。

顺带消掉一处重复实现：`BaseRole._resolve_skill_dir` 与 `tools_config.resolve_skill_dirs` 是同一套逻辑的两份代码，搬移后用后者即可。

## What Changes

- `engines/agents/tools_config.py`：新增模块函数 `register_skills(toolkit, skills, *, scan_subdir=True, group_name=None)` 与四个私有辅助 `_basic_tool_group(toolkit)` / `_tool_group(toolkit, name)` / `_skill_sources(skills, *, scan_subdir)` / `_source_dir(source)`；新增 `_SkillSource` 别名与 `import os`、`Sequence`、`Skill`、`SkillLoaderBase` 导入。
- **不再复制** `_resolve_skill_dir`：`_skill_sources` 复用本模块既有的 `resolve_skill_dirs`（`_REPO_ROOT` 本就在该模块）。
- `engines/agents/role/base.py`：删除 `register_skills` 与上述五个私有辅助，以及 `_REPO_ROOT`、`_SkillSource`；按 ruff `F401` 清理随之失效的 `import os`、`Sequence`、`Path`、`LocalSkillLoader`、`Skill`、`SkillLoaderBase`。
- `engines/agents/role/executor.py`：改调模块函数 —— `register_skills(self.role.toolkit, EXECUTOR_SKILLS_NAMES, group_name="platform_business")`。
- `tests/graybox/unit/test_executor_tool_groups.py`：两条 `register_skills` 用例改为直接对 `toolkit` 调模块函数（不再需要构造 `BaseRole`），并去掉因此变成未使用的局部变量。
- **Non-goals**：不改技能目录内容与 `EXECUTOR_SKILLS_NAMES`；不改 `build_executor_toolkit` 的构造时序（技能仍由调用点显式注册，不折进构造器）；不改 `_tool_group` / `_skill_sources` 的异常语义；不动 `reply` / `reply_stream` / `interrupt` / `start` 等保留成员。

## 关联文档

无关联需求编号。纯重构（成员换宿主 + 去重一份路径解析），行为不变，不进入 PRD / ARCH 编号体系。按 schema 约定设 `skip_specs: true`。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

无。技能注册的语义（挂到哪一组、重复目录跳过、组不存在报错、非法类型报错）逐字保留，只换宿主与调用形态。故以 `skip_specs: true` 退出 specs 阶段。

## Impact

- 代码：`engines/agents/tools_config.py`、`engines/agents/role/base.py`、`engines/agents/role/executor.py`（均未被 git 跟踪）。
- 测试：`tests/graybox/unit/test_executor_tool_groups.py` 两条用例（未被 git 跟踪）。
- `BaseRole` 最终成员集收敛为 13 个：配置 `__init__` / `start` / `_react_config` / `_context_config`；运行 `reply` / `reply_stream` / `_reply` / `_reply_stream` / `_running` / `_require_agent` / `_user_msg`；中断 `interrupt` / `_interrupt_paused`。
- 依赖：无新增（`tools_config.py` 已有的 `agentscope.skill.LocalSkillLoader` 正是所需）。
- 平台侧零改动：`engines/ai/**`、`apps/**`、`frontend/**` 不动。
