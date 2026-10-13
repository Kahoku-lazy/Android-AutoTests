## Context

见 `proposal.md` - Why。

现状（2026-10-13 实测）：

- `engines/agents/role/base.py`：458 行，含 `ModelConfig`(42-65)、`RoleSpecConfig`(67-89)、`ChatModelFactory`(93-155)、`RoleConfig`(157-187)、`BaseRole`(190-458)。
- `engines/agents/role/config.py`：54 行，已由用户复制进 `ModelConfig`(5-27) 与 `RoleSpecConfig`(30-52)；无模块 docstring；第 1 行 `from dataclasses import  dataclass` 有双空格。
- 引用方只有三处：`role/executor.py:8`、`agents.py:18`、`tests/graybox/unit/test_executor_tool_groups.py:15`；`messaging/messages.py:4` 只在 docstring 里提到 `engines.agents.role`，不是 import。
- `RoleSpecConfig` 全仓零引用（无任何实例化点）。

对位先例：平台侧 `engines/ai/agents/` 已是 `config.py`（数据 + 常量 + 提示词）+ `base.py`（角色基类）的分工，且 `ai/agents/base.py:44` 正是 `from .config import ModelConfig`。

## Goals / Non-Goals

- Goals：`role/base.py` 只剩角色基类与角色参数；三份「配置 + 工厂」在 `role/config.py` 一处；三处引用一次性改净，不留旧导入路径。
- Non-Goals：
  - 不保留 `base.py` 的再导出（不留第二个可导入位置）。
  - 不收敛 `prompt_config.py` 的重复 `ModelConfig` / `DeviceExecutionConfig`。
  - 不动 `RoleConfig`（角色参数与基类同层，本次不拆）。
  - 不改任何行为：provider 分支、`SecretStr` 归一化、字段顺序与默认值、`RoleConfig` 形参全不变。

## Decisions

**D1：三份一起搬（含工厂），不是只搬两个数据类。**
若只搬数据类、把 `ChatModelFactory` 留在 `base.py`，那么 `agentscope.credential`（三个凭证类）与 `agentscope.model`（四个模型类）的导入必须留在 `base.py` 为工厂服务 —— 角色基类文件仍然背着一整层模型创建细节，拆分收益减半。三份一起搬后，`base.py` 可以彻底摘掉 `agentscope.credential` / `agentscope.model` / `pydantic` 三处导入。

**D2：严格移动，`base.py` 不保留再导出。**
引用方只有 3 处、且都在可控范围内改净。保留再导出会让 `ModelConfig` 同时存在 `role.base.ModelConfig` 与 `role.config.ModelConfig` 两个可导入位置，形成"同名两个来源"的长期歧义；`RoleSpecConfig` 无人引用，再导出等于留一个没人用的转发模块，违背上一单归档时"不留转发模块"的既有处理（见归档单 `2026-10-12-move-sop-into-workflow` 的同类决策）。
备选：`base.py` 里 `from .config import *` 或显式再导出以兼容旧路径 —— 否决，理由如上。

**D3：`config.py` 的导入行双空格一并修正。**
本次必然要动该文件的 import 区（要新增 `agentscope` 两处导入），不修则这一行会继续违反 ruff format 口径，且它就在改动行旁边。

**D4：不收敛 `prompt_config.py` 的第三份 `ModelConfig`（按用户决定）。**
另立一单。理由：本次意图是"把 `base.py` 的三份搬到 `config.py`"，掺入第三份重复会让 diff 无法逐行追溯，也让验收标准无法单一化。

**D5：给 `config.py` 补模块 docstring。**
该文件目前没有文件头说明。新家需要一句"这里放什么"（与平台侧 `config.py` 的文件头 docstring 对位），否则下一个改动者无法判断新类该放哪。

**D6：`base.py` 的导入收敛以 ruff 为准，不凭肉眼删。**
删除三份定义后，`from dataclasses import ...`（第 40 行）、`from pydantic import SecretStr`、`from agentscope.credential import ...`、`from agentscope.model import (...)` 预期全部失效；但"预期"不是证据，逐个以 `python -m ruff check --no-cache` 的 `F401`（未使用导入）与 `F821`（未定义名）判定。这条同时清掉上一单记录的 `I001` 与 `F401`×3。

## Risks / Trade-offs

- [本会话无法执行任何真实运行验证] → 沙箱拒绝读 `site-packages/idna/__init__.py`，`pytest` 与 import 冒烟均不可用。缓解：会话内改用 ruff `--no-cache` + AST 静态校验（定义位置与导入绑定）+ 全仓检索 + 平台侧 git 指纹比对四项静态证据；**并把"必须真实运行"的 `pytest tests/graybox/unit/test_executor_tool_groups.py` 与两条导入冒烟单列为需用户在本机终端执行的任务**，未执行就不打勾。
- [误删 `base.py` 中仍被使用的导入] → 以 ruff 的 `F821` / `F401` 双项判据为准；`base.py` 仍有 `Toolkit`、`SkillLoaderBase`、`ContextConfig`、`ReActConfig`、`ConsoleRenderer` 等角色基类在用，只删被判为未使用的。
- [`RoleSpecConfig` 搬完后仍零引用] → 没有任何测试覆盖它，本次只能保证"定义存在且模块可解析"，其真实用途留给后续变更；这一点写进 tasks 供复核。
- [立项时误判测试文件已被跟踪] → 实测该文件在 `git status` 里是 `??`（未跟踪），本次变更**不产生任何 git diff**、也没有已跟踪文件被改动；记录已按实测更正。本次对该文件只改一行导入，不改断言。
- [与平台侧同名类混淆] → 脚手架 `role/config.py` 与平台 `ai/agents/config.py` 各有 `ModelConfig`，本次不合并两棵树；文档中已写明对位关系。

## Migration Plan

无部署动作：`role/base.py` 不在平台运行链路的 import 图上（`apps/` 只引同包 `tools/tool_serial.py`），搬移不影响任何运行中的服务，也不需要迁移指令。
回退策略：把三份定义搬回 `role/base.py`，恢复 `agentscope` / `pydantic` / `dataclasses` 三处导入，并把三处引用改回 `role.base`。

## Open Questions

- `engines/agents/prompt_config.py` 的第三份 `ModelConfig` 与无人引用的 `DeviceExecutionConfig` 该并到 `role/config.py` 还是删掉 —— 已知需另立一单，不影响本次范围与任务拆分。
- `RoleSpecConfig` 的用途（设计上由谁实例化）—— 可安全后置，不改变本次的搬移方案。
