## Why

「哪些日志关键词能被识别、每个关键词对应哪个功能模块 / 功能点」目前只存在于数据文件与引擎代码里：想知道「某个关键词受不受支持」「某个功能点靠什么关键字判定」，得去翻 `config/device_log_keywords.json` 或读源码。日志证据（强证据 / 疑似周期）与只读日志查询工具都建立在这张表上，验收与排查时几乎每次都要对照它。需求方要求：在 AI 工具箱里给一个入口，直接看到当前支持筛选的日志关键词。

## What Changes

- AI 工具箱左侧「工具来源」新增来源**「日志关键词」**（与「设备提示词 / 无线端口 / 模型调试」同一形态：**无**「交给助手」总闸、不进生效芯片与未装配提示、不参与装配统计）。选中后右侧以**表格**展示关键词对照：三列为 `关键词 / 功能模块 / 功能点（#编号 + 名称）`，一行一个「关键词 × 功能点」（一个关键词对应多个功能点就是多行，现场约 70 行）；表格上方带搜索（关键词 / 模块 / 功能点都能搜），并显示关键词数、功能点数与行数。
- 新增只读端点 `GET /api/ai/log-keywords/`（登录可读，与「无线端口」列表同权限）：返回当前关键词对照表（关键词 → 功能点列表）、计数、**取值来源**（运行中的采集索引 / 配置文件）与文件更新时间。
- 面板**只读**：不提供任何编辑 / 上传 / 删除入口；改表仍由数据文件完成，面板如实标注「表改完后需重启平台才用于判定」。
- 前端把对照表拍成表格行与搜索过滤的纯函数实现并随单测锁定（**保持表内顺序**：关键词按表内先后、同一关键词的功能点按表内先后；前端不重排、不合并）。
- **BREAKING**：无（新增来源与只读端点；既有来源行的行为与文案不变）。

## 关联文档

- PRD-08（AI 助手 · 设备操控 · 工具箱）。
- 依据既有能力：`device-log-evidence`（关键词表是证据等级判定的真相源，其「改表不需改代码」口径不变）、`device-log-read-tool`（只读查询的关键词过滤同源于这张表）、`device-log-port-console`（同在工具箱的只读视图先例）。

## Capabilities

### New Capabilities

- `device-log-keyword-catalog`: 日志关键词对照表的只读视图——工具箱入口、表格内容与取值来源、列与顺序 / 搜索口径、只读约束与空态。

### Modified Capabilities

（无。既有能力的行为契约不变：本变更只新增一个只读视图与端点。）

## Impact

- 后端：新增 `apps/ai_assistant/log_keywords.py`（对照表读取与组装）、`views_log_keywords_drf.py`（只读端点）、`urls.py` 一条路由；不改动既有端点与信封。
- 引擎：只读消费 `engines/device/logbus.py` 的 `KeywordIndex`（不新增引擎行为）。
- 前端：`helpers/toolbox-assembly.ts`（新增来源定义）、`components/ToolboxPanel.vue`（按来源渲染新面板）、新增 `components/LogKeywordPanel.vue` + 样式、`composables/useLogKeywords.ts`、`helpers/log-keyword-rows.ts`（表格行 / 搜索纯函数）、`api/toolbox.ts`（取数）、`constants.ts`（文案常量）。
- 测试：`tests/graybox/unit/`（端点与组装口径、空态）、`frontend/tests/ai-assistant/p0/`（来源注册、表格行与搜索、面板渲染与只读）。
- 文档：AI 助手接口文档补该端点；`frontend/src/modules/ai-assistant/AGENTS.md` 的工具来源清单同步。
- 不改动：关键词表内容本身、证据等级与 5 秒窗口口径、只读日志查询工具、端口监听开关语义。
