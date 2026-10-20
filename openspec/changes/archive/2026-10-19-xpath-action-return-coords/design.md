## Context

见 proposal.md 的 Why。`engines/agents/tools/tool_device.py` 的 `xpath_action` 仍按 `action` 分支做 `exists`、`get_text`、`click`、`long_click`。点击走元素点击，不走坐标。`find_xpath` 已经返回文本、边框和中心点。`tap_screen` 已能按像素坐标点击或长按。`engines/ai` 目录不在磁盘上。

## Goals / Non-Goals

**Goals:**

- 查询结果稳定成三种 JSON 形状，单条不带下标。
- 模型可见说明改为：先取坐标，再用 `tap_screen` 点击。

**Non-Goals:**

- 不改 `find_xpath` 的查找实现，不改 `tap_screen` / `click_ratio`。
- 不改 `executor-tool-groups` 的组成员：`xpath_action` 仍单独在 `xpath` 组。
- 不改历史迁移里的提示词快照，不恢复 `engines/ai`。

## Decisions

1. **入参只留 `serial` 和 `xpath`。**  
   `action`、`index`、`timeout` 删掉。下标由命中条数决定，不再由调用方传入。  
   备选：保留 `action=get_text`。否决原因是调用方仍会把它当成可点击工具。

2. **返回形状按条数分叉，字段从 `find_xpath` 里裁出。**  
   - 0 条：`{"count": 0, "items": []}`  
   - 1 条：`{"count": 1, "text", "x", "y", "bounds"}`，不写 `index`，不包 `items`  
   - 多条：`{"count": N, "items": [{"index", "text", "x", "y", "bounds"}, ...]}`  
   `x`、`y` 用已有中心点。不返回 `resource_id`、`class_name`、`content_desc`。单条也带 `count`，方便调用方先分支。  
   备选：一律放进 `items`，单条省略 `index`。否决原因是已确认单条为扁平对象。  
   备选：把 JSON 写到磁盘再返回路径。否决原因是模型要直接读内容，现有工具返回的就是 JSON 文本。

3. **查询走现有 `_execute`，`side_effect=False`。**  
   因此成功返回不带 `action_time`，也不附带前台应用。`xpath_action` 加入只读工具集合。点击和长按仍由 `tap_screen(serial, mode, x, y)` 用这里的 `x`、`y` 完成。  
   备选：在本工具里查完坐标再调用 `Click.by_coord`。否决原因是本工具不再执行操作。

4. **说明与组文案一起改，函数名不改。**  
   docstring、`tools_config.py` 的 xpath 组 `description` / `instructions`、执行手册里「xpath 直接点击」的句子，改成获取坐标后用坐标点击。组标识仍是 `xpath`。  
   备选：改名为 `xpath_query`。否决原因是工具组和已有登记都认 `xpath_action`。

## 模块防火墙自检

- 改动停在 `engines/agents` 的工具、组说明和技能手册，外加对拍这条行为的单元测试。
- 不新增跨 App import，不写库，不改前端，不碰仪表盘。
- 工具继续经 `engines.device.action` 取数，不直接使用 uiautomator2 句柄。

## Risks / Trade-offs

- [旧调用仍传 `action`] → 同步改执行手册、组说明和 `test_device_log_check_tool.py` 的只读对照；签名不匹配时由工具参数校验失败，而不是静默点到元素。
- [单条和多条形状不同] → 规格和手册各写一种例子；调用方先看 `count`。
- [边框解析失败时中心点为 0] → 沿用 `find_xpath` 的现有口径，`bounds` 原样返回，避免在工具层再发明一套坐标。

## Migration Plan

无数据迁移。发布即替换工具契约。回滚时恢复 `xpath_action` 的四个动作分支，并还原组说明与手册。
