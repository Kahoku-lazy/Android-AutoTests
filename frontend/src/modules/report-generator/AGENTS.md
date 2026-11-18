# report-generator 模块 AGENTS.md

> **AGENTS 层级**：二级约束 —— 根 `AGENTS.md` 与上级 `frontend/AGENTS.md` 优先于本文件（本文件只写增量）。

> 全局边界 / 模板样式 / 协议要点 / 关单清单 → `../../AGENTS.md`；本文只写本模块增量，冲突以全局为准。

## 红线（全局表 report-generator 行的展开）

| 只做 | 禁止 |
|------|------|
| 报告台账列表 / 报告数量 KPI / 来源筛选 | 写业务数据；复活通过率趋势与任务卡列表 |
| 行点击打开已生成的 HTML 报告（复用既有读取通道） | 新拼报告读取地址；注册 `/reports/:id` 或用例分解路由 |
| 侧栏「AI任务」组第四项（BUG单管理之后） | 直打 `/api/tasks/*` 或 `/api/ai/*` 的任务接口 |

- **列表一行 = 一份已生成的报告**：SOP 行身份列显示用例名称 + 任务编号；智能体行显示助手名称 + 编号。未执行/执行中/取消/中断不入列。
- **查看报告按来源分流**：SOP 行复用 `task-list/api/tasks.ts` 的 `fetchTaskReport`（blob 新标签）；智能体行复用 `ai-assistant/api/assistants.ts` 的 `issueLogTicket + threadLogUrl`（ticket 直开）。跨模块复用对方 api.ts 导出是既有模式（bug-manager 先例），**禁止**在本模块另拼地址。
- 本模块只有 `/reports` 一条路由；`/reports/:runId`、`/reports/cases/:type` 与孤儿模块 `agent-reports` 均已退役，**禁止复活**。
- 旧 csv/md 下载（`fetch().text()`）随旧端点退役；本模块不再有文件下载语义。

## 本模块契约

**响应信封（全局 `{status, data}`）**：`GET /reports/` 的 `data` 含 `summary`（`total_reports/sop_reports/agent_reports`）、`total`、`items`；过滤参数 `source/keyword/start_date/end_date`。KPI 与筛选计数一律取 `summary`，**禁止**前端对行自行汇总。

- 列表：`api.ts` 的 `listReports`（唯一 HTTP 出口）。
- 行展示派生：`helpers/report-row.ts` 纯函数；文案/列定义/分页：`constants.ts` 唯一真相源。

## 本模块特殊布局/样式（`constants.ts` 为唯一真相源）

- 版式照 BUG 单工作台：WorkbenchHeader + 「报告概览」KPI 三卡 + 「测试报告」分区（FilterTabs 来源筛选 + 关键字/日期 + AppTable 单表 + 前端分页）。
- 模块色 `--c-report`；表纸渐变、徽标、翻页键色值全部取 tokens.css 令牌，去抖 `FILTER_DEBOUNCE`。
- 空态文案：报告在执行完成后生成，引导任务清单 / 平台助手，不提执行引擎。

## 关单附加项（全局清单的 delta）

```
[ ] 常量/文案经 constants.ts，无新魔法字符串
[ ] 报告只读：无写业务数据调用；行点击打开报告文件，路由停留 /reports
[ ] 查看报告复用既有通道，未新拼地址
[ ] npx vitest run tests/report-generator tests/shared/p0/sidebarNavConfig.spec.ts
```
