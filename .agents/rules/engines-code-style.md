# engines 代码编写要求（规范原文）

本文是 engines 代码规范原文；**何时阅读由 `engines/AGENTS.md` 规定**，勿单独当作入口。

> 本文约束 `engines/` 下全部代码的**通用编写风格**。  
> 子目录若另有 `AGENTS.md`（如 `engines/agents/`、`engines/agents/rag/`），补充该领域规则。  
> **冲突时以更具体目录的 AGENTS 为准**；命名等已被子文档明确的条目，以子文档为准。  
> 写/改代码前的阅读与检查流程见 [`engines/AGENTS.md`](../../engines/AGENTS.md)；自动化检查用技能：注释/docstring → [`.agents/skills/engines-docstring-check/`](../skills/engines-docstring-check/)，命名 / 禁 import → [`.agents/skills/engines-agents-style-check/`](../skills/engines-agents-style-check/)。

## 1. 适用范围

| 层级 | 路径 | 本文哪几节生效 |
|------|------|----------------|
| 全 engines | `engines/**`（含 `agents`、`device`、`uart_log`、`vision` 等） | §2–§5、§7 |
| 仅 agents | `engines/agents/**` | 另加 §6（工具函数注释专规） |

功能架构、目录职责、工具必须经 `tools_config` 分配等，见 [`engines/agents/AGENTS.md`](../../engines/agents/AGENTS.md)，本文不重复展开。

## 2. 注释与文档字符串（极简版：只保留模块头 4 字段）

> 本节里**能机械化**的部分（模块头 4 字段、工具函数「首行摘要 + `Args:`」）由技能 [`.agents/skills/engines-docstring-check/`](../skills/engines-docstring-check/) 校验；注释文案是否准确仍需人判断。

1. **只有模块开头的文件头注释**：每个 `.py` 文件开头写一个模块 docstring，字段严格按下方模板，**不得增加模板以外的字段**。
2. **其余位置默认不写注释**：类 docstring、普通函数 / 方法 docstring、函数体内的 `#` 行内注释，没有明确要求就**不写**。
3. **唯一例外——工具函数**：会被 `FunctionTool(...)` 注册、把说明交给模型看的函数（`engines/ae_harness/tools/**` 等）必须写 docstring，且只写「首行一句话摘要 + `Args:`」；`Args:` 每个参数一行说明。工具函数**不再要求** `Returns:` / `Raises:`（保留不报错，但不要为凑段而写）。
4. 确需解释「**为什么**这么写」（非显然的协议约束、顺序敏感的实现细节）时，允许在该行上方写**一行**短注释，只写原因、不写做法；**禁止**复述代码、**禁止**把改动历史写进注释。

### 模块头模板（唯一允许的字段）

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

**字段说明**（➡️ 是起始符、🏁 是结束符，用于正则取字段内容）：

| 字段 | 必填 | 取值要求 |
| --- | --- | --- |
| 模块功能 | 是 | 一句话职责；不写编号、不写调试命令 |
| Python 调试 | 是 | 可直接复制的 `python -m …` 入口，不加任何前缀 |
| 时间 | 是 | `YYYY-MM-DD` |
| 测试 | 是 | 测试文件路径 + 覆盖项，一行一条、从 `1.` 连续编号；确实没有测试写「1. 暂无」 |

**已删除、不要再写的字段**：`文件名`、`路径`、`作者`、`版本`、`修改时间`、`类型`、`简介说明`、`关联模块`。  
历史文件里的这些字段不要求立刻删除（本次不迁移存量）；新写或改写的文件头只保留上表 4 个字段。

## 3. 模块划分与单一职责

1. **按业务域归文件**：同一业务能力放在同一个模块（`.py`）中，避免同域逻辑散落多处。  
   - agents 工具命名与归位以 [`engines/agents/AGENTS.md`](../../engines/agents/AGENTS.md) 为准：文件名 `tool_xxx.py`（例如 `tool_device.py`、`tool_serial.py`），放在 `engines/agents/tools/`。  
   - **禁止**再使用已废弃示例名 `test_device.py` / `test_serial.py`。
