## Why

`engines/agents/role/base.py` 里两个类名与本仓库既有命名口径不一致，读代码时要靠猜才能分清职责：

- `CreateModel` 是动词短语，而仓库其余类名都是名词短语（`ModelConfig` / `RoleConfig` / `ToolGroupSpec` / `RoleSpec` / `Gate` / `DeviceExecutionConfig`）。该类实际是按 provider 造一个 `ChatModelBase` 实例——它是工厂，不是「模型」本身。
- 同文件里的 `RoleSpec` 与 `ModelConfig` / `RoleConfig` / `DeviceExecutionConfig` 的「配置类以 `Config` 结尾」口径不一致。

本次只做改名，不改任何行为。

## What Changes

- **BREAKING**（仅限该脚手架包内部）：`engines/agents/role/base.py` 的类 `CreateModel` 改名为 `ChatModelFactory`。
- **BREAKING**（仅限该脚手架包内部）：`engines/agents/role/base.py` 的类 `RoleSpec` 改名为 `RoleSpecConfig`。
- 同步该文件内全部引用点：模块 docstring（第 3 行）与 `BaseRole.__init__` 里的构造调用（第 197 行）。
- 明确不动平台侧的 `engines/ai/agents/`：平台侧另有同名 `RoleSpec`，与 `CreateModel` 对应的实现是函数 `create_model`，本次一律不涉及。

## 关联文档

无关联需求编号。本次是纯改名（行为不变），不改变平台对外能力，因此不进入 `dev_docs/ARCH_PRD` 的 PRD / ARCH 编号体系。按 schema 约定，纯重构在 `.openspec.yaml` 设 `skip_specs: true`（与归档单 `2026-10-08-split-agent-roles` 同一处理方式）。

## Capabilities

### New Capabilities

无。本次不引入任何新能力。

### Modified Capabilities

无。类名不是可观察行为；行为不变，spec 就不应变。故按 schema 约定以 `.openspec.yaml` 的 `skip_specs: true` 显式退出 specs 阶段，不为通过校验而编造需求。

## Impact

- 代码：仅 `engines/agents/role/base.py`。该目录未被 git 跟踪，属独立实验脚手架，不在平台 PRD 范围。
- 引用面：全仓检索确认该文件之外**没有** `CreateModel` 或该 `RoleSpec` 的引用。
  - 其余 `CreateModel` 命中全部是 Django 迁移里的 `migrations.CreateModel(`（如 `apps/*/migrations/*.py`），与本次无关。
  - 平台侧 `engines/ai/agents/**` 的 `RoleSpec` 是同名但不同的类，本次不改。
  - `openspec/changes/archive/**` 里的历史记录提到旧名，属归档文本，不改。
- 平台侧零改动：`engines/ai/**`、`apps/**`、`frontend/**` 不动。`apps/ai_assistant/tools.py` 只从同包引 `engines/agents/tools/tool_serial.py`，不经过本次改名的两个类。
- 测试：`tests/graybox/unit/test_executor_tool_groups.py` 只 import `BaseRole, ModelConfig, RoleConfig`，不受影响；`tests/graybox/unit/test_agent_event_stream.py` 的 `RoleSpec` 来自 `engines.ai.agents`（平台侧），不受影响。
- 依赖：无新增。
