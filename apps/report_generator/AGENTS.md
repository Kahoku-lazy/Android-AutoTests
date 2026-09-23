# report_generator App AGENTS.md

> **AGENTS 层级**：二级约束 —— 根 `AGENTS.md` 与上级 `apps/AGENTS.md` 优先于本文件（本文件只写增量）。

> 全局边界 / 协议要点 / 关单清单 → `../AGENTS.md`；本文只写本 App 增量，冲突以全局为准。

## 红线（全局索引表 report_generator 行的展开）

| 只做 | 禁止 |
|------|------|
| 报告只读列表/详情/分解 + 下载 | 写业务数据（跨 App 写必须走对方 api） |
| `FileResponse` 下载报告文件 | 把文件内容塞进 JSON 信封 |
| 列表只读聚合可见 `AITask`（`ai_task_reports.py`） | import dashboard / ai_assistant 的 service、views |

- **列表数据源**：`GET /api/reports` 读当前用户可见的 `AITask`（成功 = `completed`/`success`，失败 = `failed`）；不写 `ai_tasks`。
- **详情壳**：`/reports/run|task|cases` 仍为空壳（本变更不复活）。
- 下载/查看端点必须防路径穿越（`{filename}` 校验），现有 403/404 语义保持。

## 本 App 契约（特例 + 真相源）

真相源：`apps/report_generator/urls.py`（6 端点：`""` / `cases` / `run/{run_id}` / `task/{task_id}` / `{filename}/content` / `{filename}`）+ `views.py` + `ai_task_reports.py` + `api.py`。

**信封特例（legacy 平铺，禁止新增/改造）**：

- `/reports/*` 列表/详情响应为**平铺** `{status, ...}`（非全局 `{status, data}`），前端按平铺读取。
- 下载走 `FileResponse`（`{filename}` 端点），前端用 `fetch().text()` 消费，**不是 JSON 信封**。
- `{filename}/content` 为 HTML 内容查看端点。

## 本 App 协议要点

无 WS / SSE。

## 关单附加项（全局清单的 delta）

```
[ ] 无 ORM 写业务表；只读查询 + 文件读取
[ ] 列表只读 AITask + ai_assistant.api 只读函数，无 service import
[ ] 路径穿越防护：恶意 filename 返回 403/404（不落盘、不泄漏）
[ ] 平铺信封与 FileResponse 形态未变（前端按平铺/文本读取）
```
