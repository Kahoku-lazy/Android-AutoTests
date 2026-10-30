---
name: engines-agents-style-check
description: >-
  Use whenever checking engines/ style in Android-AutoTests, after editing engines/,
  fixing docstring/Raises/tool naming, or before claiming style is clean —
  always run this project AST checker and report only what it covers. When to load
  this skill is directed by engines/AGENTS.md. Prose source of truth is
  .agents/rules/engines-code-style.md. Project-local skill for this repo's engines/
  only; do not treat as a shared global skill.
---

# engines 风格检查（本仓库 · 实事求是）

本技能属于 **Android-AutoTests** 仓库（`.agents/skills/engines-agents-style-check/`），只服务本项目的 `engines/` 模块；不要放到助手共享技能库，也不要当成全局通用技能。

## 规范与流程入口（勿混淆）

| 文档 | 作用 |
|------|------|
| [`engines/AGENTS.md`](../../../engines/AGENTS.md) | **必读流程**：何时读规范、何时用本技能（职责 / 红线 / AI 阅读与检查流程） |
| [`.agents/rules/engines-code-style.md`](../../rules/engines-code-style.md) | **风格正文 source of truth**（docstring / Raises / SRP / agents 专规等散文） |

本技能**不**承载完整风格散文；`engines/AGENTS.md` 也不再堆放全文。检查器只覆盖正文里**能机械化**的子集。

## 何时使用本技能

按 [`engines/AGENTS.md`](../../../engines/AGENTS.md)「AI 阅读与检查流程」第 4 步：在下列情况**必须**阅读并按步骤执行，不要只靠口头对照规范正文：

- 改动了 `engines/` 下任意 Python（含 `agents` / `device` / `uart_log` / `vision`）之后的自检
- 用户要求检查是否符合规范、补 docstring / Raises、或「跑一下风格检查」
- 准备宣称「已符合规范 / Raises 已对齐 / 工具命名没问题」之前
- PR 或本地门禁里看到 `engines-agents-style` 告警，需要解释含义或复现

**不要**在无关目录（纯 frontend、纯 backend apps）上无故全量跑，除非用户明确要求。  
只读分析 / 不改 `engines/**` 代码时，通常不必加载本技能（仍以 `engines/AGENTS.md` 为准）。

## 先对齐预期（对用户和自己都说实话）

本检查器是 **AST 静态扫描**，只覆盖 [`.agents/rules/engines-code-style.md`](../../rules/engines-code-style.md) 里**能机械化**的子集。

### 它能校验什么

| 规则 id（输出里可见） | 含义 |
|---|---|
| `module-docstring` | 模块是否有文件头 docstring（部分空壳 `__init__.py` 可跳过） |
| `raises-doc` | 函数/方法体内有显式 `raise Xxx(...)` 时，docstring 是否有 `Raises:` 且写到该异常类型名 |
| `tool-naming` | `engines/agents/tools/` 下除 `__init__.py` 外是否均为 `tool_*.py` |
| `tool-doc-order` | 仅 `tool_*.py`：若有 `Raises:`，须在 `Returns:` 之后，且不得插在摘要与 `Args:` 之间 |
| `no-django-apps-import` | `engines/**` **模块顶层**不得 `import django` / `apps` / `backend.apps`（函数内可选探测除外；对齐 OpenSpec `agent-harness`） |

### 它不能校验什么（禁止夸大）

- 「一域一文件」、单一职责、模块低耦合
- 类型注解是否完整、业务对错、该不该 `raise`
- 异常说明文字是否准确
- 裸 `raise` / `raise err`（变量再抛）— 检查器会忽略，避免误报
- §6 穿透异常是否写全（未自动核对）
- `ruff` 已管的事（如 `print`）— 仍用 `ruff check engines`，不要说本技能已覆盖
- 不执行代码、不验证导入、不替代 OpenSpec / 子目录 AGENTS 架构规则

过检 **≠** 整份规范正文合规；只能说「机械化条目当前无报 / 仍有 N 条」。

## 怎么跑（主路径：先进入技能目录）

与 `skill-creator` 一样：在**技能目录**下用 `python -m scripts.<module>` 运行。脚本会从 `__file__` 向上查找含 `engines/AGENTS.md` 的仓库根；因此 `cd` 之后 `--path engines/...` 仍按**仓库根**解析，不是相对当前 cwd。

```text
cd .agents/skills/engines-agents-style-check
python -m scripts.check_engines_agents_style
```

默认全量扫 `<repo>/engines/`，文本输出违规行 + 按规则汇总。退出码：无违规 0，有违规 1。

```text
cd .agents/skills/engines-agents-style-check
python -m scripts.check_engines_agents_style --path engines/agents/tools
```

只扫指定目录或文件（相对路径相对仓库根）。改局部时优先用这个，加快反馈。

```text
cd .agents/skills/engines-agents-style-check
python -m scripts.check_engines_agents_style --format json
```

同样扫描，JSON 输出（含扫描文件数与 violations），供脚本解析；可与 `--path` 联用。

门禁（非阻塞 WARN；`check_gates` 会把 cwd 设为本技能目录）：

```text
python -m utils.check_gates --only engines-agents-style
```

### 次要：不 cd 时（不推荐）

若必须从仓库根调用，需把 cwd / `PYTHONPATH` 指到本技能目录后再 `python -m scripts.check_engines_agents_style`。**优先使用上面的 `cd` 形式**（与 skill-creator 一致）。

## Bundled resources

- 检查器实现：`scripts/check_engines_agents_style.py`（canonical；从本技能目录 `python -m scripts.check_engines_agents_style`）
- 风格正文：[`.agents/rules/engines-code-style.md`](../../rules/engines-code-style.md)
- 何时读 / 何时查：[`engines/AGENTS.md`](../../../engines/AGENTS.md)（子目录 AGENTS 更具体时以子目录为准；本检查器只执行上表条目）

## 门禁接线

`utils/check_gates.py` 中 `engines-agents-style` 门禁调用：

```text
[py, "-m", "scripts.check_engines_agents_style"]
cwd = <repo>/.agents/skills/engines-agents-style-check
blocking=False
```

## 执行步骤

1. `cd` 到 `.agents/skills/engines-agents-style-check`（或经门禁自动设 cwd）。
2. 若本次只改了某子树，用 `--path` 指向该子树（仓库根相对）；否则全量。
3. 运行检查；保留完整输出。
4. 向用户汇报时**只陈述检查器覆盖的规则**与具体路径/行号；需要谈职责划分、依赖时，单独作为人工/设计审查，勿写成「检查已通过所以设计也 OK」。
5. 若要修复：只改 docstring / 命名等与报错对应的项；改完对同一 `--path` 再跑一遍确认。
6. 不要在未再跑检查的情况下声称「Raises 已全部对齐」。

## 汇报模板（短）

- 命令：…
- 扫描范围 / 文件数：…
- 结果：通过，或 `module-docstring=A, raises-doc=B, …`
- 说明：仅覆盖 AST 可查条目；未覆盖单一职责 / 穿透 Raises / ruff 等
