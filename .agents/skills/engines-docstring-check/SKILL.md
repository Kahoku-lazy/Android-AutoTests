---
name: engines-docstring-check
description: 读写本仓库 engines/ 的 Python docstring（注释）——① 改完代码后按既定规则校验注释是否合规（模块头 4 字段 ➡️/🏁 模板：模块功能 / Python 调试 / 时间 / 测试；工具函数首行摘要 + Args；不再要求 Returns/Raises），默认只查 git 改动、且只报本次新引入的问题，不噪声；② 读代码前先抽取 docstring + 签名，拿到模块职责/能力清单/测试归属，不必逐行读实现。凡出现「注释合规吗」「docstring 检查」「补注释」「这个模块干什么的」「先看注释再读代码」「这批改动动了什么」等意图，或改动了 engines/** 之后要自检，都用本技能。
compatibility: 仅需 Python 3.11+ 与 git；纯标准库脚本，复用仓库 utils/module_docstring.py；面向本仓库（Android-AutoTests），不适用于其他项目。
---

# engines docstring 读写（本仓库专用）

本技能负责 **engines/ 的注释/docstring**：一边**校验合规**，一边**当读代码的入口**。
规范正文是 [`.agents/rules/engines-code-style.md`](../../rules/engines-code-style.md) §2 / §6；何时读规范、何时检查由 [`engines/AGENTS.md`](../../../engines/AGENTS.md) 规定。本技能只做**可机械化**的那部分，不替代人读散文。

**2026-11-24 起的口径**：模块头只保留 4 个字段（模块功能 / Python 调试 / 时间 / 测试）；普通函数、类、行内 `#` 注释**默认不写**；只有被 `FunctionTool(...)` 注册、会把说明交给模型的工具函数必须写「首行摘要 + `Args:`」。

## 与 `engines-agents-style-check` 的分工（先看这张表，别跑错）

| 关注点 | 用哪个技能 |
| --- | --- |
| 注释内容与结构（模块头 4 字段、工具函数摘要与 `Args`、编号连续性） | **本技能** `engines-docstring-check` |
| 想先看注释了解代码（读之前的地图） | **本技能** `read` |
| `tool_*.py` 命名、`engines/**` 禁 `django`/`apps` import、module-docstring 存在性 | [`engines-agents-style-check`](../engines-agents-style-check/SKILL.md) |

**改注释后自检用本技能**；`run.py check` 里的 `engines-agents-style` 门禁照常跑，不需要你手动调。

## 两个使用时机

### A. 写完代码要自检（默认路径）

```text
cd .agents/skills/engines-docstring-check
python -m scripts.docstrings check
```

不用给参数：默认查 **git 改动的 engines/** 文件，并且只报**这次改动新引入**的违规（与 HEAD 版本逐符号对比，文件里原有的欠账不算你头上），只报 error 级。退出码 0 = 通过，1 = 有 error。

覆盖不到时按需加范围：

```text
python -m scripts.docstrings check --include-existing     # 连 HEAD 已有的存量一起报（整文件口径）
python -m scripts.docstrings check --all                  # 全量审计 engines/（存量清单，不是回归）
python -m scripts.docstrings check --path engines/ae_harness/tools
python -m scripts.docstrings check --path engines/x.py --strict   # warn 也算失败
python -m scripts.docstrings check --format json          # 给脚本/CI 解析
```

### B. 读代码前先取注释（省 token 的地图）

```text
cd .agents/skills/engines-docstring-check
python -m scripts.docstrings read --path engines/ae_harness/tools/adb/tools.py
python -m scripts.docstrings read --changed              # 先看这批改动涉及哪些模块、各干什么
python -m scripts.docstrings read --path engines/ae_harness  # 整个子包速览
python -m scripts.docstrings read --path engines/x.py --depth module   # 只看模块级字段
python -m scripts.docstrings read --changed --format md  # 贴进回复/文档
```

`read` 输出：模块头 4 字段（功能 / 调试入口 / 时间 / 测试；历史文件若还带「简介说明 / 关联模块」也会一起显示）+ 类与函数的**签名 + 摘要 + 段清单 + 行号**。

**为什么先 read**：模块头的「模块功能」和工具函数的摘要就是作者写的职责/能力说明，签名来自 AST 不会漂移，比逐行读实现快一个量级；而且能立刻看出这块注释是否可信（见下面的边界）。

## 检查规则（8 条，这就是「既定规则」的机械化切片）

| rule | 级别 | 判据 | 规范条款 |
| --- | --- | --- | --- |
| `module-docstring` | error | 文件有模块 docstring（空壳 `__init__.py` 豁免） | §2.1 |
| `module-fields` | error | 4 字段齐全（模块功能 / Python 调试 / 时间 / 测试）、`Python 调试` 是 `python -m …`、`时间` 是 `YYYY-MM-DD` | §2 |
| `module-summary` | error | `模块功能` 非空、不以编号或 `python -m` 开头（一句话职责） | §2 |
| `module-numbering` | error | `测试` 的编号列表从 1 连续 | §2 模板 |
| `tool-docstring` | error | 被 `FunctionTool(...)` 注册的工具函数必须有 docstring | §2.3 / §6.1 |
| `tool-summary` | error | 工具函数 docstring 首行是一句话摘要，不直接以 `Args:` 之类的段名开头 | §6.1 |
| `tool-args` | error | 工具函数有参数就有 `Args:`，且参数名一个不漏 | §6.1 |
| `tool-args-empty` | warn | `Args:` 每个条目都有说明文字 | §2.3 |

补充约定（脚本里写死，便于你判断是否符合预期）：

- **工具函数** = 模块里被 `FunctionTool(fn, ...)` 第一个位置参数引用的函数名（`FunctionTool` / `模块.FunctionTool` 都识别）。普通函数、类不查注释。
- **只看模块/类体**，不进函数体里找嵌套函数。
- **不再检查**：类 `Attributes:`、`Returns:`、`Raises:`、段序；这些段写了也不报错，只是不要求。
- 严重级决定退出码：`error` 失败；`warn` 默认不影响退出码（`--strict` 才拦）。

## 输出长什么样

```text
engines/ae_harness/tools/document/tools.py:1: [module-fields] (error) 缺少字段：时间
engines/ae_harness/tools/adb/tools.py:120: [tool-args] (error) adb_tap: 有参数 ['x', 'y'] 但缺 Args: 段

scanned 1 file(s) [path: engines/ae_harness/tools/document/tools.py]; 2 error(s), 0 warn(s): module-fields=1, tool-args=1
```

改动模式下末尾还有一行 `（另有 N 条未计入：HEAD 已有的存量、warn 级…）`——N 不是零，说明**这个文件的注释本来就有欠账**，但你这次没让它更差。想连存量一起看就加 `--include-existing`。

## 汇报模板（别夸大）

- 命令：`python -m scripts.docstrings check --<范围>`
- 范围 / 文件数：…（改了 N 个文件，其中 engines/ 内 M 个）
- 结果：通过；或按 rule 列出 `module-fields=1, tool-args=2 …`（带 `文件:行号`）
- 说明：本技能只覆盖上表 8 条可机械化项；**过检 ≠ 整份规范合规**（单一职责、注释文案是否准确、`#` 行内注释质量都没查）

## 修复指引（按 rule 对症）

| rule | 怎么改 |
| --- | --- |
| `module-fields` | 照 §2 模板补齐 4 字段；`时间` 写 `YYYY-MM-DD`，`Python 调试` 写 `python -m …`；**不要**再加文件名/路径/作者/版本/类型/简介说明/关联模块 |
| `module-summary` | `模块功能` 写回一句话职责，编号列表挪出该字段 |
| `module-numbering` | `测试` 列表从 `1.` 开始连续编号，别跳号 |
| `tool-docstring` | 给工具函数补 docstring：首行一句话说明干什么 |
| `tool-summary` | 在 `Args:` 之前补一行摘要 |
| `tool-args` / `tool-args-empty` | 补 `Args:`；参数名照签名写（`self`/`cls` 不写），每个参数一行说明 |

改完**对同一范围再跑一次**确认归零，再声称修好了。

## 边界（诚实说明，别当它能保证什么）

1. **`#` 行内注释不参与校验**：无法机械化判定「这句注释对不对」，本技能只处理 docstring。
2. **普通函数 / 类不再要求注释**：所以它们缺 docstring 不会报错；想确认「这段实现到底干什么」只能读代码。
3. **只看结构，不看语义**：`Args:` 写成「参数」也能过；摘要与实际行为不一致也发现不了。
4. **模板字段规则只对 `engines/**` 生效**（规范 §1 的适用范围）。`--repo` 只对 engines 之外的改动叠加通用规则；别给 backend/tests 套这个模板。
5. **存量未迁移**：89 个旧模块头仍带 `文件名/路径/作者/版本/类型/简介说明/关联模块`，`utils/module_docstring.py` 仍能解析这些字段（兼容读取），但**不再要求新文件写**，也不要求删除旧字段。`check --all` 主要是存量欠账清单，不是「你改坏了」；不要为了清零做大扫除式改动——规范 §7.1 明确「逐步补齐旧代码，不做无关大扫除」。
6. 不执行代码、不验证 import、不替代 ruff（`python run.py check` 里那套）与 OpenSpec 流程。

## Bundled resources

- 实现：`scripts/docstrings.py`（`check` / `read` 两个子命令；从本技能目录 `python -m scripts.docstrings …` 运行）
- 自检：`python -m scripts.selftest` —— 用合成源码验证 8 条规则仍按预期触发（改规则后必跑）。
- 规范正文：[`.agents/rules/engines-code-style.md`](../../rules/engines-code-style.md)（§2 注释、§6 agents 专规）
- 流程入口：[`engines/AGENTS.md`](../../../engines/AGENTS.md)（何时读规范、何时用本技能）
- 姊妹技能：[`engines-agents-style-check`](../engines-agents-style-check/SKILL.md)（命名 / 禁 import / 门禁）
