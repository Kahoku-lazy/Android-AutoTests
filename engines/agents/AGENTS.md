# engines/agents 模块功能架构设计与代码规范文档

> AI在修改代码前**必须**先阅读此文档，**禁止跳过此文档规则直接编写代码**
> 术语说明：模块指的是`.py`文件； 类或者功能集合指的是`class`类； 函数、方法与计算公式指的是`def`.

## 代码目录规则

### 文件夹功能说明

1. `role`: **存放**智能体角色，所有角色创建都必须继承 `base.BaseRole`类
2. `prompts`: **存放**智能提示词，所有智能体角色的`system_prompt`, `user_prompt`用提示词额外配置，与`assistant_prompt`助手消息额外配置都在这个目录下存放。 模块名称模板`XXXX_prompt.py`其中XXX是角色名称。
3. `messaging`: **存放**事件日志与费用：事件上屏（`messages.py` 的 `AgentEventsShow`）、事件折叠（`fold.py`，只产日志行和记录，不写库）、结构化记录（`record.py`）、模型 Token 费用（`billing.py`）。接收方协议在 `event_sink.py`，默认丢弃记录。
4. `tools`: **存放**智能体角色工具
5. `skills`: **存放**智能体角色skill技能
6. `mcp_config`:**存放**智能体角色mcp工具
7. `workflow`: **存放** SOP 步骤输入与单次运行。不在此目录创建角色，也不在此配置提示词或工具。

### engines/agents 根目录代码文件说明
1. `prompt_config.py`: **配置**智能体提示词的模块，智能体角色提示词**必须**通过这个模块配置
2. `tools_config.py`: **配置**智能体工具的模块，智能体角色工具**必须**通过这个模块配置


## 业务功能编写规则

### 智能体工具配置

1. Agent所有的工具都**必须**放在tools目录下，需要按模块(`.py`)分组，文件名以`tool_xxx.py`格式命名。
- 例如 串口模块的工具名称是 `tool_serial.py`； 设备控制模块的名称是 `tool_device.py`

2. Agent的工具**必须** 通过`tools_config.py`分配给各个智能体，**禁止** 直接通过`import`方法配置工具。