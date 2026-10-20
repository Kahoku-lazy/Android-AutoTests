## 代码编写要求

1. 模块与方法必须有注释，注释格式参考下文中的"注释格式模板"。

2. 相同业务功能封装在一个模块(`.py`)中, 例如 设备控制工具全部放在`engines/agents/tools/test_device.py`中；串口日志相关的放在了`engines/agents/tools/test_serial.py`中

3. 参考模块`engines/agents/role/config.py`中的编写方法，采用单一职责划分出模型配置，Agent角色配置与创建模型功能；一个模块（类、函数、组件）只做一件事，内部元素紧密相关，职责清晰；

4. **要保证**模块之间依赖尽量少、尽量简单。改一个地方，不容易牵连一大片

### 异常与 Raises 规则

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
