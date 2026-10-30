# engines 代码编写要求（规范原文）

本文是 engines 代码规范原文；**何时阅读由 `engines/AGENTS.md` 规定**，勿单独当作入口。

> 本文约束 `engines/` 下全部代码的**通用编写风格**。  
> 子目录若另有 `AGENTS.md`（如 `engines/agents/`、`engines/agents/rag/`），补充该领域规则。  
> **冲突时以更具体目录的 AGENTS 为准**；命名等已被子文档明确的条目，以子文档为准。  
> 写/改代码前的阅读与检查流程见 [`engines/AGENTS.md`](../../engines/AGENTS.md)；自动化检查用技能 [`.agents/skills/engines-agents-style-check/`](../skills/engines-agents-style-check/)。

## 1. 适用范围

| 层级 | 路径 | 本文哪几节生效 |
|------|------|----------------|
| 全 engines | `engines/**`（含 `agents`、`device`、`uart_log`、`vision` 等） | §2–§5、§7 |
| 仅 agents | `engines/agents/**` | 另加 §6（Agent / 工具 / Raises 专规） |

功能架构、目录职责、工具必须经 `tools_config` 分配等，见 [`engines/agents/AGENTS.md`](../../engines/agents/AGENTS.md)，本文不重复展开。

## 2. 注释与文档字符串（必须）

1. **模块与公开方法必须有 docstring**，格式见下文「注释格式模板」。
2. 模块 docstring 放在文件头：写明 `Python 调试`（`python -m …`）、模块用途、简介说明、关联本地模块与相关测试（格式见模板）。
3. 方法 docstring：首行一句话说明做什么；有参数写 `Args:`；有返回写 `Returns:`；有显式或文档化的失败面写 `Raises:`（细则见 §5 / §6）。

### 注释格式模板

```python
def method(self, content: str) -> None:
    """
    一句话说明这个方法做什么。

    Args:
        content: 参数说明。

    Returns:
        返回值说明。

    Raises:
        ValueError: 触发条件。
        RuntimeError: 触发条件。
    """
```

**模块 docstring 模板：**

```python
"""
文件名: ➡️ models_config.py 🏁
路径: ➡️ engines/agents/config/models_config.py 🏁
模块功能：➡️ 模型配置工具 🏁
Python 调试：➡️python -m engines.agents.config.models_config 🏁
时间：➡️ 2026-10-29 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-10-30 🏁
类型: ➡️ 模型配置模块 🏁
简介说明:➡️
1. ModelsConfig: 模型配置工具
🏁
关联模块:➡️
1. engines.xxx.yyy: 本模块使用的本地能力简述
🏁
测试:➡️
1. tests/.../test_xxx.py: 覆盖的测试项简述
🏁
"""
```
**注释解释说明**
1. ➡️ 是起止符号 🏁是结束符号；用于正则查找。例如当正则匹配到字段是“文件名”，就需要通过➡️🏁匹配这个“文件名”字段的内容。尤其是针对于“简介说明”“关联模块”“测试”这类字段，内容可以是多行编号列表，使用起止符号可以准确获取字段内容。
2. **Python 调试**：值为可直接复制的 `python -m …` 调试入口（不要再写「Python 调试运行入口：」等冗余前缀）。旧字段名「说明」已弃用，请改用本字段。
3. **关联模块**：列出本文件 `import` 的**本地**项目模块（如 `engines.*` / `utils.*`），并简要说明各导入用途；格式同「简介说明」（➡️…🏁 内编号列表）。
4. **测试**：写明相关测试代码路径，并精简概括测什么；格式同「简介说明」。
5. 「修改时间」可选；其余模板字段（含关联模块、测试）按检查器要求填写。
6. "类型"字段只允许从如下类型中选择
    - 工具模块: `engines/utils/` 中的模块都属于工具模块
    - 模型配置模块: 与模型配置相关的模块都属于模型配置模块
    - Harness 配置模块：与智能体配置相关的，例如tools，skill，mcp等模块相关的模块
    - Agent 能力模块：例如设备控制，视觉控制等模块就属于Agent能力模块

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

## 5. 异常与 Raises（通用）

1. **必须**：函数体内有显式 `raise` 的，其 docstring **必须**写 `Raises:` 段，并逐条写明异常类型与触发条件（与代码里的 `raise` 一一对应）。
2. 异常只用内置类型（`ValueError` / `RuntimeError` / `TypeError` / `SystemExit`）或仓库 / 框架**既有**类型（如 `DeveloperOrientedException`、`FrozenInstanceError`）。**禁止**在 engines 内随意新增自定义异常类；确有需要时先在对应子目录 AGENTS 中立项约定。
3. `Raises:` 段写在 `Returns:` 之后（无返回时可省略 `Returns:`，但仍保持 `Args:` → `Raises:` 顺序清晰）。

## 6. agents 专规（仅 `engines/agents/**`）

1. **公开入口**（如 `Agent.reply` / `reply_stream` / `interrupt`（及语音 session））即使自身不 `raise`，也**必须**把会穿透出去的内部异常写进 `Raises:`，便于调用方从签名处看到失败面。
2. **工具函数**（`tools/tool_*.py`）：docstring **首行摘要**是模型可见的工具说明（实测：AgentScope `FunctionTool` 只取首行摘要作 `description`、只取 `Args:` 作参数说明；`Raises:` 不进入模型侧）。因此：  
   - `Raises:` **必须**写在 `Returns:` 之后；  
   - **禁止**把 `Raises:` 插在首行摘要与 `Args:` 之间。
3. 工具文件命名、经 `tools_config.py` 分配、禁止业务代码直接 `import` 绑工具等，见 [`engines/agents/AGENTS.md`](../../engines/agents/AGENTS.md)。

## 7. 建议一并遵守（通用）

1. **类型注解**：新增 / 改动的公开函数与方法应标注参数与返回类型；逐步补齐旧代码，不做无关大扫除。
2. **日志**：用项目既有 logging 方式；避免在库代码里用 `print` 打业务日志。
3. **测试**：行为变更应有对应测试（优先既有 `tests/` 布局）；不要把测试文件塞进业务包当正式模块。
4. **功能开发**：涉及新能力或跨模块行为变更时，仍遵循仓库根目录 AGENTS / OpenSpec 流程（若根文档有要求）；**局部风格与 docstring 修复**可不走 OpenSpec，但不得借机扩大范围。
5. **本地风格检查**：按 [`engines/AGENTS.md`](../../engines/AGENTS.md)「AI 阅读与检查流程」使用技能 [`.agents/skills/engines-agents-style-check/`](../skills/engines-agents-style-check/)（`python -m scripts.check_engines_agents_style`）。检查器只覆盖机械化子集；过检 ≠ 整份规范合规。

## 8. 修订说明（相对旧版）

- 修正工具示例名为 `tool_device.py` / `tool_serial.py`，与 `engines/agents/AGENTS.md` 一致。  
- 区分全 `engines` 通用规则与 `agents` 专规。  
- 写明与子目录 `AGENTS.md` 的优先级。  
- 澄清「一域一文件」与「单一职责」的边界，避免互相打架。  
- 规范原文迁至本文件；何时阅读 / 何时用检查技能由 `engines/AGENTS.md` 规定。
