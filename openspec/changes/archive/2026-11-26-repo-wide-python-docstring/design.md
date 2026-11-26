# Design: repo-wide-python-docstring

## Context

见 `proposal.md` — Why。补充两条约束：

1. engines 的 4 字段方案不是「待讨论的想法」，而是 2026-11-24 已落地并被检查器机械校验的现状（89/91 达标）。
   本次是**扩大适用范围**，不是重新设计模板——模板、`➡️/🏁` 标记、字段语义一律不动。
2. 全仓 744 个 `.py`（已排除 `.venv`/`node_modules`/`__pycache__`）。在册范围与存量差距实测（2026-11-24）：

| 分区 | 文件 | 已达标 | 有 docstring 非模板 | 无 docstring |
| --- | --- | --- | --- | --- |
| engines | 91 | 89 | 2 | 0 |
| backend 非固定结构 | 91 | 0 | 64 | 27 |
| tests | 255 | 1 | 210 | 44 |
| utils | 26 | 1 | 25 | 0 |
| 根 `run.py`/`run_daphne.py` | 2 | 0 | 2 | 0 |
| **在册合计** | **465** | **91** | **301** | **71** |

Django 固定结构 233 个（含 migrations）、`.agents` 34、`temps` 9、`dev_docs` 4、`manage.py` 1 等 —— 不在册（共 279 个）。

**批次 1 完成后的实测（`check --all --summary`）**：在册 465，达标 190（其中约 70 个是空壳 `__init__.py` 豁免），
待迁移 275 个文件（`tests` + `backend` 非固定结构）；`engines` 91/91、`utils` 26/26、根脚本 2/2 已归零。

**批次 2 完成后的实测**：在册 **328**（engines 91 / backend 非固定结构 91 / tests 118 / utils 26 / 根脚本 2），
其中待迁移 **58 个文件（全部在 backend）**，`tests`、`utils`、`engines`、根脚本均 0 error。
在册数从 465 降到 328 的原因见 D10（单元测试层迁出仓库）。

**批次 3 完成后的实测（收口）**：`check --all --summary` = 在册 **328**、**0 error**、**0 files_with_issues**；
排除 **436 个**（Django 脚手架 232、`temps/` 归档用例与临时脚本、`.agents`、`dev_docs` 等）。

## Goals / Non-Goals

**Goals**
- 一套模板、一处正文、一个检查器，覆盖全部在册 Python 文件；agents 与人类读到同一份规则。
- 存量按目录分批清零，每批可独立回归、独立回退。

**Non-Goals**
- 不改模板字段（不加 `作者`/`版本`/`简介说明` 回来，也不新增第 5 个字段）。
- 不要求普通函数 / 类写 docstring（§2.2 口径不变，只有 engines 的 `FunctionTool` 工具函数例外）。
- **不删减 `engines/ae_harness/tools/**` 里任何工具函数的 docstring**——那是给模型看的说明，不是注释债务（见 D9）。
- 不做「一次大扫除」：不复述代码行、不补类型注解、不顺手重构。
- 不动 Django 脚手架文件（即使它们也有自由格式 docstring）。

## Decisions

### D1 排除清单：按「Django 生成的固定结构」而不是「backend 目录」划界

排除（不写模块头）：

| 类别 | 具体文件 |
| --- | --- |
| Django 脚手架（仅 `backend/**`） | `models.py`、`views.py`、`views_*.py`、`*_views.py`、`api.py`、`api_*.py`、`serializers*.py`、`admin.py`、`urls.py`、`apps.py`、`asgi.py`、`wsgi.py`、`settings.py`、根 `manage.py` |
| 迁移 | `backend/**/migrations/` 下的文件 |
| 非产品代码 | `.agents/**`、`temps/**`、`dev_docs/**`、`openspec/**`、`frontend/**`、依赖与缓存目录 |

纳入：`engines/**`、`backend/**` 除上表以外的文件（服务层、AI 装配层、`management/commands/*`、`shared/**`、`gateway/**`）、
`tests/**`、`utils/**`、根 `run.py` / `run_daphne.py`。

