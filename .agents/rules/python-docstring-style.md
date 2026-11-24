# Python 注释（模块 docstring）规范 — 全仓

> **层级**：根 [AGENTS.md](../../AGENTS.md) → **本文件（唯一正文）** → 子系统追加条款（如 [`.agents/rules/engines-code-style.md`](engines-code-style.md) §6）
> **本文件是全仓 4 字段模块头的唯一真相源**。engines 不再单独定义模板，只保留「工具函数摘要 + `Args:`」这条追加条款。
> 自动化检查：[`.agents/skills/engines-docstring-check/`](../skills/engines-docstring-check/SKILL.md)（技能名沿用历史，实际检查范围是全仓在册文件）。

## 1. 适用范围

### 1.1 纳入（必须写 4 字段模块头）

| 范围 | 说明 |
| --- | --- |
| `engines/**` | 引擎层（已全量迁移） |
| `backend/**` 非固定结构 | 服务层、AI 装配层、`shared/`、`gateway/`、`config/` 非脚手架文件、`management/commands/*` |
| `tests/**` | 全部用例文件（口径见 §4） |
| `utils/**` | 公共基础设施：门禁、linting、服务控制 |
| 根 `run.py`、`run_daphne.py` | 项目自写入口 |

### 1.2 排除（不写 4 字段模块头，写了也不检查）

| 类别 | 文件 |
| --- | --- |
| Django 固定脚手架（**仅 `backend/**` 下**，见下条说明） | `models.py`、`views.py`、`views_*.py`、`*_views.py`、`api.py`、`api_*.py`、`serializers*.py`、`admin.py`、`urls.py`、`apps.py`、`asgi.py`、`wsgi.py`、`settings.py`、根 `manage.py` |
| 迁移 | `backend/**/migrations/` 下的全部文件 |
| 非产品代码 | `.agents/**`、`temps/**`、`dev_docs/**`、`openspec/**`、`frontend/**` |
| 依赖与缓存 | `.venv`、`.dvenv`、`node_modules`、`__pycache__`、`.git`、`.pytest-tmp`、`.testtmp` |

**按文件名排除只在 `backend/` 下生效**：`engines/ae_harness/agents/models.py`、`engines/ae_harness/knowledge/models.py`
是引擎自己的领域模型（不是 Django ORM 骨架），**照常写 4 字段模块头**；否则「排除 Django 骨架」会被误读成「凡叫 models.py 都不写」。

**为什么按路径 / 文件名判定**：`api.py` 与 `api_rows.py` 只差一个词，只有确定性规则能被机器执行；
「看着像 Django 就不写」这种口子迟早被解读出第三、第四种答案。

**例外：空壳 `__init__.py`**（无 def/class、只有少量语句）不要求模块头；只写了一行包说明也算空壳，不会报错
（要写 4 字段也可以，例如 engines 的包门面）。

## 2. 模块头模板（唯一允许的字段）

```python
"""
模块功能：➡️ 模型配置工具 🏁
Python 调试：➡️python -m engines.agents.config.models_config 🏁
时间：➡️ 2026-10-29 🏁
测试:➡️
1. tests/.../test_xxx.py: 覆盖的测试项简述
🏁
"""
```

`➡️` 是起始符、`🏁` 是结束符，检查器用它正则取字段内容，**缺一个就取不到值**。

| 字段 | 必填 | 取值要求 |
| --- | --- | --- |
| 模块功能 | 是 | 一句话职责；不写编号、不写调试命令、不写「本文件」「该模块」这类空话 |
| Python 调试 | 是 | 可直接复制的 `python -m <模块全名>`，不加任何前缀；**库模块也写模块路径**（与 `engines/` 存量口径一致，便于调试器直接跳转） |
| 时间 | 是 | `YYYY-MM-DD`（本模块头首次写 / 最近改写它的日期，不臆造「创建时间」） |
| 测试 | 是 | `1. <测试文件>: <覆盖项>`，一行一条、从 `1.` 连续编号；确实没有测试写 `1. 暂无` |

**禁止新增字段**：`文件名`、`路径`、`作者`、`版本`、`修改时间`、`类型`、`简介说明`、`关联模块` 一律不写。
历史文件里带着的这 8 个字段不要求立刻删（迁到该文件时一并去掉），新写或改写的模块头只保留上表 4 个。

## 3. 其余位置默认不写注释

