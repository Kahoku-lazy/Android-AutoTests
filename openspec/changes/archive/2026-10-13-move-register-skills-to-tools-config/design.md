## Context

见 `proposal.md` - Why。实测现状：

- `BaseRole` 现有 18 个成员，其中 `register_skills` 与 5 个私有辅助只服务"往工具包挂技能"。
- `BaseRole._resolve_skill_dir(directory)`：绝对路径原样返回，相对路径拼 `_REPO_ROOT`（`base.py` 的 `parents[3]`）。
- `tools_config.resolve_skill_dirs(names)`：同样逻辑，跳过空串，返回列表；该模块已有 `_REPO_ROOT`（`parents[2]`）。
- 调用方：`executor.py:29` 一处；测试 `test_executor_tool_groups.py` 第 175 / 178 / 185 / 186 行共 4 处，其中 178 行断言组不存在时抛 `ValueError`。
- `tools_config.py` 已导入 `Toolkit` / `ToolGroup` / `LocalSkillLoader` / `Path`，但未导入 `os` / `Sequence` / `Skill` / `SkillLoaderBase`。

## Goals / Non-Goals

- Goals：`BaseRole` 只剩「配置（含按配置创建智能体）+ 运行 + 中断」；技能注册归工具配置层；消掉路径解析的重复实现。
- Non-Goals：
  - 不折进 `build_executor_toolkit`（保持"显式注册"的现有调用时序）。
  - 不改技能目录内容、不改 `EXECUTOR_SKILLS_NAMES`、不改 `ToolGroupSpec`。
  - 不改异常语义（`basic` 缺失仍 `RuntimeError`；其它组缺失仍 `ValueError`；非法 skill 来源仍 `TypeError`）。

## Decisions

**D1：`register_skills` 变模块函数，首参 `toolkit`（用户已选）。**
签名：`register_skills(toolkit: Toolkit, skills: Sequence[_SkillSource], *, scan_subdir: bool = True, group_name: str | None = None) -> None`。移动而非删除 —— 直接删会让 `ExecutorRole` 丢掉 platform_business 技能包，属功能退化。

**D2：`_resolve_skill_dir` 不搬，复用同模块既有的 `resolve_skill_dirs`。**
`_skill_sources` 内改为 `resolve_skill_dirs([directory])[0]`。依据：两者是同一套"绝对路径原样、相对路径拼仓库根"的逻辑；`tools_config` 已有 `_REPO_ROOT`。**注意 `parents` 层级不同**：原实现位于 `engines/agents/role/base.py`（`parents[3]`），`tools_config.py` 在 `engines/agents/`（`parents[2]`）—— 复用既有常量正好避免抄错层级。任务里为此加等价断言。

**D3：`_basic_tool_group` / `_tool_group` 变模块私有函数，首参为 `toolkit`。**
`_tool_group(toolkit, name)` 的异常语义逐字保留：遍历 `toolkit.tool_groups` 找同名组；找不到且 `name == "basic"` → `RuntimeError("工具包缺少 basic 组")`；否则 → `ValueError(f"工具包中不存在工具组: {name}")`（测试第 178 行断言这条 `ValueError`）。

**D4：`_skill_sources` / `_source_dir` 逐字搬；`_SkillSource` 别名归 `tools_config.py`。**
`_skill_sources` 的 `TypeError` 文案与"空串跳过"行为保持不变。

**D5：`BaseRole` 的失效导入按 ruff `F401` 判定删除。**
预计失效：`import os`（只服务 `_source_dir`）、`Sequence`（只服务两个签名）、`Path`（只服务 `_REPO_ROOT` / `_resolve_skill_dir`）、`LocalSkillLoader` / `Skill` / `SkillLoaderBase`（只服务技能来源）；模块常量 `_REPO_ROOT` 与 `_SkillSource` 一并移除。

**D6：测试改为直接对 `toolkit` 调模块函数。**
第 173-178 行那条用例的 `role = _role(build_toolkit([]))` 简化为 `toolkit = build_toolkit([])`；第 181-188 行那条用已有的 `toolkit`，去掉 `role = _role(toolkit)`。
理由：`_role(...)` 只用来拿工具包，改后不再需要构造 `BaseRole`；留着会变成未使用局部变量（ruff `F841`）。`_role` 助手本身仍被其它用例使用，保留。

**D7：以 `skip_specs: true` 退出 specs 阶段。**
纯重构：技能注册的语义与异常全部逐字保留，只换宿主与调用形态。

## Risks / Trade-offs

- [仓库根层级抄错（`parents[3]` vs `parents[2]`）] → D2 直接复用 `tools_config._REPO_ROOT`；4.2 断言"同一个相对目录解析出的绝对路径 == `Path(tools_config.__file__).resolve().parents[2] / dir`"，并与旧实现口径对照。
- [漏改调用方] → 全仓检索 `.register_skills(` 必须 0 命中；AST 断言 `executor.py` 与测试都从 `tools_config` 取 `register_skills`。
- [异常语义被改，测试红] → 第 178 行那条 `pytest.raises(ValueError, match="missing-group")` 原样保留，作为语义守卫。
- [删出未使用导入 / 未使用局部变量] → 以 ruff `F401` / `F841` 为准（D5 / D6）。
- [技能目录解析结果变化导致技能挂不上] → 4.2 的运行期断言直接检查挂载后的 `skills_or_loaders` 指向的目录存在且是仓库内的 `engines/agents/skills/executor`。

## Migration Plan

无部署动作：三个文件都不在平台运行链路的 import 图上。
回退策略：把六个函数搬回 `BaseRole`（恢复为方法）、恢复 `_resolve_skill_dir` 与相关导入，并把 `executor.py` 与测试改回 `self.register_skills(...)`。

## Open Questions

- `tools_config.register_skills` 是否应改为"幂等注册进 `build_executor_toolkit`"（即把 `ToolGroupSpec.skill_dirs` 派生的加载器与显式注册合一）—— 本次不做；若做，属行为与时序调整，应另立一单。
