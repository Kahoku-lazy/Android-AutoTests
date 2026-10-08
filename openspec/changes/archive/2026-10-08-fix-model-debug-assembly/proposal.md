# 修复：模型调试台 / model_test 的三角色装配（未定义名）

## Why

`python manage.py model_test <planner|executor|verifier|full>` 与网页「工具箱 → 模型调试」的**对话**入口共用同一个装配函数 `build_device_models_for_agent`；该函数调用 `build_device_models`，但这个名字**从未被导入**——一调用就抛 `NameError`。**四个阶段与调试对话全部不可用**（调试页只读配置仍能打开，因为那条路径不装配）。

这是**既有回归**，与本仓库最近两次引擎结构拆分无关：调用自功能上线（`59a99dac`）就在且当时 import 正确；删除 import 的是 `f823a6a7`（「提示词收回引擎并下线提示词管理面」）。工作区在两次拆分前的版本（`43756da0`）已缺该 import。

**为什么没人拦住**：仓库 `ruff.toml` 的 `select` 是一份窄白名单（`I` / `F401` / `F403` / `F405` / `E722` / `T201` / `Q`），**不含未定义名检查（F821）**；而已有的调试台用例把这个装配函数**整个 mock 掉**，真实入口从未被执行。两道防线同时失效。

## What Changes

- 修复 `apps/ai_assistant/model_debug.py`：把 `build_device_models` 加回引擎包级导入（本就是包入口公开导出）。
- **开启 `F821`（未定义名）到 `ruff.toml` 的 `select`**：实测全仓该规则存量**恰为 1 处**（即本 bug），修完即零存量；此后"用了没导入的名字"这类缺陷在门禁处即被拦住，不再依赖人来发现。
- 新增回归用例 `tests/graybox/unit/test_ai_debug_assembly_entry.py`：**不打桩被测函数本身**，用桩 agent 调真实装配入口，断言产出「1 份三角色配置 + 3 个角色对象」且角色类与配方正确（只对密钥解密与技能目录两处外部依赖打桩）。
- 零行为变更：除上述缺陷修复外不改任何行为；提示词、工具子集、工作流、接口契约均不动。

## 关联文档

- 受影响能力：`ai-model-debug`（其既有要求「调试对话按该角色真实装配运行」被本缺陷违反，修复即回归该要求，规格正文无需改动）。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

无。本修复让代码**回到** `ai-model-debug` 既有要求的状态（该要求原文已规定调试对话必须按真实装配运行），不改变任何对外行为与验收口径，故按 schema 约定在 `.openspec.yaml` 设 `skip_specs: true`。

## Impact

- 后端：`apps/ai_assistant/model_debug.py`（一行 import）；`ruff.toml`（`select` 增加 `F821`）。
- 测试：新增 1 个单元测试文件（2 条用例：真实装配成功 + 三角色配方正确）。
- 恢复的能力：`python manage.py model_test planner|executor|verifier|full` 四阶段、网页模型调试台对话。
- 前端 / 数据库 / 通道 / 规格：零改动。
