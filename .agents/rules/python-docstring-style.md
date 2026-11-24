# 代码注释规范 — 全仓（2026-11-24 起：不写注释）

> **层级**：根 [AGENTS.md](../../AGENTS.md) → **本文件（唯一正文）** → 子系统追加条款（如 [`.agents/rules/engines-code-style.md`](engines-code-style.md) §6）
> **本文件是全仓注释规则的唯一真相源**。自动化检查：[`.agents/skills/engines-docstring-check/`](../skills/engines-docstring-check/SKILL.md)（技能名沿用历史）。

## 1. 总则

1. **不写注释**：模块 docstring、类 docstring、普通函数 / 方法 docstring、函数体内的 `#` 行内注释，一律不写。
2. **唯一例外——工具函数 docstring**：被 `FunctionTool(...)` 注册、把说明交给模型的函数（`engines/ae_harness/tools/**`，以及 `engines/ae_harness/knowledge/tool.py` 的 `search_knowledge`）**必须**写「首行一句话摘要 + `Args:`」，每个参数一行。
   AgentScope 取首行作工具 `description`、取 `Args:` 作参数说明 —— 这里的 docstring 是**运行时输入**，不是注释债务，删了等于把工具说明从模型上下文里抹掉。细则见 [`.agents/rules/engines-code-style.md`](engines-code-style.md) §6。
3. **保留工具链指令**：`# noqa`、`# type: ignore`、`# pragma: no cover`、shebang、编码声明等写给工具链的注释**必须保留**；`silent-except` 门禁要求的痕迹统一写成 `# silent-except` 标记。
4. **唯一的运行时 docstring（非工具）**：`tests/**/e2e/**` 里 `test_*` 函数的 docstring —— `tests/e2e/conftest.py` 取它作 e2e 报告标题，属运行时输入。
5. **职责写进文档**：模块职责、能力清单、字段枚举、`python -m` 调试入口不写进代码，写进 `.agents/docs/<module>/**` 与对应 `AGENTS.md`。

## 2. 检查

命令不变（在技能目录下运行）：

```text
cd .agents/skills/engines-docstring-check
python -m scripts.docstrings check            # 默认：只查本次 git 改动
python -m scripts.docstrings check --all      # 全仓在册文件全量审计
python -m scripts.docstrings read --changed   # 读代码前取签名与结构（代码里已无注释）
```

- 现在只校验**工具函数 docstring**（首行摘要、`Args:` 覆盖参数）。
- 模块头规则仅对**仍保留模块头**的存量文件生效；缺模块头不再报错，`engines/ae_harness/tools/**` 豁免模块级校验。
- 全仓 `python-module-docstring` 门禁已移除；engines 风格门禁为 `python -m utils.check_gates --only engines-agents-style`（tool 命名 / 禁 django·apps import）。

## 3. 常见误写

| 误写 | 后果 |
| --- | --- |
| 给工具函数只写 `Args:` 不写首行摘要 | `工具 docstring 应以一句话摘要开头` |
| 工具函数有参数却漏列 `Args:` 条目 | `缺 Args: 段` / `漏列参数名` |
| 为了让 `silent-except` 过检写解释性注释 | 违反「不写注释」；应写 `# silent-except` 标记 |

## 4. 修订说明

- **2026-11-24**：全仓移除注释与 docstring（含此前的 4 字段模块头模板）；只保留工具函数 docstring 与工具链指令；检查器移除模块头要求。
- **2026-11-24（前序）**：4 字段模块头推广到全仓；本次一并废止。变更单：`openspec/changes/repo-wide-python-docstring`。
