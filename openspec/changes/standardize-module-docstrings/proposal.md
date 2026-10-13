## Why

`standardize-raises-docstrings` 把**两套注释模板**写进了 `engines/agents/AGNETS.md`（模块 docstring 与方法 docstring），但当时只落到 `role/base.py`、`role/config.py` 两个文件。AST 实测（`temps/report_module_docstrings.py`）：该包 **24 个模块里只有 2 个**套用了模块 docstring 模板，**22 个没有** —— 其中 21 个是随手一句话（如 `tools_config.py` 的"改下面的名字表即可"），既缺"调试路径"入口，也缺"本模块的业务功能"清单；剩下 1 个（`mcp_config/mcp_config.py`）**连模块 docstring 都没有，而且无法编译**（详见 What Changes 的排除说明）。

这是本会话最后一处**"规范已生效、代码未跟进"**：`AGNETS.md` 要求模块 docstring 采用统一外形，而 92% 的模块不符合。

## What Changes

- 按 `AGNETS.md` 的**模块 docstring 模板**改写 **21 个模块**的 docstring：
  ```python
  """
  python -m 调试路径: engines.agents.<子包>.<模块>

  本模块的业务功能如下：
  1. <类或功能名>: <一句话说明>。
  """
  ```
  覆盖：根目录 4 个（`agents.py` / `billing.py` / `prompt_config.py` / `tools_config.py`）、`role/` 1 个（`executor.py`）、`messaging/` 3 个、`prompts/` 5 个、`tools/` 4 个、`workflow/` 4 个。
- **排除 `mcp_config/mcp_config.py`**（不套模板）：实测 `py_compile` 与 `import` **均失败**（`SyntaxError: 'await' outside function` —— 该文件是**三段重复粘贴的 AgentScope MCP 示例**，含硬编码 `Bearer xxx` 占位），全仓**零引用**，且归档单 `2026-10-10-executor-tool-groups` 的 design 已明确决定"不接 MCP，该文件保持现状"。给它写"调试路径"入口会是**误导**（照着跑必然报错），故本单不碰它。
- 4 个 `__init__.py`（`messaging` / `prompts` / `tools` / `workflow`）的"业务功能"写**包的职责与导出面**，不写函数清单。
- 顺带修正 2 处**内容过时/随意**的描述：`messaging/__init__.py` 现在只提"对话稿"（漏了 `messages.py` 的解析、用量费用与上屏）；`tools_config.py` 的"改下面的名字表即可"改为正式表述。
- **Non-goals（本次不做）**：
  - **不改任何代码**：函数体、类定义、常量、`raise`、import 一律逐字不动（校验脚本以 AST 比对证明）。
  - **不动 `prompts/*.py` 里的提示词正文**（只改模块 docstring）。
  - 不改方法 docstring（`Raises:` 等已在 `cleanup-agents-scaffold` 单完成）。
  - 不动 `engines/ai/**` 与平台侧、不动 `AGNETS.md` 本体。
  - 不给 `skills/` 供应商脚手架套模板（已在 `ruff.toml` 排除，且属供应商产物）。
  - **不动 `mcp_config/mcp_config.py`**（不可编译的示例残留）：**用户已决定"保持现状"** —— 不删、不改、不套模板、不另立单。

## 关联文档

无关联需求编号。本次是脚手架包的 docstring 外形统一，不改任何可观察行为（AST 比对为证），故不进入项目的 PRD / ARCH 编号体系。按 schema 约定设 `skip_specs: true`。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

无。纯 docstring 改动。以 `skip_specs: true` 退出 specs 阶段。

## Impact

- `engines/agents/**` 的 **21 个** `.py`（均已被 git 跟踪）。
- 平台侧零改动：`engines/ai/**`、`apps/**`、`frontend/**` 不动。
- 行为风险：无（不改一行代码；校验脚本用"剥离 docstring 后的 AST 与 `HEAD` 版本逐字比对"证明）。
- 收尾效果：完成后该包 **23/24** 模块符合模板（唯一例外 `mcp_config/mcp_config.py`，已登记理由），"规范与代码不一致"清零。
