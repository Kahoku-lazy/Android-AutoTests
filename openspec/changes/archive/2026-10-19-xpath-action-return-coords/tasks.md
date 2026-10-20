## 1. 查询实现

- [x] 1.1 将 `engines/agents/tools/tool_device.py` 的 `xpath_action` 收成 `serial` 与 `xpath`。经 `_execute` 且 `side_effect=False` 调用 `find_xpath`，按 0 / 1 / 多条裁成规格中的 JSON 文本，去掉 `resource_id`、`class_name`、`content_desc`。把 `xpath_action` 加入只读工具集合。说明改为获取页面 xpath 坐标，再用坐标点击控制。验证：`python -m ruff check engines/agents/tools/tool_device.py` 通过。

- [x] 1.2 为单条无下标、三条带下标 0/1/2、零条、查询成功时无 `action_time` 且不调用点击、连接失败返回 `error`、边框无法解析时 `x`/`y` 为 0 补单元测试。`tests/graybox` 已在工作区删除，测试落在 `tests/engines/agents/test_xpath_action_coords.py`。验证：`python -m pytest tests/engines/agents/test_xpath_action_coords.py -q` 通过。

## 2. 调用方与说明

- [x] 2.1 `tests/graybox/unit/test_device_log_check_tool.py` 已随 `tests/graybox` 在工作区删除，不再改那份旧对照。查询成功且没有 `action_time` 的断言由 1.2 的 `test_single_hit_has_no_index` 覆盖。

- [x] 2.2 更新 `engines/agents/tools_config.py` 的 xpath 组说明，以及 `engines/agents/skills/executor/platform-tools-manual/SKILL.md` 中 `xpath_action` 的用途、推荐序列和入参返回。写成先取 `x`/`y`，再调 `tap_screen`。组名保持 `xpath`。验证：上述两处不再把 `exists` / `get_text` / `click` / `long_click` 写成 `xpath_action` 的动作。
