## Context

- 规则（`engines/ai/AGENTS.md`）：函数方法注释只写功能 / 入参 / 返回值。
- 现状：`engines/ai` 非 vendored 部分有 75 处 `>= 4 行` 的 docstring，多数是设计说明而非契约。
- 范围外：`engines/ai/skills/skill-creator/**`（`ruff.toml` 列为 vendored 脚手架）。

## Goals / Non-Goals

**Goals:**

- 全部 docstring 收敛到同一口径：模块 1–3 行职责；类 1 句职责（必要时列关键属性）；函数 1 句功能 + `Args:` / `Returns:`。
- 精简后的注释仍是可用契约：参数取值范围、失败 / 未命中语义、异常、副作用、文件与事件格式都留着。
- 零代码逻辑变化。

**Non-Goals:**

- 不改任何代码逻辑、符号名、字符串字面量。
- 不改工具说明书（`tools/tool_device_catalog.py` 的 `description`）与提示词常量（`agents/config.py` 的 `*_PROMPT` 等），它们面向模型。
- 不改 `engines/ai/skills/skill-creator/**`（vendored）与测试文件。

## Decisions

**D1 口径统一为「功能 / 入参 / 返回值」，不保留模块内的设计说明段。**

理由：规则就是这么要求的；设计理由应落在 OpenSpec 变更文档（本单）里，而不是长期留在源码注释里随实现漂移。

**D2 契约与旁白的判定线：调用方是否需要它来做决定。**

保留：参数取值范围与单位、失败 / 未命中的返回语义、异常约定、副作用、落盘路径与事件名格式、跨模块必须同步的常量（价目表、模型目录）。
删除：变更编号与历史沿革、实现步骤、消费者与读者说明、取舍理由、框架内部行为解释。

**D3 不改 vendored 脚手架。**

理由：`ruff.toml` 已把 `engines/ai/skills/skill-creator/**` 标为供应商产物、"改了会在下次 skill 更新时丢失"；改它既不在 lint 范围内，也会被覆盖。

## 模块防火墙自检

- 改动行 100% 落在 docstring 与 `#` 注释；AST 比对（剥离 docstring 与属性文档）36 个文件全部一致。
- 无新增 import、无跨 App 依赖、无写库、前端不涉及。

## Risks / Trade-offs

- [删过头，丢掉调用方需要的契约] → 逐条按 D2 判定线复核；`Args:` / `Returns:` / `Raises:` 段一律保留或补全，并在最终回复里列出"为契约而保留"的位置。
- [改到字符串字面量导致提示词 / 工具说明书变化] → AST 比对 + `tests/graybox/unit` 的 AI 相关用例（工具说明书、提示词契约、模型目录对拍）全绿。
- [ruff 的 D 规则被启用后反向要求补文档] → 本次以 `ruff check` / `ruff format --check` 现状为准，不引入新规则。

## Migration Plan

1. 备份 `engines/ai` 供 AST 与统计对拍（`temps/before_ai`）。
2. 自下而上改写：引擎协议层 → 智能体包 → 消息与计费 → 工具 → 工作流。
3. `ruff format` + `ruff check` + 定向 `pytest`。
4. 自查：AST 等价、`>= 4 行` docstring 统计、旁白关键词扫描。
5. 归档由仓库维护者执行（本单不移动目录）。
