## Context

OCR 的底层能力在 `utils.vision.ocr.recognize`（L1a 算法层），截图在 `engines.device.action.Screenshot`；上一单删除的平台侧实现只是把两者串起来并调用 `apps.device_inspector.api.ocr_screen`。引擎要保留同一能力，必须绕开 `apps` 依赖（引擎不得反向 import 应用层）。

## Goals / Non-Goals

**Goals:**

- 在 `engines/agents/tools` 内提供一个可复用的只读 OCR 工具，语义与删除前一致（文本 / 置信度 / 角点 / 归一化中心点，支持多文本过滤）。
- 用测试锁死「实现存在但不装配」这一边界，防止后续被误加进角色工具集。

**Non-Goals:**

- 不改变执行/验收角色的工具集（`tools_config.py` 一行不改）。
- 不恢复平台侧工具注册表、工具箱或内部网关。
- 不新增 API、不落库、不改前端。

## Decisions

**D1 独立模块 `tool_ocr.py`，不并入 `tool_device.py`。**
OCR 是识别类只读能力，不产生设备副作用；独立模块能直白表达「存在但不装配」，也避免给 `tool_device` 增加一个永远不被角色使用的工具。备选：并入 `tool_device`——会让 `build_device_tools()` 自动带上 OCR，等于变相装配，否决。

**D2 引擎自给自足：`Screenshot` + `utils.vision.ocr.recognize`，禁止 import `apps`。**
删除前的实现经 `apps.device_inspector.api.ocr_screen` 取数，方向错误；新实现直接用引擎截图与算法层 OCR。备选：把检测器服务搬进引擎——超范围，不做。

**D3 `PIL` 与 `cnocr` 惰性导入。**
`utils.vision.ocr` 在模块顶部 import cnocr；若 `tool_ocr` 顶层 import 它，引擎任何模块导入都会拉起重依赖。识别函数内部再 import，保持引擎导入轻量。

**D4 不装配由测试守护，而不是靠注释。**
`tests/engines/agents/test_ocr_tool.py` 断言规格存在且只读、并且 `EXECUTOR_BASIC_TOOL_NAMES`、`VERIFIER_BASIC_TOOL_NAMES` 与全部 `ToolGroupSpec.tool_names` 都不含 `ocr_page`。

**D5 截图落盘复用 `Screenshot.save(keep_local=True)`。**
返回 `screenshot_path` / `screenshot_name` 便于人工复核；工具未被装配，不会产生任务级副作用。

## 模块防火墙自检

- 跨 App import：无（`engines` 不 import `apps`）。
- 引擎边界：只用 `engines.device.action` 与 `utils.vision`，不触碰 airtest/u2 裸句柄。
- 写库：无。
- 前端：无。

## Risks / Trade-offs

- [cnocr 首次调用会下载模型] → 属既有 OCR 行为；工具未被装配，正常任务不会触发。
- [截图落盘占用空间] → 与 `screenshot_page` 同一落盘策略，人工清理即可。
- [未来有人把工具加进角色工具集] → 单测直接失败。
- [识别结果与删除前的实现有细微差异] → 过滤与归一化口径照抄原实现（逗号/顿号/换行分隔、忽略大小写、按截图尺寸归一化），并有纯函数单测。

## Migration Plan

无数据迁移。回滚 = 删除 `tool_ocr.py` 与其测试。
