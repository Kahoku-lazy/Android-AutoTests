## Context

`HtmlReportRenderer` 产出的是**自包含单文件 HTML**（`engines/ae_harness/event/render.py`，CSS / JS 全内联）。它被三种方式消费：

| 打开方式 | 载体 | 相对路径可用？ |
| --- | --- | --- |
| 前端「执行报告」页 / 任务卡片 / BUG 抽屉 | `URL.createObjectURL(new Blob([html]))` → `blob:` 文档 | ❌ |
| 开发者本地调试 | `file://` | ✅ |
| 后端把文件直接吐出 | `FileResponse` 的 `text/html` | 取决于路由前缀 |

现状是 `@font-face` 的 `src` 写死相对路径，于是只有 `file://` 这一种能拿到 `Ziku FeiYang`，前端打开时字体静默失败 —— 而前端正是最常走的路径。这就是「两处标题栏字体和平台不一样」的全部成因。

字体之外还有两件事被顺带发现：`--app-size-xs` 被当正文用了（本该只给列头 / 标签 / 时间戳），侧栏宽度写死 260px 且没有手柄。

## Goals / Non-Goals

**Goals:**

- 两处标题栏在**任何打开方式**下都是平台品牌手写体。
- 报告文本只有 12 / 14 / 16 三档，语义按平台口径分配。
- 侧栏默认占三成，鼠标与键盘都能调，两栏退化时不渲染手柄。

**Non-Goals:**

- 不改报告的折叠契约、手绘序号、卡片微倾、事件流视图切换（都是既有验收项）。
- 不动前端任何页面与组件（`frontend/` 零改动）。
- 不回写历史报告：旧 HTML 保持原样，重新生成才生效。
- 不做字体子集化 / 按需裁字（见 D1 的取舍）。

## Decisions

**D1 品牌字体以 data URI 整体内联，不做子集化。**
`src: url("data:font/ttf;base64,...")`，读不到文件时回落原来的相对路径（保底可渲染）。备选三条被否：

| 备选 | 否掉原因 |
| --- | --- |
| 继续用相对路径 + 让前端补一个 `<base>` | `blob:` 文档的 base 仍是不可解析的伪路径；`file://` 又需要另一套 |
| 起一个后端路由吐字体、报告用绝对 URL 引用 | 引入跨源与部署前缀耦合，`file://` 打开直接失效 |
| 用 `pyftsubset` 裁出 13 个字形内联（约 +20KB） | 需要新增生成脚本与产物文件，标题文案一改就缺字回落，收益不值这个维护面 |

代价明确：每份报告 +约 1.9MB。现有报告 5–12MB（内联截图是主项），相对增幅 16%~38%，且报告是本地/内网读取的静态文件，可接受。

**D2 字号按「角色」分三档，不按「元素」逐个拍。**
口径与平台 `frontend-doodle-sketch-table` §1.1 的表格三档同源：

| 角色 | 令牌 | 落点 |
| --- | --- | --- |
| 时间 / 日期 / 次数 / 耗时 / 标签 / Badge | `--app-size-xs` (12) | `.t`、`.log-t`、`.call-m`、`.phase-h em`、`.k`、`.label`、`.badge`、`.log-badge`、`.pill`、`.no`、`.role-label`、`.legend`、`.tl-label` |
| 正文 | `--app-size-sm` (14) | `.task .v`、`.check-card li`、`.tip`、`.side-list`、`.token-card .row`、`.log-body`、`.code`、`.cpanel pre`、`details.kv pre`、`.note`、`.final` |
| 标题 / 小标题 | `--app-size-md` (16) | `.phase-h h3`、`.tool`（工具卡标题）、`.chart-card h4`、`table.marks th` |
| 页面标题栏（平台档位，不动） | `--app-size-lg` (20) / `--app-size-xl` (24) | `.brand-title` / `.wb-title` |

`.kpi strong`（20）是指标数字、不是文本，按展示级保留，不进这三档。

**D3 分栏手柄照抄平台 `SplitHandle.vue` 的契约，只把默认值换成三成。**
平台契约见 `openspec/specs/frontend-split-pane`；报告是 vanilla JS，因此复刻的是行为而不是组件：8px 命中区 + 居中 2px 线（常态 `--color-orange-76`，hover / 拖拽转 `--ink`）、`col-resize` + 正文不可选、16 / 48 步长、Home / End、双击复位、`role="separator"` + 三个 aria 值。

两处与平台不同，都是需求决定的：

1. **默认值**是「容器宽的 30%」而不是固定 280px —— 需求方明确要三成。
2. **上限**放宽到 760px（平台是 560px）。理由：30% 在 1920px 窗口就是 576px，沿用 560 会让「默认三成」在常见屏上被静默截断。

**D4 宽度持久化走 localStorage，失败即忽略。**
键 `agent-report-side-w`。`blob:` 文档继承创建者 origin，因此同一浏览器下各份报告共享同一宽度；`file://` 下访问可能抛异常，包一层 `try/catch` 后回落默认三成。

## Risks / Trade-offs

| 风险 | 影响 | 处置 |
| --- | --- | --- |
| 报告体积 +1.9MB | 落盘与经 API 传输变慢 | 已量化评估（16%~38%）；将来若不可接受，走 D1 的子集化路线 |
| 侧栏 30% 在 1280px 屏上只有 384px | 长验收事项换行变多 | 下限 220px 已可读；用户可拖窄 |
| 去掉侧栏 `border-right` 后分界变细（2px 暖灰） | 与新皮肤的手柄一致，但比原来 2.5px 墨线弱 | 手柄 hover / 拖拽转墨色给出反馈；如嫌弱可把 `::before` 常色改 `var(--ink)` |
| 拖拽宽度被记住，换小屏后再打开 | 宽度触上限被夹 | 每次 `apply` 都按当前容器重算上下限 |

## Migration

无需迁移。旧报告不重写；新报告天然带内联字体。前端零改动。

## Verification

1. `python -m pytest -c tests/pytest.ini tests/engines/ae_harness/unit/test_report_render.py -q` —— 三条新契约 + 八条既有折叠契约全过。
2. 内联脚本 `node --check` 通过（`initSplitter` 无语法错误）。
3. 人工：重新跑一次平台任务，从「执行报告」页打开，确认两处标题栏是手写体、正文变 14、侧栏占三成且能拖动。