**三个边界判定（需求方选项未逐字覆盖，明确记录）**：
- 根 `manage.py` 归入 Django 脚手架排除——它是 `django-admin startproject` 生成的 15 行入口，与 `settings.py` 同类；
  需求方「根脚本纳入」指的是 `run.py` / `run_daphne.py`（项目自写）。若要翻转，只需改检查器常量一处。
- `backend/**/management/commands/*.py` 纳入——它们是项目自写的一次性运维脚本（`recalc_usage_costs.py` 等），不是 Django 生成的骨架。
- **按文件名排除只在 `backend/` 下生效**：`engines/ae_harness/agents/models.py`、`engines/ae_harness/knowledge/models.py` 是引擎领域模型，
  必须照常检查（实测这两处最初被误排除，已修）；否则「排除 Django 骨架」会被误读成「凡叫 models.py 都不写」。

**为什么按目录划界而不是按「是否 Django 相关」**：后者无法机械化——`api.py`（Django API 层）与 `api_rows.py`（同为 API 层的拆分模块）
只差一个词，靠语义判断必然分歧；检查器必须能用路径 + 文件名确定性判定，否则「排除清单」迟早被解读出第三种答案。
本次取「API / 视图 / 模型这一层整体排除」：`api.py` 与 `api_*.py`、`views.py` 与 `views_*.py`、`*_views.py` 同进同出。

### D2 tests 口径：测试文件也要 4 字段，`测试` 字段写「覆盖什么」

测试文件是代码，不享受豁免。字段填法：

| 字段 | 测试文件的填法 |
| --- | --- |
| 模块功能 | 这份用例保证什么行为（一句话），例如「接口鉴权：未带 JWT 的业务路由必须 401」 |
| Python 调试 | `python -m pytest -c tests/pytest.ini tests/<路径>` |
| 时间 | 首次写 / 最近改写该模块头的日期 |
| 测试 | `1. 覆盖 <被测模块相对路径>`（可多条，按被测面拆） |

**为什么不写「1. 本文件即用例」**：该字段在测试文件上唯一有价值的信息是「它守的是哪块生产代码」，
写成自指等于把字段废掉——后人还得再读一遍 import 才知道覆盖什么。

**空壳 `__init__.py` 豁免**：无 defs 且只有常量的 `__init__.py` 不要求模块头（现状已如此，保留）。

### D3 脚本范围：`utils/` + 根脚本纳入，`temps/`、`dev_docs/`、`.agents/` 排除

- `utils/**`（26 个）纳入：它是产品代码的公共基础设施（门禁、linting、服务控制），会被 `run.py` 与 CI 直接调用。
- `temps/**` 排除：AGENTS.md 定义它是临时目录，随时整体删除，为它写模块头是给自己制造待维护噪声。
- `dev_docs/project-viz/tools/**` 排除：一次性数据生成器，产出的是文档看板数据。
- `.agents/**` 排除：agent 技能脚本不是产品代码，且技能常被整体替换/升级；其自身 docstring 由各 skill 的 SKILL.md 承载。
- `manage.py` 见 D1。

### D4 规则唯一真相源：新增全仓规则文件，engines 保留「工具函数」专规

新增 `.agents/rules/python-docstring-style.md` 作为模板与范围的**唯一正文**；
`.agents/rules/engines-code-style.md` §2 收敛为「指向全仓规范 + engines 追加条款」：

- 全仓规范管：4 字段模板、字段取值、排除清单、tests 口径、检查命令。
- engines 追加：`FunctionTool(...)` 注册的工具函数必须写「首行摘要 + `Args:`」（这是 AgentScope 取 `description` 的契约，别处没有）。

**为什么不就地改 `engines-code-style.md` 的 §1 适用范围**：文件名叫 engines 却管全仓，后来者第一眼就会误判适用范围；
而且这份文件属于 engines 层级的规则树（`engines/AGENTS.md` → rules），全仓规则挂在它下面等于把平台规则藏进子系统。

