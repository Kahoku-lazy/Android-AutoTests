## Context

见 `proposal.md` - Why。AST 实测（`temps/report_module_docstrings.py`，扫描 `engines/agents/**`，排除 `skills/`）：

- **24 个模块**：**已套模板 2 个**（`role/base.py`、`role/config.py`）、**待改 22 个**。
- 其中 **`mcp_config/mcp_config.py` 的模块 docstring 为空**，且该文件**无法编译**：`py_compile` 与 `import` 均报 `SyntaxError: 'await' outside function`（内容是三段重复粘贴的 AgentScope MCP 示例，含硬编码 `Bearer xxx` 占位）；全仓**零引用**；归档单 `2026-10-10-executor-tool-groups` 的 design 已写明"不接 MCP，该文件保持现状"。
- **22 个模块里只有 `agents.py` 有 `__main__` 块** —— 但已套模板的两个模块（`role/base.py`、`role/config.py`）**也没有** `__main__`，照样带 `python -m 调试路径` 一行 → 这一行的定位是"复制即用的调试入口"，与是否可独立运行无关。
- `messaging/__init__.py` 的描述已过时：只写"对话稿记录包"，而该包现已包含消息解析、用量费用与上屏渲染。
- `prompts/` 下 5 个模块的 docstring 均为单行（如 `executor_prompt.py` 的"执行角色提示词。执行角色只此一份系统提示词。"）。

## Goals / Non-Goals

- Goals：22 个模块统一套用模块 docstring 模板（含新建 1 个、含 4 个 `__init__.py` 的包口径）、顺带修正 2 处过时表述，并用 AST 比对证明"只动 docstring"。
- Non-Goals：见 proposal 的 Non-goals。

## Decisions

**D1：模板统一套到 22 个模块，一个不留。**
规范已写明外形，留几个"特例"就会立刻重新漂移。完成后以"24/24 合规"为验收口径，可脚本校验。

**D2：`python -m 调试路径` 一行**不要求**模块可独立运行。**
依据现成先例：`role/base.py` 与 `role/config.py` 都没有 `__main__` 块，但都带这一行。它的价值是"给人一个可直接复制执行的调试入口"。**否决**"只给 `agents.py` 加"的方案 —— 那会让模板出现两种外形，与 D1 冲突。

**D3：4 个 `__init__.py` 的"业务功能"写包的职责 + 导出面，不写函数清单。**
包入口没有独立业务功能，硬凑函数清单会与 `__init__.py` 的实际作用（再导出）不符。写法示例：
```
本模块的业务功能如下：
1. 包导出面: 对话稿 `DialogueLog`、消息与工具输出解析、用量费用与上屏渲染。
```

**D4：顺带修正内容过时的描述（不额外扩范围）。**
模板本身要求写"本模块的业务功能如下"，所以内容必须重写，过时描述自然被覆盖。已知两处：`messaging/__init__.py`（漏了 `messages.py` 的三类功能）、`tools_config.py`（"改下面的名字表即可"→ 正式表述）。

**D5：排除 `mcp_config/mcp_config.py`（不套模板、不改、不删）。**
三条证据：①`py_compile` / `import` 均失败（`SyntaxError: 'await' outside function`）；②全仓零引用；③归档单 `2026-10-10-executor-tool-groups` 已决定"保持现状"。
给它写 `python -m 调试路径: engines.agents.mcp_config.mcp_config` 会是**误导**（照着跑必然报错），而"修好它"属于改代码，超出本单 Non-goal；"删掉它"是独立决策（见 Open Questions）。故本单范围从 22 收到 **21**，验收口径改为 **23/24 合规**，并把该文件作为**已知例外**登记。**用户已决定：保持现状**（不删、不改、不另立单）。

**D6：用"剥离 docstring 的 AST 比对"证明零代码改动。**
校验脚本对 22 个文件逐个：`git show HEAD:<path>` 取出改动前版本 → 解析 AST → 剥掉所有 docstring 节点 → 与当前文件的同口径 AST 做 `ast.dump` 比对，必须逐字相等。这比"人眼看 diff"强得多，也是本单唯一的硬保证。

**D7：以 `skip_specs: true` 退出 specs 阶段。**
纯 docstring。

## Risks / Trade-offs

- [误改代码或提示词正文] → D6 的 AST 比对；另外单独断言 `prompts/*.py` 里所有字符串常量的**取值逐字未变**（防止手滑改到提示词文案）。
- [提示词正文被读取为模块 docstring] → 核查全仓是否有 `__doc__` 消费点（`rg "\.__doc__|getdoc|inspect\.getdoc"`）；若有则先确认再动 `prompts/`。
- [`mcp_config.py` 的例外被遗忘] → 校验脚本把"该文件仍不可编译"写成**显式断言**（而非只写在文档里），一旦有人顺手改好或删掉，脚本会报出来提醒同步文档。
- [diff 大、review 费力] → 22 个文件的改动**只**集中在文件头 docstring，且分组提交（按目录 5 组任务），逐组验证。
- [lint/format 回归] → 每组跑 `ruff check --force-exclude` + `ruff format --check`。
- [首行摘要语义] → 模块 docstring 的**首行**不是模型可见内容（只有**工具函数**的 docstring 首行才是），但仍是人读的第一印象，要求每行都写清职责、不写"本模块用于…"这类废话。

## Migration Plan

无部署动作、无迁移。回退：`git checkout -- <path>` 即可逐个还原。

## Open Questions

- ~~**`mcp_config/mcp_config.py` 怎么处置**~~ → **已定（用户决定）：保持现状。** 不删、不改、不套模板，也**不另立单**；它作为**已知例外**留在 `engines/agents` 下（不可编译、零引用）。本单的守卫断言（tasks 3.1 ⑤）会持续提示它的状态变化，避免将来有人"顺手改好"却没人同步文档。
- `prompts/` 这类"正文即数据"的模块是否真的需要调试入口行 —— 按 D2 一律保留；若后续认为噪音，可另立一单放宽。
- 是否要求"业务功能清单"里的条目与 `__all__` 一一对应 —— 本次不强制（`__init__.py` 尤其不适用）。
