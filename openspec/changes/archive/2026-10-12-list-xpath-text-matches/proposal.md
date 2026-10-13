## Why

同一 xpath 命中多个相同文本（例如多个 `ON`）时，`get_text` 只返回第一条，调用方无法知道还有哪些、该用哪个下标去点。

## What Changes

- `xpath_action` 的 `get_text` 列出该 xpath 的全部命中，每条带点击所用下标、文本和像素范围。
- 入参 `index` 仍然决定返回里的 `text` 取哪一条；`exists` / `click` / `long_click` 不变。
- 返回在原有 `text` 之外增加 `index`、`count`、`items`。已有只读 `text` 的调用方仍能取到该字段。

## 关联文档

无关联 PRD。这是设备 xpath 读文本的返回补全，便于同一页上多个相同文案按位置区分。

## Capabilities

### New Capabilities

### Modified Capabilities

- `ai-device-action`: `get_text` 必须列出全部命中并标出下标与坐标范围。

## Impact

- `engines/device/android/android_device.py`、`engines/device/android/__init__.py`、`engines/device/base.py`：列出命中。
- `engines/agents/tools/tool_device.py`、`engines/ai/tools/tool_device.py`、`apps/ai_assistant/tools.py`：`get_text` 走这份返回。
- 工具说明书与执行手册中的 `get_text` 返回约定。
- 测试：`tests/graybox/unit/test_xpath_text_matches.py`。不跑全量回归。
