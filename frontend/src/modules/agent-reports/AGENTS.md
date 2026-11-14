# agent-reports 模块 AGENTS.md

> **AGENTS 层级**：二级约束 —— 根 `AGENTS.md` 与上级 `frontend/AGENTS.md` 优先于本文件（本文件只写增量）。

## 职责

- `/agent-reports` 执行报告历史：列出 `logs/agents/backend_bridge/` 下的平台运行报告，点开查看 HTML 正文。
- 接口统一走 `api.ts` → `/api/ai/agent-reports/*`；**禁止**直连任务、报告生成或账本接口。

## 红线

| 只做 | 禁止 |
|------|------|
| 列报告、打开报告 | 在页面里解析报告内部结构或重算 token |
| 正文以 blob URL 新窗口打开 | 用 `v-html` 把报告注入当前页面（会污染全局样式与脚本） |
| 展示后端给的文件名与大小 | 前端拼路径、猜目录名或自己拼 `/logs/...` |

## 契约

- 列表 `GET /api/ai/agent-reports/?limit=` 返回 `{status, data: AgentReportRow[]}`，`data` 项含 `run/report/log/bytes/modified_at`。
- 详情 `GET /api/ai/agent-reports/{run}/{name}/` 返回 `{status, data: {run,name,content}}`，`content` 是完整 HTML。
- 后端对路径做白名单校验：越界 400、缺文件 404。前端**不得**传任意路径。

## 样式

- 走 Doodle Craft 默认：`WorkbenchHeader` + `DoodleNote`（列表条目）+ `DoodleBtn`；模块色 `--c-report`。
- 三态用共享件 `SkeletonCard` / `ErrorState` / `EmptyState`，加载期间不得渲染空态。
- 字号、间距、颜色只取 `shared/styles/tokens.css` 令牌。

## 快速验证

```bash
cd frontend
npx vitest run tests/agent-reports
npm run typecheck
npm run lint:styles
```