**代价**：`engines-code-style.md` 的 §2 从正文变成指针，历史文档里「§2 定义模板」的引用要跟着改（本次一并改 §8 修订说明）。

### D5 检查器改造：范围判定收进一个函数，`--all` 语义改为全仓

- `in_scope(rel) -> bool` + `exclusion_reason(rel) -> str`：**唯一**的排除判定入口，D1 的表就是它的实现；规则文档里的表与它逐行对应。
- `_module_rules` 不再判 `_is_engines_path`，改判 `in_scope`——这是「模板字段规则扩到全仓」的实质改动点。
- `--all`：从「扫 `engines/`」改为「扫全仓在册文件」。
- 改动模式（默认）：过滤条件从 `engines/` 改为 `in_scope`，其余（HEAD 基线对比、只报新引入）保持不变——这是存量不清零也能安全落地的关键。
- `--repo`：保留为兼容空开关（不再有语义），help 里标注 deprecated，避免历史命令报错。
- 新增 `--summary`：只输出按规则聚合的计数 + 涉及文件数，供非阻塞门禁使用（全量 465 个文件的逐条输出没人看）。
- **不新增规则**，只扩充范围；`RULES` 表 8 条不变。

### D6 分批节奏与每批完成判据

| 批次 | 范围 | 规模 | 完成判据 |
| --- | --- | --- | --- |
| 1 | 规范 + 检查器 + 门禁 + 试点（`utils/**`、根 2 个、engines 2 个残留） | 30 | 试点范围 `check --path` 归零；`selftest` 通过；`run.py check --only python-module-docstring` 可跑 |
| 2 | `tests/**` | ~255 | 该范围 `check --path tests` 归零；`pytest tests -q` 不回归 |
| 3 | `backend/**` 非固定结构 | 91 | 该范围归零；`python -m manage check` + 受影响测试通过 |
| 4 | 收口：全仓 `check --all --summary` 只剩 Django 排除项之外的 0 | — | 计数为 0；文档与检查器口径一致；`openspec validate` 通过 |

每批一个提交（Conventional Commits，`docs(style):` / `chore(tooling):`），**禁止 `git add -A`**。

### D7 迁移原则：只重排注释，不改语义、不改代码

- 现有自由格式 docstring 的**首句**升为 `模块功能`（信息密度最高的那句），其余明细**不搬**——
  能力清单该写进 `.agents/docs/<module>/**` 模块文档，而不是塞回注释（模板只允许 4 字段）。
- 不因为「顺手」改函数签名、import 顺序、日志文案。diff 里出现非 docstring 行 = 该文件要重做。
- 不改日期以外的历史：`时间` 写本次改写日期，不臆造「首次创建时间」。

### D8 信息损失的对冲

自由格式里那些「按类列 12 条能力」的枚举会消失，这是模板的既定取舍（engines 89 个文件已经这样做过）。
对冲办法不是加字段，而是：模块功能那句话必须写到能让人判断「要不要打开这个文件」；需要细节时读模块文档或代码。

### D9 `ae_harness` 工具函数注释是「喂给 Agent 的契约」，必须保留并被覆盖

需求方 2026-11-24 追加约束：`engines/ae_harness/tools/**` 里被 `FunctionTool(...)` 注册的函数，其 docstring 要**保留**，
因为 AgentScope 取首行作 `description`、取 `Args:` 作参数说明——注释在这里是运行时输入，删了等于把工具说明从模型上下文里抹掉。

落地四件事：

1. **规则正文**：模板的「其余位置默认不写注释」必须带一个显式例外，且例外**写明路径** `engines/ae_harness/tools/**`，
   不能只写「工具函数」——历史上就因为写在 `engines/agents/**` 名下，agents 退役后这条专规一度失去指代（§6 标题至今如此）。
