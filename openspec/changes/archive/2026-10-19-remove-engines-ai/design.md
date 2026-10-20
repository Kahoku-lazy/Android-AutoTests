## Context

见 proposal.md 的 Why。当前 `task_runner` 已经只调用 `run_platform_sop`，但 `engine_adapter` 在导入时仍引用 `engines.ai.base` 的 `ModelSpec` 与 `TaskRequest`。`engines/ai/skills` 目录不存在。SOP 的角色技能在 `engines/agents/skills/executor`，由 `tools_config.py` 装配，不走共享技能扫描。`ToolSpec` 已在 `engines/agents/tools/tool_base.py`。

## Goals / Non-Goals

**Goals:**

- 删掉 `engines/ai` 之后，Django 启动任务与打开任务页不再导入该包。
- 执行与验收模型仍从控制设备线路组装成 SOP 使用的 `ModelConfig`。
- 共享技能上传落到 `engines/agents/skills/shared`，并继续只扫描该目录的一级 `SKILL.md`。

**Non-Goals:**

- 不改 SOP 的步骤、工具清单、关闭任务与同设备排队。
- 不把 `common` / `executor` 并进共享工具箱，也不改 `tools_config.py` 的技能名单。
- 不改任务详情对执行结果、验收结果的展示。
- 不把旧三角色过程日志迁到新文件。

## Decisions

1. **整包删除，不留转发模块。** `engines/ai/tools/tools_base.py` 现在只把 `ToolSpec` 转发到新位置，没有任何调用方。备选是留这个转发文件，这样目录删不干净，导入仍会经过已删除包。选择连同转发一起删除。

2. **模型组装留在 `engine_adapter.sop_role_models`。** 该函数直接构造 `engines.agents.role.config.ModelConfig`，不再经 `ModelSpec`。校验仍用现有的 provider 集合、模型名与密钥非空。只读执行与验收，不读规划角色。`build_request` 与 `TaskRequest` 只服务旧引擎，随调用方删除。`resolve_device_serial` 保留，任务页仍用它。备选是把校验搬进 SOP 入口；入口今天只收已经组装好的模型，搬进去会让引擎认识平台配置结构。

3. **共享技能使用子目录 `shared`。** 扫描规则仍是根下一级且含 `SKILL.md`。若把根直接改成 `engines/agents/skills`，扫到的是没有 `SKILL.md` 的 `common` 与 `executor`，工具箱仍为空，上传还会和角色目录并列。备选是递归扫描这两个角色目录；那会把 SOP 技能暴露成可停用的共享项，超出本单。实施时创建空的 `shared` 目录，并放一个让 Git 能跟踪空目录的占位文件。

4. **测试与命令随引擎删除，不改写成调用旧工作流。** `model_test`、`planner_eval`、`ui_pipeline`、`model_assembly.py`，以及只导入 `engines.ai` 的测试一并删除。仍描述 SOP 启动或技能目录的测试改为新路径。`test_task_runner_sop` 里禁止调用 `engines.ai.registry` 的补丁改为断言任务线程的导入图中没有 `engines.ai`。

5. **路径常量与排除规则同步改掉。** `skills_catalog.SHARED_SKILLS_DIR`、相关注释、`ruff.toml` 与 `tools/check_gates.py` 里指向 `engines/ai/skills` 的排除，改为不再引用已删除目录。`engines/__init__.py` 与 `config/settings.py` 里对旧引擎注册表的说明改成 SOP 是平台执行入口。

## 模块防火墙自检

- 不新增跨 App import。模型组装与技能目录仍在 `apps/ai_assistant` 内部。
- 不新增对其它 App 的 `service` / `runner` / `consumer` / `state_machine` 导入。`resolve_device_serial` 继续走现有的 `apps.device_pool.api`。
- 不新增写库路径。技能记录的写入仍经 `apps/ai_assistant/api.py`。
- 前端不直连数据库，仪表盘无写操作。

## Risks / Trade-offs

- [漏改导入，Django 或 SOP 启动时报 `ModuleNotFoundError`] → 实施结束时搜索 `engines.ai` 与 `engines/ai`，生产代码与测试中不得再有导入。
- [共享目录为空，工具箱在第一次上传前没有磁盘技能] → 与今天 `engines/ai/skills` 不存在时的行为一致；上传成功后文件出现在 `shared`。
- [只覆盖旧引擎的测试被删除后，提示词与规划契约不再有自动化守护] → 这些需求已在本变更的 delta 中收回。SOP 启动与技能目录另有测试。
- [回滚需要恢复整包] → 无数据库迁移。回滚用版本管理还原删除的文件与 `SHARED_SKILLS_DIR`。已上传到 `shared` 的技能目录保留，不自动搬回旧路径。
