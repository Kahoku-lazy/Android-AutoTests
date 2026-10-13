# engines/agents 模块功能架构设计与代码规范文档

> AI在修改代码前**必须**先阅读此文档，**禁止跳过此文档规则直接编写代码**
> 术语说明：模块指的是`.py`文件； 类或者功能集合指的是`class`类； 函数、方法与计算公式指的是`def`.

## 代码目录规则

### 文件夹功能说明

1. `role`: **存放**智能体角色，所有角色创建都必须继承 `base.BaseRole`类
2. `prompts`: **存放**智能提示词，所有智能体角色的`system_prompt`, `user_prompt`用提示词额外配置，与`assistant_prompt`助手消息额外配置都在这个目录下存放。 模块名称模板`XXXX_prompt.py`其中XXX是角色名称。
3. `messaging`: **存放**对话稿与消息处理：对话落库（`dialogue.py`）、工具输出与用量费用解析、上屏渲染（`messages.py`）。
4. `tools`: **存放**智能体角色工具
5. `skills`: **存放**智能体角色skill技能
6. `mcp_config`:**存放**智能体角色mcp工具
7. `workflow`: **存放** SOP 步骤输入与单次运行。不在此目录创建角色，也不在此配置提示词或工具。

### engines/agents 根目录代码文件说明
1. `billing.py`: 费用计算相关功能放在这个模块(`.py`)，里面都是模型 Token 费用计算规则。
2. `prompt_config.py`: **配置**智能体提示词的模块，智能体角色提示词**必须**通过这个模块配置
3. `tools_config.py`: **配置**智能体工具的模块，智能体角色工具**必须**通过这个模块配置


## 业务功能编写规则

### 智能体工具配置

1. Agent所有的工具都**必须**放在tools目录下，需要按模块(`.py`)分组，文件名以`tool_xxx.py`格式命名。
- 例如 串口模块的工具名称是 `tool_serial.py`； 设备控制模块的名称是 `tool_device.py`

2. Agent的工具**必须** 通过`tools_config.py`分配给各个智能体，**禁止** 直接通过`import`方法配置工具。


## 异常与 Raises 规则

1. **必须**：函数体内有显式 `raise` 的，其 docstring **必须**写 `Raises:` 段，并逐条写明异常类型与触发条件（与代码里的 `raise` 一一对应）。
2. 异常只用内置类型（`ValueError` / `RuntimeError` / `TypeError` / `SystemExit`）或框架既有类型（`DeveloperOrientedException`、`FrozenInstanceError`）。**禁止**新增自定义异常类。
3. 公开入口（如 `BaseRole.reply` / `reply_stream` / `interrupt`）即使自身不 `raise`，也**必须**把穿透出去的内部异常写进 `Raises:`，便于调用方从签名处就能看到失败面。
4. 工具函数（`tools/tool_*.py`）的 docstring **首行摘要**是模型可见的工具说明（实测：AgentScope `FunctionTool` 只取首行摘要作 `description`、只取 `Args:` 段作参数说明；`Raises:` 段两者都不进）。因此 `Raises:` **必须**写在 `Returns:` 之后，**禁止**插在首行摘要与 `Args:` 之间。

### 注释格式模板

```python
def method(self, content: str):
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

**模块 docstring**（放在文件头，写明模块用途与包含的类 / 功能清单）：

```python
"""
python -m 调试路径: engines.agents.<子包>.<模块>

本模块的业务功能如下：
1. <类或功能名>: <一句话说明>。
"""
```

> **禁止**在 `"""` 后加空格：`ruff format` 会把它判为尾随空白。同理，docstring 内的空行**禁止**留缩进空格（写真正的空行）。仓库既有文件已按此清理。