2. **engines 规则**：`.agents/rules/engines-code-style.md` §6 标题范围改为 `engines/ae_harness/tools/**`，
   保留「首行摘要 + `Args:`、不要求 `Returns:`/`Raises:`」的口径。
3. **检查器**：`tool-docstring` / `tool-summary` / `tool-args` / `tool-args-empty` 四条本来就不限路径（只要函数名出现在
   `FunctionTool(fn, ...)` 第一位置参数里就查），本次范围扩大后**自动覆盖**，不需要新规则；只需在收口任务里确认计数为 0。
4. **迁移禁令**：批次 1–3 只改模块头；工具文件（`tools.py`）若被模块头迁移碰到，工具函数 docstring 必须逐字不变——
   `git diff` 里出现在 `def ` 上方的改动一律回退重做。

**为什么不把工具说明搬到别处**：`FunctionTool` 的 `description` 就取自函数 docstring，改由外部配置提供等于给「工具说明」造第二个真相源，
与 engines 红线「工具实现放 `tools/<域>/`、由门面分配」冲突。

### D10 与 2026-11-24 测试口径收敛的关系（并行变更，不改本单口径）

并行提交 `97de4e96 test(tests): 测试口径收敛为灰盒与 b2b，单元层迁出仓库` 把 `tests/**/unit/` 的 118 个用例
迁到 `temps/tests-unit-archive/`，`tests/` 只留灰盒、b2b 与 `tests/arch/unit` 契约守护。对本单的影响只有两条：

1. **批次 2 范围缩小**：255 → 118 个文件；收敛后 `tests/` 内的文件仍按 D2 口径写 4 字段（测试文件不豁免）。
2. **归档用例不纳入**：它们落在 `temps/`，按 D3 属排除范围；若将来回迁到 `tests/`，回迁时补模块头即可。

**不改本单口径的原因**：D2 只规定「测试文件怎么写模块头」，与该目录收哪几类测试无关；
把「测试类型口径」写进注释规范会让两套规则互相污染。

## Risks / Trade-offs

- [301 个文件重排后注释与实现漂移] → 每批只改模块头，diff 必须只含 docstring 行；抽检 10% 读模块功能是否与代码一致。
- [排除清单被误读成「backend 全不管」] → 规则表把「纳入」与「排除」两栏并列写死，检查器 `--summary` 输出里打印排除文件数。
- [非阻塞门禁没人看] → 门禁输出聚合计数（`--summary`），存量清零后另开单改阻塞（不在本单）。
- [tests 255 个文件语义字段靠人读] → 分批，每批 ≤60 个文件，按二级目录（arch / device / ai_assistant / ...）切子批。
- [检查器自身在 `.agents/`，属于被排除范围] → 它不写 4 字段模块头是**有意**的（D3），不是遗漏。
- [工作区已带未提交的在途改动] → 本轮开工时工作区已有 8 个与本变更无关的改动（`python run.py` → `python -m run` 口径统一，涉及 README/CONTRIBUTING/CI/`.agents/lint`），其中 5 个文件（`utils/adb.py`、`utils/check_gates.py`、`utils/check_openapi_coverage.py`、`utils/gen_arch_stats.py`、`utils/service_ctl/commands.py`）会同时承载两套差异。提交时必须逐文件 `git add`，**禁止 `git add -A`**；本变更的回退只回退自己那几行。

## Migration Plan

1. 批次 1 落地后再动存量代码；批次 2/3 各自独立提交。
2. 回退：单文件 `git checkout -- <path>`；整批 `git revert <commit>`；规则层回退见 proposal「变更申请」。
3. 无部署动作，无数据迁移。

## Open Questions

- `engines-docstring-check` 这个技能名在规则全仓化后已名不副实（它检查的是全仓）。改名需要同步 `engines/AGENTS.md`、
  `.agents/rules/engines-code-style.md`、根 `AGENTS.md` 的引用，属于收尾动作，不影响本单的规范与迁移；列入 4.x 任务，可与批次 4 同批做。
