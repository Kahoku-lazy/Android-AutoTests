## Why

`xpath_action` 现在会直接对命中元素做存在检查、读文本、点击或长按。同一 xpath 命中多个元素时，模型要先选下标再点元素，点偏后无法改用已经算出的中心坐标。需要把它收成只查询，查出文本和坐标后再用坐标点击。

## What Changes

- **BREAKING** `xpath_action` 不再接受 `action`、`index`、`timeout`，也不再执行 `exists` / `get_text` / `click` / `long_click`。
- 入参只保留 `serial` 与 `xpath`。工具按 xpath 查出元素文本和中心坐标，以 JSON 字符串返回，不写磁盘文件，不产生点击。
- 命中 1 条时返回该条的 `text`、`x`、`y`、`bounds`，不写下标。命中多条时放入 `items`，下标从 0 起。没有命中时 `count` 为 0、`items` 为空列表。
- 点击和长按改用返回的像素坐标调用 `tap_screen`。工具名保持 `xpath_action`，仍在 `xpath` 组。

## 关联文档

无关联 PRD。这是执行角色设备工具的行为收口，范围已在当次讨论中确认。

## Capabilities

### New Capabilities

### Modified Capabilities

- `ai-device-action`: `xpath_action` 从「按动作读文本或点击」改为「只返回文本与坐标」。原「读取文本时列出全部命中，且存在检查、点击、长按不变」的要求被替换。

## Impact

- `engines/agents/tools/tool_device.py`：`xpath_action` 的入参、说明和返回。
- `engines/agents/tools_config.py`：xpath 组说明改为获取坐标，点击交给坐标工具。
- `engines/agents/skills/executor/platform-tools-manual/SKILL.md`：去掉用 xpath 直接点击的约定。
- `tests/graybox/unit/test_device_log_check_tool.py`：只读对照调用要改成新入参，并断言查询结果没有 `action_time`。
- 不改历史迁移里的旧提示词快照。`engines/ai` 已不在磁盘上，不在本次范围内。