2. **文件内再拆职责**：一个类 / 函数 / 组件只做一件事，内部元素紧密相关。可参考 `engines/agents/config.py`：模型配置、Agent 角色配置、创建模型功能分开，而不是堆进一个巨类。
3. **边界口诀**：  
   - 允许：一个 `.py` = 一个业务域，内部多个小类/函数各司其职。  
   - 禁止：无关业务塞进同一文件；禁止「为拆而拆」导致改一处要改十个文件。

## 4. 依赖与耦合

1. **模块之间依赖尽量少、尽量简单**；改一处不应轻易牵连一大片。
2. 优先依赖稳定、靠近本域的接口；避免循环导入与跨层乱引用。
3. 新增跨包依赖前，先确认是否已有配置入口或门面（agents 侧如 `role_sys_prompts` / `tools_config` / `config.models`）。

## 5. 异常（通用）

1. 异常只用内置类型（`ValueError` / `RuntimeError` / `TypeError` / `SystemExit`）或仓库 / 框架**既有**类型（如 `DeveloperOrientedException`、`FrozenInstanceError`）。
2. **禁止**在 engines 内随意新增自定义异常类；确有需要时先在对应子目录 AGENTS 中立项约定。
3. **不再要求**把 `raise` 写进 docstring 的 `Raises:` 段（与 §2.2「其余位置默认不写注释」一致）；失败面由异常类型本身与工具返回契约表达。

## 6. agents 专规（仅 `engines/agents/**`）

1. **工具函数**（`tools/tool_*.py`）：docstring **首行摘要**就是模型可见的工具说明（实测：AgentScope `FunctionTool` 取首行摘要作 `description`、取 `Args:` 作参数说明；`Raises:` 不进入模型侧）。因此工具函数**必须**写「首行摘要 + `Args:`」，`Args:` 覆盖每个参数。
2. **公开入口**（如 `Agent.reply` / `reply_stream` / `interrupt`（及语音 session））：按 §2.2 不写 docstring；失败面由异常类型表达，不再要求 `Raises:`。
3. 工具文件命名、经 `tools_config.py` 分配、禁止业务代码直接 `import` 绑工具等，见 [`engines/agents/AGENTS.md`](../../engines/agents/AGENTS.md)。

## 7. 建议一并遵守（通用）

1. **类型注解**：新增 / 改动的公开函数与方法应标注参数与返回类型；逐步补齐旧代码，不做无关大扫除。
2. **日志**：用项目既有 logging 方式；避免在库代码里用 `print` 打业务日志。
3. **测试**：行为变更应有对应测试（优先既有 `tests/` 布局）；不要把测试文件塞进业务包当正式模块。
4. **功能开发**：涉及新能力或跨模块行为变更时，仍遵循仓库根目录 AGENTS / OpenSpec 流程（若根文档有要求）；**局部风格与 docstring 修复**可不走 OpenSpec，但不得借机扩大范围。
5. **本地风格检查**：按 [`engines/AGENTS.md`](../../engines/AGENTS.md)「AI 阅读与检查流程」使用技能 [`.agents/skills/engines-docstring-check/`](../skills/engines-docstring-check/)（`python -m scripts.docstrings check`，查注释/docstring 合规）与 [`.agents/skills/engines-agents-style-check/`](../skills/engines-agents-style-check/)（`python -m scripts.check_engines_agents_style`，查命名 / 禁 import）。两个检查器都只覆盖机械化子集；过检 ≠ 整份规范合规。

## 8. 修订说明（相对旧版）

- **2026-11-24 注释收敛**：模块头只保留 4 字段（模块功能 / Python 调试 / 时间 / 测试），删除 `文件名`、`路径`、`作者`、`版本`、`修改时间`、`类型`、`简介说明`、`关联模块`；函数 / 类 / 行内注释默认不写，仅工具函数保留「首行摘要 + `Args:`」；`Raises:` 不再强制。存量代码不迁移，检查器只对新写 / 改动的文件生效。
- 修正工具示例名为 `tool_device.py` / `tool_serial.py`，与 `engines/agents/AGENTS.md` 一致。  
- 区分全 `engines` 通用规则与 `agents` 专规。  
- 写明与子目录 `AGENTS.md` 的优先级。  
- 澄清「一域一文件」与「单一职责」的边界，避免互相打架。  
- 规范原文迁至本文件；何时阅读 / 何时用检查技能由 `engines/AGENTS.md` 规定。
