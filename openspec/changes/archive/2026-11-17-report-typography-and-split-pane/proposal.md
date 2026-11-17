## Why

需求方拿执行报告的截图对比平台「任务清单」页，提出三条：两处标题栏字体和平台不一致、正文字号偏小、左侧栏太窄且不能拖。三条都落在引擎侧的单文件报告渲染器 `engines/ae_harness/event/render.py`，与平台前端无关。

1. **字体**：报告里两处标题栏（侧栏 `AGENT可视化报告`、页头 `AGENT 执行报告`）声明的是平台品牌手写体 `Ziku FeiYang`，但 `@font-face` 的 `src` 写的是磁盘相对路径 `../../../../frontend/public/fonts/ziku-feiyang.ttf`。报告实际有三种打开方式，全是 `blob:` 文档（`frontend/src/modules/agent-reports/index.vue`、`task-list/components/TaskBoard.vue`、`bug-manager/components/BugDetailDrawer.vue` 都走 `URL.createObjectURL(new Blob(...))`），另外本地调试常直接 `file://` 打开。`blob:` 解析不了文件系统相对路径，字体请求失败后浏览器静默回落 `Noto Sans SC` —— 平台侧同一支字体正常，所以观感是「字体不一样」。
2. **字号**：`--app-size-xs`（12px）被当成正文在用（任务正文、验收事项、提示语、侧栏列表、结果 JSON、事件流字段），而平台口径里 12 只给列头 / 标签 / 时间戳 / Badge，正文是 `--app-size-sm`（14）。
3. **侧栏**：宽度写死 `260px`，1900px 宽的窗口里只占 14%，任务与验收事项被挤成窄条；也没有任何拖拽手柄。

## What Changes

- **品牌字体内联**：`@font-face` 的 `src` 改为 `data:font/ttf;base64,...`，与「品牌 logo 已内联成 base64」同一套做法；读不到字体文件时才回落原来的相对路径。
- **字号收成三档**：时间 / 日期 / 次数 / 耗时 / 标签 / Badge 保持 12，正文统一 14，标题与小标题（子目标标题、工具卡标题、图表卡标题、表头）统一 16。两处页面标题栏维持平台档位（侧栏品牌 20、页头 24），不压到 16。
- **侧栏默认三成宽 + 可拖**：`--side-w` 由 `260px` 改为 `30%`；侧栏与主区之间新增分栏手柄，契约照平台共享件 `shared/components/SplitHandle.vue`（下限 220px、上限 `min(760px, 容器宽 - 480px)`、拖拽期间 `col-resize` 且正文不可选、←/→ 16px / 按住 Shift 48px、Home / End 到两端、双击回默认），宽度落 `localStorage`；两栏退化成单栏（≤900px）时不渲染手柄。
- **不改**：报告的三层折叠契约、手绘序号、微倾卡片、事件流视图切换、颜色令牌、以及前端任何页面。

## 关联文档

无关联 PRD 编号。口径来源：`.agents/skills/doodle-craft/`（令牌与组件规格）+ `openspec/specs/frontend-split-pane`（分栏手柄契约）+ `openspec/specs/frontend-doodle-sketch-table` 的表格字号三档（16 / 14 / 12）。本变更把「单文件报告也要内联品牌字体」这条规则登记回 `references/standalone-html.md`。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `ae-harness-report-render`：新增「标题栏字体不依赖外部文件」「字号只有三档」「侧栏默认三成且可拖可键盘」三条呈现契约。

## Impact

- `engines/ae_harness/event/render.py`：`_brand_font_src()` 新增；`:root` 的 `--side-w` 与字号取值调整；`.splitter` 新增；`initSplitter()` 新增并初始化。
- 报告体积：每份 HTML 增加约 1.9MB（字体 1.45MB → base64）。现有报告已是 5–12MB（内联截图为主），相对增幅 16%~38%，换取「任何打开方式字体都正确」。
- `tests/engines/ae_harness/unit/test_report_render.py`：新增三条契约测试。
- `.agents/skills/doodle-craft/references/standalone-html.md`：登记单文件报告的品牌字体内联规则、字号三档与分栏手柄默认值。
- 不影响任何接口、数据库或前端页面；旧的报告文件不会自动重写。
