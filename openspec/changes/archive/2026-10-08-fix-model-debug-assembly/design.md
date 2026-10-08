# 设计：修复模型调试台 / model_test 的三角色装配

## Context

- 缺陷事实（提交级已核实）：`apps/ai_assistant/model_debug.py:120` 调用 `build_device_models`，但该名字不在任何 import 中。调用点自 `59a99dac` 引入时就存在（当时从 `engines.ai.agentscope.model` 正确导入）；`f823a6a7` 删除了该 import（同批把 `agentscope/` 目录改名为 `agents/`），此后该名字悬空。两次引擎结构拆分（`b84598af` / `ba2979b3`）之前的版本 `43756da0` 已缺该 import —— **缺陷先于拆分存在，拆分按"零行为变化"把它原样保留**。
- 影响面：`model_test` 的 planner / executor / verifier / full **四阶段**都先走该装配函数，故全部失败；网页调试台的 `POST /api/ai/model-debug/<role>/chat`（`run_role_chat`）同样先走它，故对话 500。只读配置接口 `GET /api/ai/model-debug/<role>/` 不触发装配，页面能打开。
- 两道防线为何失效：① `ruff.toml` 的 `[lint] select` 为窄白名单，**不含 F821（未定义名）**；② `tests/graybox/unit/test_ai_model_debug.py:216` 与 `test_ai_debug_log_check.py:149` 都把 `build_device_models_for_agent` **整个打桩**，真实装配函数从未被真实调用。
- 存量实测：`ruff check --select F821 .` 全仓**恰 1 处**（即本缺陷）。

## Goals / Non-Goals

**Goals:**

- 恢复两个入口（`model_test` 四阶段、调试台对话）。
- 让"用了没导入的名字"这类缺陷在门禁处被机械拦住，而不是靠人发现。
- 补一条**真实走装配**的回归用例（不再整体打桩），守住"三角色装配产出"这一行为。

**Non-Goals:**

- 不改调试台与 `model_test` 的任何对外行为、参数、文案与超时口径。
- 不改提示词、工具子集、工作流、引擎结构（两次拆分的成果不动）。
- 不扩大 lint 规则面（只加 F821 一条，且已实测零额外存量）；不做全仓 lint 规则重估。
- 不为"mock 掉了真实入口"的既有用例做全面改造（仅新增真实入口用例）。

## Decisions

**D1 修的一行从引擎包入口导入，不从子模块导入。**

`build_device_models` 是智能体包的公开导出（上一单 `2026-10-08-split-ai-engine-into-five-parts` 的 D9 确立"上层只经包级入口"），故写 `from engines.ai.agents import build_device_models`，与同文件其余引擎导入同风格。

**D2 开启 F821，而不是只写一条用例。**

`ruff check --select F821 .` 实测：修复前全仓**恰 1 处**命中（就是本缺陷），修复后**零命中**——即"零成本、可机械验证"的守门，远强于靠人写用例穷举。写入 `ruff.toml` 的 `[lint] select`，随既有 lint 步骤生效。
**范围说明（实测）**：仓库门禁的 ruff 范围是 `apps/ config/ gateway/ shared/ models/` + `engines/`（`tools/check_gates.py` 的 `PY_SCOPES` 与 engines 专项），`ruff check .` 另有 31 处**门禁范围之外**的既有告警（T201 / I001 / F401 / Q 系列，分布在 tests/ 等路径），与本单无关、也未被本单新增；本单只保证「门禁范围全绿」+「F821 全仓零命中」。
备选：只补手写用例 —— 只能守住这一条路径，同类缺陷（任意模块漏 import）仍会漏过；否决。

**D3 回归用例不打桩被测函数。**

调用真实 `build_device_models_for_agent`，只对两处**外部依赖**打桩：密钥解密（`decrypt_key`，避免依赖加密格式）与技能目录扫描（`list_enabled_skill_dirs`，避免磁盘/DB）。断言返回「1 份 `DeviceExecutionConfig` + 三个角色对象」且角色类、`spec.role` 与视觉标记正确。这样一旦装配链任何一环名字悬空或签名漂移，用例即失败。
备选：source 级断言（如"模块命名空间里有 build_device_models"）—— 更脆且不覆盖真实调用链；否决。

**D4 用例只覆盖"装配成功"，不覆盖真实模型调用。**

用例不打桩角色类的 `run()`，也不发网络请求——只构造角色对象（`create_model` 只建客户端对象，无 I/O）。真实跑一次由 tasks 的真机/真模型冒烟步骤承担（本单即复用用户要求的 `model_test planner` 实跑）。

## 模块防火墙自检

- 跨 App import：`model_debug.py` 新增的是引擎包导入（apps → engines，既有方向），无新增跨模块依赖。
- 写库路径：零写库改动（调试对话本就不落库）；无迁移。
- 前端：零改动。
- 引擎边界：从引擎**包级入口**导入公开导出，不深引用内部模块；引擎仍零 `apps.*` 依赖。

## Risks / Trade-offs

- [开启 F821 后全仓变红] → 已实测：F821 全仓命中恰 1 处（本缺陷），修复后 `ruff check --select F821 .` 为 **All checks passed**；门禁范围 `ruff check apps/ config/ gateway/ shared/ models/ engines/` 全绿（187 文件格式检查亦通过）。关单时复跑这两条命令取证。
- [用例依赖真实外部装配，易碎] → 只对解密与技能目录打桩，其余走真实路径；用桩 agent（`route_configs` / `max_loops` / `owner_id` / `enable_skills`），不发网络、不碰设备。
- [只修 import 而掩盖同类隐患] → F821 打开即为该类隐患的机械防线；关单时附"全仓 F821 零命中"证据。
- [真机冒烟仍依赖设备与密钥] → 本单的实跑选在**规划角色**（不需要设备）；执行/验收阶段是否实跑由用户决定，未获授权则在汇报中显式标注未跑。

## Migration Plan

1. 修 `model_debug.py` 的 import；在 `ruff.toml` 的 `select` 增加 `F821`。
2. 新增回归用例并跑通。
3. 验证：`ruff check .`（含 F821）零命中、相关用例全绿、`manage.py check`、边界检查；随后实跑 `model_test planner`。
4. 回滚策略：纯代码/配置改动、无数据变更，`git revert` 单次提交即可回退。
