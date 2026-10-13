## Why

`engines/agents/tools/` 里设备工具被登记表和实现各写一遍，再用函数名字符串拼回去。登记字段大多没有读取方，改一个工具要动两个文件。

## What Changes

- 设备工具只保留 `tool_device.py`：说明书写在函数 docstring 上，`ToolSpec` 直接从函数表生成。
- 删除 `engines/agents/tools/tool_device_catalog.py`。
- 打开设备、执行、断开收成一个上下文；截图仍返回图片 dict，其余工具仍返回 JSON 字符串。
- 不改 `engines/ai/tools/` 下的同名副本，也不改工具对模型的可见名字、参数和返回形状。

## 关联文档

无关联需求编号。这是 `engines/agents/tools/` 内的纯重构，工具对外行为保持不变。

## Capabilities

### New Capabilities

### Modified Capabilities

## Impact

- 只改 `engines/agents/tools/tool_device.py`，并删除同目录的 `tool_device_catalog.py`。
- `engines/agents/tools_config.py` 仍调用 `device_tool_specs()`，签名不变。
- 现有单测覆盖的是 `engines/ai/tools/tool_device.py`，本变更不进入该路径。
