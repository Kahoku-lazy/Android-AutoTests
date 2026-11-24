---
name: engines-docstring-check
description: 读写本仓库 Python 的 docstring（注释）——① 改完代码后按既定规则校验注释是否合规（模块头 4 字段 ➡️/🏁 模板：模块功能 / Python 调试 / 时间 / 测试；engines 工具函数首行摘要 + Args；不再要求 Returns/Raises），默认只查 git 改动、且只报本次新引入的问题，不噪声；② 读代码前先抽取 docstring + 签名，拿到模块职责/能力清单/测试归属，不必逐行读实现。2026-11-24 起范围是全仓在册 Python 文件（engines 之外的 backend/tests/utils/根脚本也查，Django 固定脚手架排除）。凡出现「注释合规吗」「docstring 检查」「补注释」「这个模块干什么的」「先看注释再读代码」「这批改动动了什么」等意图，或改动了 engines/** 之后要自检，都用本技能。
compatibility: 仅需 Python 3.11+ 与 git；纯标准库脚本，复用仓库 utils/module_docstring.py；面向本仓库（Android-AutoTests），不适用于其他项目。
---

# Python 模块 docstring 读写（本仓库专用）

本技能负责**全仓 Python 的模块 docstring**：一边**校验合规**，一边**当读代码的入口**。
规范正文是 [`.agents/rules/python-docstring-style.md`](../../rules/python-docstring-style.md)（2026-11-24 起全仓生效，不再是 engines 专属）；
engines 工具函数的追加条款在 [`.agents/rules/engines-code-style.md`](../../rules/engines-code-style.md) §6。
技能目录名 `engines-docstring-check` 沿用历史，**实际检查范围是全仓在册文件**。

**口径要点**：模块头只保留 4 个字段（模块功能 / Python 调试 / 时间 / 测试）；普通函数、类、行内 `#` 注释**默认不写**；
唯一例外是 `engines/ae_harness/tools/**` 里被 `FunctionTool(...)` 注册的工具函数——必须写「首行摘要 + `Args:`」，
那是交给模型的说明，**不属注释债务，不得删减**。

## 范围（机器判定见 `docstrings.py` 的 `in_scope` / `exclusion_reason`）

| 在册（必须写 4 字段） | 排除（不要求、也不报错） |
| --- | --- |
| `engines/**`、`backend/**`（非固定结构）、`tests/**`、`utils/**`、根 `run.py` / `run_daphne.py` | Django 固定脚手架（`models.py`、`views*.py`、`api.py`/`api_*.py`、`serializers*.py`、`admin.py`、`urls.py`、`apps.py`、`asgi.py`、`wsgi.py`、`settings.py`、`manage.py`、`migrations/**`）；`.agents/**`、`temps/**`、`dev_docs/**`、`openspec/**`、`frontend/**`；依赖与缓存目录 |

在册是**白名单**口径：新增顶层目录要同时改 `IN_SCOPE_ROOTS` 与规范 §1，否则不会被检查。

## 与 `engines-agents-style-check` 的分工（先看这张表，别跑错）

| 关注点 | 用哪个技能 |
| --- | --- |
| 注释内容与结构（模块头 4 字段、工具函数摘要与 `Args`、编号连续性） | **本技能** `engines-docstring-check` |
| 想先看注释了解代码（读之前的地图） | **本技能** `read` |
| `tool_*.py` 命名、`engines/**` 禁 `django`/`apps` import、module-docstring 存在性 | [`engines-agents-style-check`](../engines-agents-style-check/SKILL.md) |

**改注释后自检用本技能**；`run.py check` 里的 `engines-agents-style` 与 `python-module-docstring` 门禁照常跑，不需要你手动调。

## 两个使用时机

### A. 写完代码要自检（默认路径）

```text
cd .agents/skills/engines-docstring-check
python -m scripts.docstrings check
```

不用给参数：默认查 **git 改动的在册文件**，并且只报**这次改动新引入**的违规（与 HEAD 版本逐符号对比，文件里原有的欠账不算你头上），只报 error 级。退出码 0 = 通过，1 = 有 error。

覆盖不到时按需加范围：

```text
python -m scripts.docstrings check --include-existing     # 连 HEAD 已有的存量一起报（整文件口径）
python -m scripts.docstrings check --all                  # 全仓在册文件全量审计（存量清单，不是回归）
python -m scripts.docstrings check --all --summary        # 只出按规则聚合的计数（门禁 / 巡检用）
python -m scripts.docstrings check --path utils
python -m scripts.docstrings check --path tests/arch/unit/test_channels.py --strict   # warn 也算失败
python -m scripts.docstrings check --format json          # 给脚本/CI 解析
```

`--path` 指向排除范围内的文件（如 `backend/apps/accounts/api.py`）时不会报违规，只在 stderr 提示「跳过 N 个排除文件」。
`--repo` 已废弃（范围本来就是全仓），保留仅为兼容旧命令。

### B. 读代码前先取注释（省 token 的地图）

```text
cd .agents/skills/engines-docstring-check
python -m scripts.docstrings read --path utils/gen_arch_stats.py
python -m scripts.docstrings read --changed              # 先看这批改动涉及哪些模块、各干什么
python -m scripts.docstrings read --path engines/ae_harness  # 整个子包速览
python -m scripts.docstrings read --path engines/x.py --depth module   # 只看模块级字段
python -m scripts.docstrings read --changed --format md  # 贴进回复/文档
```

`read` 输出：模块头 4 字段（功能 / 调试入口 / 时间 / 测试；历史文件若还带「简介说明 / 关联模块」也会一起显示）+ 类与函数的**签名 + 摘要 + 段清单 + 行号**。
`read` 不受在册范围限制：排除范围内的文件也能读（它就是读代码的工具）。

**为什么先 read**：模块头的「模块功能」和工具函数的摘要就是作者写的职责/能力说明，签名来自 AST 不会漂移，比逐行读实现快一个量级；而且能立刻看出这块注释是否可信（见下面的边界）。

## 检查规则（8 条，这就是「既定规则」的机械化切片）

| rule | 级别 | 判据 | 规范条款 |
| --- | --- | --- | --- |
| `module-docstring` | error | 在册文件有模块 docstring（空壳 `__init__.py` 豁免） | 规范 §2 |
| `module-fields` | error | 4 字段齐全（模块功能 / Python 调试 / 时间 / 测试）、`Python 调试` 是 `python -m …`、`时间` 是 `YYYY-MM-DD` | 规范 §2 |
| `module-summary` | error | `模块功能` 非空、不以编号或 `python -m` 开头（一句话职责） | 规范 §2 |
| `module-numbering` | error | `测试` 的编号列表从 1 连续 | 规范 §2 |
| `tool-docstring` | error | 被 `FunctionTool(...)` 注册的工具函数必须有 docstring | 规范 §3.2 / engines §6.1 |
| `tool-summary` | error | 工具函数 docstring 首行是一句话摘要，不直接以 `Args:` 之类的段名开头 | engines §6.1 |
| `tool-args` | error | 工具函数有参数就有 `Args:`，且参数名一个不漏 | engines §6.1 |
| `tool-args-empty` | warn | `Args:` 每个条目都有说明文字 | 规范 §3.2 |

补充约定（脚本里写死，便于你判断是否符合预期）：

- **工具函数** = 模块里被 `FunctionTool(fn, ...)` 第一个位置参数引用的函数名（`FunctionTool` / `模块.FunctionTool` 都识别）。普通函数、类不查注释。
- **只看模块/类体**，不进函数体里找嵌套函数。
- **不再检查**：`Attributes:`、`Returns:`、`Raises:`、段序；这些段写了也不报错，只是不要求。
- 严重级决定退出码：`error` 失败；`warn` 默认不影响退出码（`--strict` 才拦）。

## 输出长什么样

```text
utils/gen_arch_stats.py:1: [module-fields] (error) 有 docstring 但未使用➡️/🏁模板
utils/gen_arch_stats.py:1: [module-fields] (error) 缺少字段：模块功能
scanned 1 file(s) [排除 0 个] [path: utils/gen_arch_stats.py]; 6 error(s), 0 warn(s): module-fields=5, module-summary=1
```

聚合模式：

```text
files_in_scope: 464, files_excluded: 282
  module-docstring   1
  module-fields      1520
  module-summary     304
errors: 1826, warns: 0, files_with_issues: 306
top: backend/__init__.py(6), ...
```

改动模式下末尾还有一行 `（另有 N 条未计入：HEAD 已有的存量、warn 级…）`——N 不是零，说明**这个文件的注释本来就有欠账**，但你这次没让它更差。想连存量一起看就加 `--include-existing`。

## 汇报模板（别夸大）

- 命令：`python -m scripts.docstrings check --<范围>`
- 范围 / 文件数：…（改了 N 个文件，其中在册 M 个）
- 结果：通过；或按 rule 列出 `module-fields=1, tool-args=2 …`（带 `文件:行号`）
- 说明：本技能只覆盖上表 8 条可机械化项；**过检 ≠ 整份规范合规**（单一职责、注释文案是否准确、`#` 行内注释质量都没查）

## 修复指引（按 rule 对症）

| rule | 怎么改 |
| --- | --- |
| `module-fields` | 照规范 §2 模板补齐 4 字段；`时间` 写 `YYYY-MM-DD`，`Python 调试` 写 `python -m …`；**不要**再加文件名/路径/作者/版本/类型/简介说明/关联模块 |
| `module-summary` | `模块功能` 写回一句话职责，编号列表挪出该字段（明细写进 `.agents/docs/**` 模块文档） |
| `module-numbering` | `测试` 列表从 `1.` 开始连续编号，别跳号 |
| `tool-docstring` | 给工具函数补 docstring：首行一句话说明干什么 |
| `tool-summary` | 在 `Args:` 之前补一行摘要 |
| `tool-args` / `tool-args-empty` | 补 `Args:`；参数名照签名写（`self`/`cls` 不写），每个参数一行说明 |

改完**对同一范围再跑一次**确认归零，再声称修好了。

## 边界（诚实说明，别当它能保证什么）

1. **`#` 行内注释不参与校验**：无法机械化判定「这句注释对不对」，本技能只处理 docstring。
2. **普通函数 / 类不再要求注释**：所以它们缺 docstring 不会报错；想确认「这段实现到底干什么」只能读代码。
3. **只看结构，不看语义**：`Args:` 写成「参数」也能过；摘要与实际行为不一致也发现不了。
4. **模板字段规则对在册文件生效，对排除清单生效为「不检查」**：别给 `backend/apps/*/api.py`、`models.py`、`migrations/**` 套模板。
5. **存量未清零**：`check --all` 主要是在册范围的存量欠账清单，不是「你改坏了」；按 `openspec/changes/repo-wide-python-docstring/tasks.md` 的分批节奏推进，不做无关大扫除。
6. **工具函数 docstring 不是可删注释**：它被 AgentScope 读取成模型可见的工具说明；任何批量整理都不得删改（规范 §3.2）。
7. 不执行代码、不验证 import、不替代 ruff（`python run.py check` 里那套）与 OpenSpec 流程。

## Bundled resources

- 实现：`scripts/docstrings.py`（`check` / `read` 两个子命令；从本技能目录 `python -m scripts.docstrings …` 运行）
- 自检：`python -m scripts.selftest` —— 用合成源码验证 8 条规则 + 范围判定表仍按预期触发（改规则后必跑）
- 规范正文：[`.agents/rules/python-docstring-style.md`](../../rules/python-docstring-style.md)；engines 追加条款：[`.agents/rules/engines-code-style.md`](../../rules/engines-code-style.md) §6
- 流程入口：[`engines/AGENTS.md`](../../../engines/AGENTS.md)「AI 阅读与检查流程」（engines 任务）；根 `AGENTS.md`「文档与工具说明」
- 姊妹技能：[`engines-agents-style-check`](../engines-agents-style-check/SKILL.md)（命名 / 禁 import / 门禁）
