## 1. 按组组装工具包

- [x] 1.1 给 `build_toolkit` 增加可开关组参数，顶层工具只进入常驻组；用一个不连设备的组装示例确认存在非常驻组时组开关已注册，且常驻组不含这些组里的工具
- [x] 1.2 在 `tools_config` 写明常驻工具与五个可开关组（`gesture`、`xpath`、`text_input`、`app`、`platform_business`）的说明、使用指引和成员，并提供每次返回新工具包的 `build_executor_toolkit()`；用未知工具名和跨组重名各组装一次，确认两次都失败且错误信息包含该名字

## 2. 技能登记到指定组

- [x] 2.1 `register_skills` 支持目标组；不传组时仍进入常驻组，传入不存在的组名时失败并带上组名，同一目录已在工具包任一组时不追加第二份。用 `tests/graybox/unit/` 中针对这三项的测试确认
- [x] 2.2 `engines/agents/role/executor.py` 在创建智能体前把执行技能名单登记到 `platform_business`，且常驻组没有该目录。构造执行角色后不调用 `start()`，用测试确认智能体尚未创建、目录只在 `platform_business`
- [x] 2.3 `engines/agents/agents.py` 的执行角色改为使用 `build_executor_toolkit()` 的新工具包，不再把 `engines/agents/skills/executor` 挂进常驻组。读组装结果确认常驻组技能来源为空

## 3. 执行提示词

- [x] 3.1 在 `EXECUTOR_PROMPT` 写明：用某组前先打开该组，一次组开关是全部可开关组的最终状态，截图和返回键不用打开。读提示词文本确认这三句都在

## 4. 分组可见性

- [x] 4.1 用 `tests/graybox/unit/test_executor_tool_groups.py` 覆盖规格场景：默认只见 `screenshot_page`、`press_key` 和组开关；分别只打开四个动作组时可见工具与规格一致；先打开 `gesture` 再只打开 `text_input` 后前者消失；打开 `platform_business` 才列出 `platform-tools-manual`，关闭时不列出。运行 `pytest tests/graybox/unit/test_executor_tool_groups.py` 与 `ruff check` 检查本次改动的 Python 文件，两者都通过
