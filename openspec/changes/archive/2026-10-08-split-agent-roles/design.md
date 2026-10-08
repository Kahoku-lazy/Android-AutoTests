# 设计：智能体拆为「模型创建基类 + 三个继承角色」

## Context

- 上一单（`2026-10-08-split-ai-engine-into-five-parts`）已把引擎按五部分分层，智能体包（`engines/ai/agents/`）现为 `config.py`（208 行：提示词 + 工具子集 + 模型/引擎配置）+ `model.py`（651 行）+ 包入口。
- `model.py` 现在装五件事：`RoleSpec` 角色配方、provider 兼容常量、`create_model` 模型连接创建、`AgentRole` 角色基类（180 行主干）、`PlannerRole` / `ExecutorRole` / `VerifierRole` 三个子类、`build_device_models` 装配工厂。
- 三角色**已是继承结构**（都继承 `AgentRole`），本单是把「基类 + 模型创建」独立成 `base`、三个子类各占一个文件。
- 约束 1：提示词常量路径 `engines/ai/agents/config.py` 被 4 份主规格 + 前端模块约束 + 接口文档引用 → 保持不动即零规格改动。
- 约束 2：公开导入面必须稳定——`from engines.ai.agents import DeviceExecutionConfig, ModelConfig, build_device_models` 现被引擎入口与后端使用；`from engines.ai.agents import <角色类/规格/配置>` 被模型调试台使用。
- 约束 3：本单零行为变化，验收复用上一单的验收集（搬迁前基线 164 项）。

## Goals / Non-Goals

**Goals:**

- 智能体包内实现「base（模型创建 + 角色基类）+ 三个继承角色」的结构，一个角色一个文件。
- 保持公开导入面与角色类 API 不变：引擎入口、后端、调试台**零改动**。
- 保持零规格改动、零行为变化。

**Non-Goals:**

- 不改任何行为：类体与函数体逐字保留，日志文案、结果字段、提示词、工具子集、ReAct/上下文参数一律不动。
- 不搬提示词与工具子集出 `config.py`（那会牵动 4 份主规格 + 前端约束 + 接口文档）。
- 不引入新抽象（不加模板方法、不加注册表、不加角色基类的第二个层次）；三角色继续各自实现 `run()`。
- 不改五部分布局与依赖方向（agents 仍是 `messaging` / `tools` / `billing` 的使用方）。

## Decisions

**D1 装配工厂放包入口 `__init__.py`，不放 `base.py`。**

工厂要构造三个角色类，而三个角色类要继承 `base`。若工厂写在 `base.py`，就形成 `base → planner/executor/verifier → base` 的循环导入。放包入口既避开循环（`__init__` 是包导入链的终点），又让 `from engines.ai.agents import build_device_models` 这一行**在引擎入口与后端里原样成立**——调用方零改动。
备选：工厂单立 `factory.py` —— 可行，但多一个文件且公开路径从"包入口"降级为"子模块"，调用方反而要改 import；否决。

**D2 提示词与工具子集留在 `config.py`。**

四份主规格、前端模块约束、接口文档都写死了 `engines/ai/agents/config.py` 是提示词唯一真相源。留在原处 = 零规格改动（与上一单同一取舍）。角色文件改为从 `config` 取自己的提示词与工具子集，读起来仍是"这个角色用哪套提示词与工具"一目了然。
备选：提示词随角色文件走（更内聚）——要同步改 4 份主规格 + 前端约束 + 接口文档，属规格级变更，收益不抵改动面；用户已明确选择留在 `config.py`。

**D3 `model.py` 删除，不留兼容转发。**

转发模块会让同一批符号存在两处入口，正是上一单明确拒绝的模式（"不留兼容转发，避免两处真相源"）。引用者只有 2 个测试文件，直接改 import 成本更低。

**D4 文件与符号命名。**

`base.py` / `planner.py` / `executor.py` / `verifier.py`；类名保持 `AgentRole` / `PlannerRole` / `ExecutorRole` / `VerifierRole` 不变（对外零影响）。
`_force_keep_local_screenshot` 随 `VerifierRole` 一起进 `verifier.py`（只被它使用）。

**D5 同名消歧：`engines/ai/base.py` 与 `engines/ai/agents/base.py`。**

两处都叫 base、层级不同：前者是引擎协议（`AiEngine` / `TaskRequest` / `TaskResult`），后者是智能体包的模型创建与角色基类。两个文件头各写明自身定位与"不是哪一个"，避免误读。

**D6 `base.py` 的职责边界。**

`base.py` = provider 兼容常量 + `create_model`（按 provider 建连接）+ `RoleSpec`（角色配方）+ `AgentRole`（角色基类主干）。
它从 `config` 只取 `ModelConfig` 做类型；三个角色的提示词与工具子集由各自文件从 `config` 取——`base` 不认识任何具体角色。

## 模块防火墙自检

- 跨 App import：无新增（本单只在引擎内部切分文件；引擎仍零 `apps.*` 依赖）。
- 写库路径：零写库改动，无迁移、无 ORM 变更、无新端点。
- 前端：零改动。
- 引擎边界：依赖方向不变（`agents → messaging / tools / billing`），且包内新增的 `base ← planner/executor/verifier` 是单向继承依赖，不引入回指。
- 公开面：`engines.ai.agents` 的导出集合不变（`build_device_models`、三个角色类、`RoleSpec`、`AgentRole`、`ModelConfig`、`DeviceExecutionConfig`、三份提示词与工具子集）。

## Risks / Trade-offs

- [`base` 与三个角色之间成环] → 工厂放包入口（D1）；搬迁后以 AST 建图做一次环检测，并做真导入核验（`get_ai_engine("agentscope")`）。
- [漏改引用导致运行期 `ImportError`] → 引用检索 MUST 同时覆盖两种形态：`engines.ai.agents.model`（点号）与 `from engines.ai.agents import model`（`import` 形态）。**实测教训**：本单首轮只按点号形态检索，漏掉 `test_ai_model_debug` 用例函数内的一处 `from engines.ai.agents import model as engine_model`，验收阶段才由测试暴露（该处同时是 monkeypatch 目标，必须改到 `base`——`_assemble` 从 `base` 的模块全局解析 `build_toolkit`）。
- [切分时无意识改到行为] → 逐字搬迁：类体/函数体不动，只改 import 与文件头 docstring；以 `git diff -M` 核对 `model.py` 的每一段只经历"移动"。
- [公开导入面被破坏] → 关单前逐项核验 `engines.ai.agents` 的导出集合与上一单一致（角色类、规格、工厂、配置、提示词、工具子集）。
- [同名 base 引起误读] → D5 的两个文件头消歧说明。

## Migration Plan

1. 新建 `base.py` / `planner.py` / `executor.py` / `verifier.py`，内容自 `model.py` 逐字搬迁并调整 import。
2. 重写包入口 `__init__.py`（公开导出 + 装配工厂），删除 `model.py`。
3. 同步 2 个测试文件的 import 与 monkeypatch 目标。
4. 验收：环检测、真导入、验收集（基线 164 项）、ruff、`manage.py check`、边界检查、旧路径零命中。
5. 回滚策略：纯代码移动、无数据库与契约变更，`git revert` 单次提交即可完整回退。
