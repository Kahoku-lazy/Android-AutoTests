## Python代码编写要求

### 代码编写要求

1. 高内聚、低耦合、单一职责

2. 相同业务功能封装在一个模块(`.py`)中, 例如 adb 设备工具放在`engines/ae_harness/tools/adb/`，串口日志放在`engines/uart_log/`

3. 参考`engines/ae_harness/agents/models.py`（按调用方传入的连接参数造模型）与`engines/ae_harness/agents/creator.py`（只造智能体、不定义角色）的写法，一个模块（类、函数、组件）只做一件事，内部元素紧密相关，职责清晰；

4. **要保证**模块之间依赖尽量少、尽量简单。改一个地方，不容易牵连一大片