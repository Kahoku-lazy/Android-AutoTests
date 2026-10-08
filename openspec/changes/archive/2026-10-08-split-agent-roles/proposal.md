# 智能体拆为「模型创建基类 + 三个继承角色」

## Why

智能体包归位后，三个角色仍然挤在同一个 651 行的文件里：模型连接创建、角色配方（`RoleSpec`）、角色基类（180 行的「装配 → 接受任务 → 执行 → 出报告」主干）、三个具体角色、装配工厂全在一处。加一个角色或改一个角色的配方，都要在这个大文件里翻找；「模型创建」与「角色行为」两件事也没有边界。

用户要求的结构是：先写一个 `base` 负责模型创建，再用继承的方式创建**步骤规划 / UI 执行 / 结果验收**三个角色。这同时把上一单确立的"五部分"在智能体包内部再分层一次。

## What Changes

- 智能体包按「1 个基类 + 3 个继承角色」重排：新增 `base.py`（模型连接创建 + 角色基类）、`planner.py`（步骤规划）、`executor.py`（UI 执行）、`verifier.py`（结果验收）。
- 装配工厂 `build_device_models` 移到**包入口** `__init__.py`（理由见 design.md D1：放进 `base.py` 会与三个子类形成循环导入；放包入口还让调用方 import 一行都不用改）。
- 删除 `engines/ai/agents/model.py`（内容全部有归属），**不做兼容转发**。
- 提示词与三份工具子集**留在 `config.py` 不动**（4 份主规格 + 前端模块约束 + 接口文档都引用该路径，保持零规格改动）。
- 引擎入口与后端**零改动**（公开导入面不变）。
- **BREAKING**（限仓库内部引用者）：**3 个**单元测试文件的 import 需同步——`test_ai_engine_config`（含一处 monkeypatch 目标字符串）、`test_ai_role_tool_subsets`，以及 `test_ai_model_debug` 中一处**函数内**的 `from engines.ai.agents import model as engine_model`。
- 零行为变化：只搬位置与切分文件，函数体与类体逐字保留。

## 关联文档

无关联需求编号：本单是纯内部结构重构（智能体包内再分层），不改变任何对外行为与验收口径，故不关联 PRD / ARCH 需求条目。承接上一单 `2026-10-08-split-ai-engine-into-five-parts`（引擎五部分分层）。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

无。角色类的公共 API（`AgentRole.ask/run/tool_results_seen/reset_context`、三个角色类的 `run()` 签名与 `RoleSpec` 字段）、提示词常量路径（`engines/ai/agents/config.py`）、装配工厂的公开导入路径（`engines.ai.agents.build_device_models`）全部保持不变。按 schema 约定，纯重构在 `.openspec.yaml` 设 `skip_specs: true`。

## Impact

- 引擎：`engines/ai/agents/` 由 2 个模块（`config.py` / `model.py`）变为 5 个（`config.py` / `base.py` / `planner.py` / `executor.py` / `verifier.py`）+ 包入口；`model.py` 删除。
- 测试：**3 个**单元测试文件的 import 与 1 处 monkeypatch 目标同步；**断言行零改动**。其中 `test_ai_model_debug` 的引用写在用例函数内（`from engines.ai.agents import model as engine_model`），只按 `agents.model` 点号形态检索会漏掉，故关单以"点号 + `import model as`"两种形态复扫。
- 后端 / 前端 / 数据库 / 通道：零改动（无接口、字段、迁移、端点变化）。
- 文档与规格：`config.py` 路径不变，主规格、前端模块约束、接口文档零改动。
