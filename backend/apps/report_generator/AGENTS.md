# report_generator App AGENTS.md

> **AGENTS 层级**：二级约束 —— 根 `AGENTS.md` 与上级 `backend/apps/AGENTS.md` 优先于本文件（本文件只写增量）。

> 全局边界 / 协议要点 / 关单清单 → `../AGENTS.md`；本文只写本 App 增量，冲突以全局为准。

## 红线（全局索引表 report_generator 行的展开）

| 只做 | 禁止 |
|------|------|
| 报告只读列表 + 文件查看/下载 | 写业务数据（跨 App 写必须走对方 api） |
| `FileResponse` 下载报告文件 | 把文件内容塞进 JSON 信封 |
| 列表只读聚合可见 `task_list.Task`（`task_list/task_reports.py`） | import dashboard / ai_assistant / task_list 的 service、views |

- **列表数据源**：`GET /api/reports` 读当前用户可见的 `task_list.Task`（成功 = `completed`/`success`，失败 = `failed`）；不写 `task_tasks`。
- **详情**：任务事件流程归任务清单 `GET /api/tasks/{id}/report/`；本 App 不提供 Run 详情或用例分解端点。
- 下载/查看端点必须防路径穿越（`{filename}` 校验），现有 403/404 语义保持。

## 本 App 契约（特例 + 真相源）

真相源：`backend/apps/report_generator/urls.py`（3 端点：`""` / `{filename}/content` / `{filename}`）+ `views.py` + `api.py`（任务列表聚合读 `task_list.task_reports`）。2026-10-23 已删除 `cases` 与 `run/{run_id}` 两个空壳端点。

**响应信封**：`/reports/*` 的列表/内容统一为全局 `{status, data}`，业务负载放在 `data` 中，不再自带 `status`；错误为 `{status: false, message}` + 404。

- 下载走 `FileResponse`（`{filename}` 端点），前端用 `fetch().text()` 消费，**不套 JSON 信封**（附件语义，不算信封特例）。
- `{filename}/content` 为 JSON 内容查看端点（`data.content`）。

## 本 App 协议要点

无 WS / SSE。

## 关单附加项（全局清单的 delta）

```
[ ] 无 ORM 写业务表；只读查询 + 文件读取
[ ] 列表只读 task_list.Task + ai_assistant.api 只读函数，无 service import
[ ] 路径穿越防护：恶意 filename 返回 403/404（不落盘、不泄漏）
[ ] 响应为 `{status, data}` 标准信封；FileResponse 下载形态未变（前端按附件/文本读取）
```