1. 类 docstring、普通函数 / 方法 docstring、函数体内的 `#` 行内注释，没有明确要求就**不写**。
2. **唯一例外：工具函数**——`engines/ae_harness/tools/**` 里被 `FunctionTool(...)` 注册、说明会交给模型的函数，
   **必须**写「首行一句话摘要 + `Args:`」，每个参数一行。AgentScope 取首行作工具 `description`、取 `Args:` 作参数说明，
   这里的注释是**运行时输入**，不是注释债务，删了等于把工具说明从模型上下文里抹掉。
   细则见 [`.agents/rules/engines-code-style.md`](engines-code-style.md) §6。
3. 确需解释「**为什么**这么写」（非显然的协议约束、顺序敏感的实现细节）时，允许在该行上方写**一行**短注释：
   只写原因、不写做法；禁止复述代码、禁止把改动历史写进注释。
4. 能力清单、字段枚举这类明细**不写进注释**——写进 `.agents/docs/<module>/**` 的模块文档。

## 4. 测试文件口径（`tests/**`）

测试文件是代码，不豁免；但字段填法有专门口径：

| 字段 | 填法 |
| --- | --- |
| 模块功能 | 这份用例保证什么行为（一句话），如「接口鉴权：未带 JWT 的业务路由必须 401」 |
| Python 调试 | `python -m pytest -c tests/pytest.ini tests/<路径>` |
| 时间 | 本模块头首次写 / 最近改写的日期 |
| 测试 | `1. 覆盖 <被测模块相对路径>`；一个用例文件守多个面就写多条，**不写**「本文件即用例」这种自指 |

## 5. 检查命令

```text
cd .agents/skills/engines-docstring-check
python -m scripts.docstrings check            # 默认：只查本次 git 改动（全仓在册范围），只报新引入
python -m scripts.docstrings check --all      # 全仓在册文件全量审计（存量清单）
python -m scripts.docstrings check --path utils
python -m scripts.docstrings check --all --summary   # 只出按规则聚合的计数（门禁用）
python -m scripts.docstrings read --changed   # 读代码前先取模块头 + 签名
```

- 退出码：`0` 无 error（`--strict` 时 warn 也算失败）；`1` 有 error。
- 本地门禁：`python -m utils.check_gates --only python-module-docstring`（当前为**非阻塞**告警项，存量清零后才议阻塞；`python -m run check` 会一并跑）。
- 覆盖范围是**可机械化子集**：4 字段齐全与格式、`测试` 编号连续、工具函数摘要 / `Args:`。
  「模块功能写得准不准」「行内 `#` 注释有没有价值」不检查，仍需人判断。

## 6. 存量迁移（分批，已完成批次见下）

| 批次 | 范围 | 状态 |
| --- | --- | --- |
| 1 | 规范 + 检查器 + 门禁 + `utils/**` + 根脚本 + engines 残留 | ✅ 已完成（2026-11-24） |
| 2 | `tests/**`（118 个；单元层已迁出到 `temps/`，不纳入） | ✅ 已完成（2026-11-24） |
| 3 | `backend/**` 非固定结构（58 个） | ✅ 已完成（2026-11-24） |

当前状态：`check --all --summary` = 328 个在册文件、**0 error**；Django 固定脚手架与 `temps/` 等按 §1.2 排除。

迁移铁律：**只重排注释，不改语义、不改代码**。现有自由格式 docstring 只取信息密度最高的**首句**升为 `模块功能`，
其余明细不搬（明细归模块文档）；`python -m` 入口按模块全名补；`时间` 写改写日期。
diff 里出现非 docstring 行 = 该文件重做。**工具函数的 docstring 一律逐字保留**（§3.2）。

## 7. 常见误写

| 误写 | 后果 |
| --- | --- |
| 只在开头写自由说明，不加 `➡️/🏁` | `有 docstring 但未使用➡️/🏁模板` + 4 个 `缺少字段` |
| `时间` 写 `2026/10/29` 或 `2026-10` | `时间格式应为 YYYY-MM-DD` |
| `Python 调试` 写 `pytest ...` 或 `见 README` | `Python 调试格式异常（期望 python -m …）` |
| `模块功能` 写 `1. xxx` 或 `python -m ...` | `模块功能 应是一句话职责` |
| `测试` 编号跳号（1. 3.） | `测试 编号不连续` |
| 给工具函数只写 `Args:` 不写首行摘要 | `工具 docstring 应以一句话摘要开头` |

## 8. 修订说明

- **2026-11-24**：范围从 `engines/**` 扩到全仓在册 Python 代码（排除 Django 固定脚手架与非产品代码）；
  模板正文从 `engines-code-style.md` §2 迁到本文件，engines 保留 §6 工具函数追加条款（范围同时从 `engines/agents/**` 更正为 `engines/ae_harness/tools/**`）。
  变更单：`openspec/changes/repo-wide-python-docstring`。
