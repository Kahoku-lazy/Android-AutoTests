## 1. 收成单文件

- [x] 1.1 重写 `engines/agents/tools/tool_device.py`：说明书放在函数 docstring，`_device` 统一开关连接，`device_tool_specs` 按原顺序从函数表生成。验证：`device_tool_specs()` 产出 9 个工具，名字与只读标记与原登记表一致，说明书首行与原文一致。
- [x] 1.2 删除 `engines/agents/tools/tool_device_catalog.py`。验证：该路径不存在，且 `engines/agents` 内不再 import 它；`engines/ai/tools/tool_device_catalog.py` 仍在。
- [x] 1.3 对 `engines/agents/tools/tool_device.py` 跑 `ruff check`。验证：退出码为 0。
