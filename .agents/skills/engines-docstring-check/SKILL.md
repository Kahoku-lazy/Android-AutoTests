---
name: engines-docstring-check
description: 读写本仓库 engines/ 的 Python docstring（注释）——① 改完代码后按既定规则校验注释是否合规（模块 11 字段 ➡️/🏁 模板、类 Attributes、函数 Args/Returns/Raises、段序、编号连续性），默认只查 git 改动、且只报本次新引入的问题，不噪声；② 读代码前先抽取 docstring + 签名，拿到模块职责/能力清单/依赖/测试归属，不必逐行读实现。凡出现「注释合规吗」「docstring 检查」「补注释」「Raises 写了没」「这个模块干什么的」「先看注释再读代码」「这批改动动了什么」等意图，或改动了 engines/** 之后要自检，都用本技能。
compatibility: 仅需 Python 3.11+ 与 git；纯标准库脚本，复用仓库 utils/module_docstring.py；面向本仓库（Android-AutoTests），不适用于其他项目。
---

# engines docstring 读写（本仓库专用）

本技能负责 **engines/ 的注释/docstring**：一边**校验合规**，一边**当读代码的入口**。
规范正文是 [`.agents/rules/engines-code-style.md`](../../rules/engines-code-style.md) §2 / §5 / §6；何时读规范、何时检查由 [`engines/AGENTS.md`](../../../engines/AGENTS.md) 规定。本技能只做**可机械化**的那部分，不替代人读散文。

## 与 `engines-agents-style-check` 的分工（先看这张表，别跑错）

| 关注点 | 用哪个技能 |
| --- | --- |
| 注释 / docstring 的内容与结构（字段、Args、Returns、Raises、段序、编号） | **本技能** `engines-docstring-check` |
| 想先看注释了解代码（读之前的地图） | **本技能** `read` |
| `tool_*.py` 命名、`engines/**` 禁 `django`/`apps` import、`module-docstring` 存在性 | [`engines-agents-style-check`](../engines-agents-style-check/SKILL.md) |

两者有少量重叠（都看 docstring 存在性 / Raises）。**改注释后自检用本技能**；`run.py check` 里的 `engines-agents-style` 门禁照常跑，不需要你手动调。

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
python -m scripts.docstrings check --path engines/agents/tools
python -m scripts.docstrings check --path engines/x.py --strict   # warn 也算失败
python -m scripts.docstrings check --format json          # 给脚本/CI 解析
```

### B. 读代码前先取注释（省 token 的地图）

```text
cd .agents/skills/engines-docstring-check
python -m scripts.docstrings read --path engines/agents/tools/tool_device.py
python -m scripts.docstrings read --changed              # 先看这批改动涉及哪些模块、各干什么
python -m scripts.docstrings read --path engines/agents  # 整个子包速览
python -m scripts.docstrings read --path engines/x.py --depth module   # 只看模块级字段
python -m scripts.docstrings read --changed --format md  # 贴进回复/文档
```

`read` 输出：模块 11 字段（功能 / 调试入口 / 简介说明 / 关联模块 / 测试）+ 类与函数的**签名 + 摘要 + 段清单 + 抛出的异常类型 + 行号**，最后列出**没写 docstring 的公开符号**（提示这块只能去读实现）。

**为什么先 read**：模块 docstring 的「简介说明」就是作者写的能力清单，签名来自 AST 不会漂移，比逐行读实现快一个量级；而且能立刻看出这块注释是否可信（见下面的边界）。

## 检查规则（13 条，这就是「既定规则」的机械化切片）

| rule | 级别 | 判据 | 规范条款 |
| --- | --- | --- | --- |
| `module-docstring` | error | 文件有模块 docstring（空壳 `__init__.py` 豁免） | §2.1 |
| `module-fields` | error | 11 个模板字段齐全、`类型` 属 4 枚举、`路径`/`文件名` 与真实一致、`Python 调试` 是 `python -m …` | §2 |
| `module-summary` | error | `模块功能` 非空、不以编号或 `python -m` 开头（一句话职责） | §2.2 |
| `module-numbering` | error | `简介说明` / `关联模块` / `测试` 的编号列表从 1 连续 | §2 模板 |
| `class-docstring` | error | 公开类有 docstring | §2.1 |
| `class-attributes` | warn | 有字段的类，`Attributes:` 段列全字段名 | §2 类模板 |
| `def-docstring` | error | 公开函数/方法（含 `__init__`）有 docstring | §2.1 |
| `doc-summary` | error | 首行是一句话摘要，不直接以 `Args:` 之类的段名开头 | §2.3 |
| `doc-args` | error | 有参数就有 `Args:`，且参数名一个不漏 | §2.3 |
| `doc-args-empty` | warn | `Args:` 每个条目都有说明文字 | §2.3 |
| `doc-returns` | error | 有返回值（注解非 `None`，或体内 `return <expr>`）就有 `Returns:`；生成器按 `Yields:` 不强制 | §2.3 |
| `doc-raises` | error | 体内有显式 `raise X`，`Raises:` 必须列出 X（裸 `raise` 不计） | §5.1 |
| `doc-order` | error | 段序 `Args` → `Returns` → `Raises` | §5.3 / §6.2 |

补充约定（脚本里写死，便于你判断是否符合预期）：

- **公开** = 名字不以 `_` 开头，另外 `__init__` 算公开。私有辅助函数不强制，避免把内部实现噪声化。
- **只看模块/类体**，不进函数体里找嵌套函数。
- `模块功能` 那条是**解释**：模板要求「一句话职责」，编号列表属于「简介说明」。历史上有 21 个模块把第 2 条能力写进了 `模块功能`，`check --all` 会全部列出来。
- 严重级决定退出码：`error` 失败；`warn` 默认不影响退出码（`--strict` 才拦）。

## 输出长什么样

```text
engines/uart_log/switch.py:43: [def-docstring] (error) 公开函数 __init__ 缺少 docstring
engines/uart_log/switch.py:47: [doc-args] (error) open: 有参数 ['params'] 但缺 Args: 段

scanned 1 file(s) [path: engines/uart_log/switch.py]; 12 error(s), 0 warn(s): def-docstring=1, doc-args=4, doc-returns=7
```

改动模式下末尾还有一行 `（另有 N 条未计入：HEAD 已有的存量、warn 级…）`——N 不是零，说明**这个文件的注释本来就有欠账**，但你这次没让它更差。想连存量一起看就加 `--include-existing`。

## 汇报模板（别夸大）

- 命令：`python -m scripts.docstrings check --<范围>`
- 范围 / 文件数：…（改了 N 个文件，其中 engines/ 内 M 个）
- 结果：通过；或按 rule 列出 `def-docstring=1, doc-raises=2 …`（带 `文件:行号`）
- 说明：本技能只覆盖上表 13 条可机械化项；**过检 ≠ 整份规范合规**（单一职责、注释文案是否准确、`#` 行内注释质量都没查）

## 修复指引（按 rule 对症）

| rule | 怎么改 |
| --- | --- |
| `module-fields` | 照 `engines/AGENTS.md` 的模块模板补齐；`类型` 只能取 工具模块 / 模型配置模块 / Harness 配置模块 / Agent 能力模块 |
| `module-summary` | `模块功能` 写回一句话职责；把能力清单挪到 `简介说明` 的编号列表 |
| `module-numbering` | 列表从 `1.` 开始连续编号，别跳号 |
| `class-attributes` | 类 docstring 加 `Attributes:`，字段名与 `__init__`/注解一致 |
| `doc-summary` | 在 `Args:` 之前补一行摘要（说明「做什么、返回什么语义」） |
| `doc-args` / `doc-returns` | 补段；参数名照签名写（`self`/`cls` 不写），`Returns:` 写清结构而不是只说「返回结果」 |
| `doc-raises` | 逐个异常类型补 `Raises:`，写触发条件 |
| `doc-order` | 把 `Raises:` 挪到 `Returns:` 之后（工具函数尤其重要：模型只读首行摘要与 `Args:`） |

改完**对同一范围再跑一次**确认归零，再声称修好了。

## 边界（诚实说明，别当它能保证什么）

1. **`#` 行内注释不参与校验**：无法机械化判定「这句注释对不对」，本技能只处理 docstring。想查注释质量只能人看。
2. **只看结构，不看语义**：`Returns:` 写成「返回结果」也能过；`简介说明` 与实际函数不一致也发现不了（实测 73 个模块里，`简介说明` 只覆盖约 40% 的本地公开符号，它**不是 API 索引**）。
3. **`关联模块` 不校验**：那是人工选摘的本地依赖，和 AST import 经常对不上，别拿它当依赖图。
4. **模板字段规则只对 `engines/**` 生效**（规范 §1 的适用范围）。`--repo` 只对 engines 之外的改动叠加通用规则；别给 backend/tests 套这个模板。
5. **存量基线**：`check --all` 当前约 278 error / 21 warn（`doc-returns`、`doc-args` 是大头）。这是**欠账清单**，不是「你改坏了」。不要为了清零做大扫除式改动——规则 §7.1 明确「逐步补齐旧代码，不做无关大扫除」。
6. 不执行代码、不验证 import、不替代 ruff（`python run.py check` 里那套）与 OpenSpec 流程。

## Bundled resources

- 实现：`scripts/docstrings.py`（`check` / `read` 两个子命令；从本技能目录 `python -m scripts.docstrings …` 运行）
- 自检：`python -m scripts.selftest` —— 用合成源码验证 13 条规则仍按预期触发（改规则后必跑）。
- 规范正文：[`.agents/rules/engines-code-style.md`](../../rules/engines-code-style.md)（§2 注释、§5 Raises、§6 agents 专规）
- 流程入口：[`engines/AGENTS.md`](../../../engines/AGENTS.md)（何时读规范、何时用本技能）
- 姊妹技能：[`engines-agents-style-check`](../engines-agents-style-check/SKILL.md)（命名 / 禁 import / 门禁）
