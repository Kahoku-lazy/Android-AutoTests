## Why

`engines/agents/role/base.py` 一个文件里装了 5 个类，职责跨越四件事：模型连接数据（`ModelConfig`）、角色配方数据（`RoleSpecConfig`）、模型工厂（`ChatModelFactory`）、角色参数（`RoleConfig`）、角色基类（`BaseRole`）。加一个配置字段要在角色基类文件里翻找。

平台侧同构代码早已分开：`engines/ai/agents/config.py` 放数据与常量、`base.py` 放角色基类，且 `ai/agents/base.py` 是从 `from .config import ModelConfig` 取连接配置的。本次把脚手架对齐到同一分工：`role/config.py` 承接三份「配置 + 工厂」，`role/base.py` 只留角色基类与角色参数。

顺带收益：`base.py` 里那行游离的 `from dataclasses import ...`（第 40 行）随三份定义一起消失，上一单记录的 `I001` 与 `F401`×3 一并清零。

## What Changes

- **BREAKING**（仅限该脚手架包内部）：`engines/agents/role/base.py` 不再提供 `ModelConfig`、`RoleSpecConfig`、`ChatModelFactory`。三者迁至 `engines/agents/role/config.py`。
- `engines/agents/role/config.py`：接收 `ChatModelFactory` 及其依赖（`agentscope.credential` 三个凭证类、`agentscope.model` 四个模型类）；补模块 docstring；修正第 1 行 `from dataclasses import  dataclass` 的双空格。
- `engines/agents/role/base.py`：删除三份定义与随之失效的导入（第 40 行 `dataclasses`、`pydantic.SecretStr`、`agentscope.credential`、`agentscope.model` 的四个 `ChatModel` 名）；改为 `from .config import ChatModelFactory, ModelConfig`；更新模块 docstring。
- 同步引用方三处：`engines/agents/role/executor.py`、`engines/agents/agents.py`、`tests/graybox/unit/test_executor_tool_groups.py` 的 `ModelConfig` 导入改指向 `config`。
- **Non-goals**：不在 `base.py` 保留再导出；不收敛 `engines/agents/prompt_config.py` 里的第三份 `ModelConfig` 与无人引用的 `DeviceExecutionConfig`（按用户决定另立一单）；不动 `RoleConfig`。

## 关联文档

无关联需求编号。本次是纯搬移 + 改导入（行为不变），不改变平台对外能力，因此不进入 `dev_docs/ARCH_PRD` 的 PRD / ARCH 编号体系。按 schema 约定，纯重构在 `.openspec.yaml` 设 `skip_specs: true`。

## Capabilities

### New Capabilities

无。本次不引入任何新能力。

### Modified Capabilities

无。类住在哪个模块不是可观察行为；行为不变，spec 就不应变。故按 schema 约定以 `.openspec.yaml` 的 `skip_specs: true` 显式退出 specs 阶段。

## Impact

- 代码（4 个文件，均在 `engines/agents/`，该目录未被 git 跟踪，属独立实验脚手架、不在平台 PRD 范围）：
  - `engines/agents/role/config.py`（接收三份定义中的工厂）
  - `engines/agents/role/base.py`（删除三份定义、改导入与 docstring）
  - `engines/agents/role/executor.py`（`ModelConfig` 改从 `.config` 取）
  - `engines/agents/agents.py`（`ModelConfig` 改从 `.role.config` 取）
- 测试（**未被 git 跟踪**，实测 `git status --short` 显示 `??`，故本次变更不触碰任何已跟踪文件）：`tests/graybox/unit/test_executor_tool_groups.py` 的 `ModelConfig` 导入改指向 `engines.agents.role.config`。
- 平台侧零改动：`engines/ai/**`、`apps/**`、`frontend/**` 不动。`apps/ai_assistant/tools.py` 只从同包引 `engines/agents/tools/tool_serial.py`，不经过本次搬移的三个类。
- 依赖：无新增（`agentscope` 的凭证与模型类只是换了引用位置）。
- 验证能力受限：本会话沙箱拒绝读取 `site-packages/idna/__init__.py`，`pytest` 与任何 import 冒烟均不可执行（`pytest --collect-only` 亦然）。故本次把「必须真实运行」的验证单列为需用户在本机终端执行的任务，会话内只做静态等价验证。
