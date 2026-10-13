## Context

见 `proposal.md` 的 Why。`engines/agents/tools/tool_device.py` 用登记表里的函数名字符串查找实现，再把说明书写回函数 docstring。`name` 与 `impl` 始终相同。`Agent` 的工具参数来自真实函数签名。

## Goals / Non-Goals

**Goals:**

- 一个文件完成设备工具：函数、说明书、`ToolSpec`。
- 连接与断开只写一处。
- 工具名、参数、返回形状与现在一致。`ToolSpec` 顺序与原登记表一致。

**Non-Goals:**

- 不改 `engines/ai/tools/` 的同名文件。
- 不把函数再生成出来。签名必须留在源码里，供 AgentScope 生成参数。
- 不改截图返回 dict、其余动作返回 JSON 字符串这一差别。

## Decisions

1. 说明书放在函数 docstring 上。登记表删除。`device_tool_specs` 按固定名字顺序从 `build_device_tools` 取函数，只读集合只有 `screenshot_page`，`auto_allow` 一律为真。备选是继续留一份纯数据登记表，那会把同一工具写两遍。
2. `_device` 上下文负责打开和断开。动作失败与连接失败仍分开记日志、分开返回文案。截图失败返回仍是 `截屏失败：...`。
3. `xpath_action`、`tap_screen`、`app_control` 用分支表选择动作体，校验失败的文案保持原句。

## 模块防火墙自检

- 不新增跨 App import。设备调用仍走 `engines.device.action.open_device`。
- 无 INSERT/UPDATE/DELETE。
- 不改前端，不改 `apps/`。

## Risks / Trade-offs

- [工具顺序变化会改变模型看到的工具列表] → `build_device_tools` 按原登记表顺序组装。
- [说明书从登记表挪到 docstring 后漏抄] → 正文按原 `description` 原样搬迁。
