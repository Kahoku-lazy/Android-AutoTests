# report_generator · 报告只读台账

> 归属模块：`backend/apps/report_generator` ｜ 类型：模块功能开发说明
> 代码真相源：`backend/apps/report_generator/urls.py`（1 端点：`""`）、`views.py`、`report_inventory.py`
> 上级约束：`backend/AGENTS.md` ｜ 模块索引：`backend/apps/AGENTS.md`

## 红线

| 只做 | 禁止 |
|------|------|
| 已生成报告的只读台账（`report_inventory.py` 聚合） | 写业务数据（跨 App 写必须走对方 api） |
| 只读 `task_list.Task` 与 `ai_assistant` 三张 Model、`task_list.case_identity` 纯函数 | import dashboard / ai_assistant / task_list 的 service、views、runner |
| 列表统计报告数量（总数 / SOP / 智能体） | 扫磁盘目录发现报告；统计任务通过率或趋势 |

## 列表数据源

`GET /api/reports` 返回已生成的报告——SOP 报告取带 `report_run/report_name` 定位的终态任务；
智能体报告取带 `report_id` 的助手消息（仅正常完成轮次）。未执行/执行中/取消/中断不入列。
**不写任何业务表。**

- **限量**：遵守 `platform-load-budget`——每来源扫描 ≤1000、合并返回 ≤500；不联表读智能体大字段。
- **报告正文读取不在本 App**：SOP 走 `ai_assistant` 的 `/api/ai/agent-reports/{run}/{name}/`；
  智能体走对话栏日志 ticket 通道。本 App 不提供文件下载/查看端点。
- 旧 csv/md 文件端点（`{filename}` / `{filename}/content`）、`rg_reports` / `rg_report_templates` 表
  与 `ReportGenerator` / `save_report` 已随 rework-test-report-inventory 退役，**禁止复活**。

## 响应契约

`/api/reports/` 统一为全局 `{status, data}`：`data` 含 `summary`（`total_reports/sop_reports/agent_reports`）、
`total`、`items`；错误为 `{status: false, message}`。
`/api/reports/cases/`、`/api/reports/run/{run_id}/`、`/api/reports/{filename}*` 一律 404。

**行字段**：SOP 行带 `report_run/report_name/task_id/task_title/case_label/device/status/started_at/finished_at/duration`；
智能体行带 `assistant_id/assistant_name/thread_id/report_id/summary/created_at`。
`case_label` 只由冻结用例身份算出（与任务清单、BUG 单同口径）。

## 协议要点

无 WS / SSE。

## 关单附加项（全局清单的 delta）

```
[ ] 无 ORM 写业务表；只读查询，无磁盘扫描
[ ] 列表只读 task_list.Task + ai_assistant Model + case_identity 纯函数，无 service/views import
[ ] 响应为 `{status, data}` 标准信封；summary 统计报告数量
[ ] python -m pytest -c tests/pytest.ini tests/report
```
