## Why

`engines/ai/AGENTS.md` 的代码规则要求「函数方法注释只写功能 / 入参 / 返回值，禁写设计旁白与"给谁看"」，但 `engines/ai/**/*.py` 里大量 docstring 写成了设计说明：变更编号引用、历史沿革（"改造前""旧链路"）、实现步骤（"A → B → C"）、消费者与边界讨论、取舍理由。注释与规则不一致，读者拿不到契约，还要读一堆与调用无关的旁白。

## What Changes

- 把 `engines/ai/**/*.py` 的模块 / 类 / 函数 docstring 全部收敛为「功能（1 句）」+ 必要的 `Args:` / `Returns:` / `Raises:`。
- 删除：设计理由与权衡、"为什么这样写"、历史沿革与变更编号、实现步骤、消费者说明、"给人看 / 不抛给模型"这类旁白、与调用方无关的内部细节。
- 保留调用方需要的契约：参数取值范围与单位、未命中 / 失败时的返回语义、异常约定、副作用（如"会产生设备副作用"）、文件与事件格式约定。
- 一并清理含旁白的行内注释（`#`）。
- **不动**任何代码逻辑，也不动字符串字面量：`tools/tool_device_catalog.py` 的工具说明书、`agents/config.py` 的提示词常量原样保留。

## 关联文档

- 约束来源：`engines/ai/AGENTS.md` §代码规则 1。
- 说明：纯注释整理，无需求级行为变化（按仓库惯例置 `skip_specs: true`）。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无：只改注释，调用契约与行为不变）

## Impact

- **引擎**：`engines/ai/**` 下 25 个 `.py` 文件（含工程内引用 `engines/ai/messaging/events.py`、`process_log.py`、`tools/tool_device.py`、`tools/tool_device_catalog.py`、`workflow/sop_step.py` 的注释部分）。
- **不改**：`engines/ai/skills/skill-creator/**`（`ruff.toml` 明确标注为 vendored 脚手架、不适用本项目 lint 规范）。
- **平台与前端**：无接口、无契约、无行为变化（AST 比对：剥离 docstring 后 36 个文件全部一致）。
- **注释量**：非 vendored 部分 docstring 654 行（原 703 行）；`>= 4 行` 的 docstring 由 75 处降到 65 处（剩余均为确实需要 `Args:` / `Returns:` 的）。
