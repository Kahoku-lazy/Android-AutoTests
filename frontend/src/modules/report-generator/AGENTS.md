# report-generator 模块 AGENTS.md

> **AGENTS 层级**：二级约束 —— 根 `AGENTS.md` 与上级 `frontend/AGENTS.md` 优先于本文件（本文件只写增量）。

> 全局边界 / 模板样式 / 协议要点 / 关单清单 → `../../AGENTS.md`；本文只写本模块增量，冲突以全局为准。

## 红线（全局表 report-generator 行的展开）

| 只做 | 禁止 |
|------|------|
| 报告列表/KPI/趋势（任务卡）/文件下载 | 写业务数据 / 下载走 JSON api（用 FileResponse `fetch().text()`） |
| 列表行纯展示，不跳 `/reports/:id` 或用例分解 | 直打 `/ai/agent-tasks`（须走本模块 `api.ts` → `/reports`） |

- **报告下载是 FileResponse 非 JSON，必须用 `fetch().text()` 而非 `api()`**，否则报告内容乱码。
- `STATUS_LABEL_MAP` 双口径（`api.ts` 与 `constants.ts` 各一份）是已登记收敛项，**禁止新增第三份映射**。
- 列表一行 = 一张可见 AI 助手任务卡；任务 ID 纯文本，本页不跳转详情。

## 本模块契约

**信封特例（非全局 `{status, data}`）**：`/reports/*` 响应为**平铺**、各端点结构不同（列表 `{status, summary, trend, runs}`、详情 `{status, run:{}}`、任务 `{status, task:{}}`），前端按端点结构读取。列表 `runs[]` 为任务卡字段（无 `case_count`/`passed`/`failed`/`rate`）。

- 列表：`GET /reports`（数据源 AITask）
- 详情 / 用例分解 / 任务视角：仍可请求，后端多为空壳
- 内容（JSON api）：`GET /reports/{filename}/content`；**下载 URL**：`/api/reports/{filename}`（FileResponse，`fetch().text()`）

## 本模块特殊布局/样式（`constants.ts` 为唯一真相源）

- 表格布局尺寸 `TABLE_*`、图表配置 `CHART_*`（色值走 `CHART_COLORS`，JS 画布例外）、去抖 `FILTER_DEBOUNCE`/`CHART_RESIZE_DEBOUNCE`、阈值 `PASS_RATE_*`
- 空态 / 页头文案：`EMPTY_TEXT` / `PAGE_HEADER`（指向 AI 助手，不提执行引擎）

## 关单附加项（全局清单的 delta）

```
[ ] 文件下载走 fetch().text()，未误用 JSON api()
[ ] STATUS_LABEL_MAP 双口径未新增第三份映射
[ ] 常量/阈值经 constants.ts，无新魔法字符串
[ ] 报告只读：无写业务数据调用；列表不跳转详情
```
