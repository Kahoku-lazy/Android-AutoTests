# device_inspector App AGENTS.md

> 全局边界 / 协议要点 / 关单清单 → `../AGENTS.md`；本文只写本 App 增量，冲突以全局为准。

## 职责与边界

**严禁**添加超出以下范围的功能设计。

1. 截图保留：抓取时页面截图落盘，快照存相对路径
2. dump 元素：XML 层级分析获取页面元素，数据内嵌截图 ID（`screenshot_id`）
3. OCR 元素：OCR 识别页面文本，数据内嵌截图 ID（`screenshot_id`）
4. 只读视图：提供 dump 元素 + 截图，前端按坐标绘制矩形高亮
5. 可选保存：筛减导入元素定位，只保存勾选的 dump/OCR 数据

**不做**：元素资产 CRUD（属 element_locator）；XPath / OCR / 布局算法（属 algorithms/）；WS 截图流。

## 注意事项

- 快照查询（详情 / 删除 / 分析 / 保存）**必须**按 `created_by=user_id` 过滤，禁止只按 id 查，否则越权。
- 保存到元素定位走 `element_locator.api.import_snapshot_page`，禁止本模块直接 ORM 写 `el_` 表。
- 引擎只经 `engines.device.registry` 工厂（`open_engine` / `close_engine`）消费，禁止 import `engines.device.android.*`、禁止访问裸句柄（`.u2` / `.airtest`）。
- 截图 ID 复用 `snapshot_id`：`dump_json` / `ocr_json` 顶层内嵌 `screenshot_id`，`screenshot_path` 为对应图片。
- 占用前缀 `_EXECUTION_OCCUPY_PREFIXES` 与 `device_pool.RUNNER_OCCUPIED_PREFIXES` 同口径，改动须两边同步。
- 截图流已快照化（REST），禁止恢复 WS 截图流。
