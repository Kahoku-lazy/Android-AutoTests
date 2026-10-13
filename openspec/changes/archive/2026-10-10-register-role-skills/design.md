## Context

见 proposal.md 的 Why。`engines/agents` 的执行工具包原先只包装设备工具。`Toolkit` 只在构造时接受 `skills_or_loaders`，没有事后注册的公开方法；技能说明在每次回复组装提示词时才扫描。`engines/ai` 的 `build_toolkit` 按单个技能目录挂载，且不扫子目录。

## Goals / Non-Goals

**Goals:**

- `BaseRole.register_skills` 把目录、`Skill` 或 `SkillLoaderBase` 追加到当前工具包的 basic 组。
- `tools_config.EXECUTOR_SKILLS_NAMES` 决定执行角色工具包带哪些技能目录，并扫描子目录。
- 相对路径按仓库根目录解析，同一目录不重复挂载。

**Non-Goals:**

- 不改 `engines/ai` 的技能上传、启停和 `build_toolkit` 默认不扫子目录的行为。
- 不把 `engines/agents/role/executor.py` 迁到 `BaseRole`。
- 不在 `start()` 里自动再注册一份已经写进工具包的名单。

## Decisions

### 注册写进 basic 组的 `skills_or_loaders`

`Toolkit` 没有公开的补注册接口。basic 组的 `skills_or_loaders` 在每次 `get_skill_instructions` 时被读取，所以在 `start()` 之前追加，下一次回复就能看到；已经启动后再追加，同样要到下一次回复才进入提示词。

备选：重建整个 `Toolkit`。会丢掉已经挂上的工具包装，因此不采用。

### 角色注册与执行工具包都扫描子目录

配置路径 `engines/agents/skills/executor` 下面还有 `platform-tools-manual/SKILL.md`。`LocalSkillLoader(scan_subdir=False)` 只会看该目录自己的 `SKILL.md`，扫不到子技能。因此 `register_skills` 默认 `scan_subdir=True`，`engines/agents` 的 `build_toolkit` 增加同名参数，执行工具包显式传入 `True`。`engines/ai` 的副本保持默认 `False`，避免把单个技能目录里的嵌套说明也收进来。

### 相对路径按仓库根目录解析

`LocalSkillLoader` 会把相对路径按进程当前目录转成绝对路径。配置写的是仓库相对路径，所以在交给加载器之前，用 `engines/agents` 文件位置反推仓库根目录再拼接。

### 按绝对目录去重

再次注册时比较加载器的 `directory` 或技能的 `dir`。相同绝对路径跳过，避免提示词里同一技能出现两次。不同目录下的同名技能仍由框架按后写覆盖，并打出警告。

## 模块防火墙自检

- 不新增跨 App import。改动只在 `engines/agents`，继续使用已有的 AgentScope 依赖。
- 不写数据库，不经过 `api.py`。
- 前端不参与，仪表盘无写操作。

## Risks / Trade-offs

- [追加的是工具包内部列表，框架升级后字段可能改名] → 注册只碰 basic 组的 `skills_or_loaders`；缺少 basic 组时直接报错，而不是静默丢掉技能。
- [父目录扫描会收进该目录下全部 `SKILL.md`] → 执行角色的名单写成希望暴露的那一层目录；不要把整个 `engines/agents/skills` 放进名单。
- [已启动后再注册要等下一次回复] → 在方法说明里写明，调用方在 `start()` 之前注册。
