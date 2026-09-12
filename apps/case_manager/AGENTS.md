# case_manager App AGENTS.md

> 全局边界 / 协议要点 / 关单清单 → `../AGENTS.md`；本文只写本 App 增量，冲突以全局为准。
> 版本：v2.1 · 最后更新：2026-09-09 · v2.1：CaseFile 表格页；树仅目录/文件。

## 红线（全局索引表 case_manager 行的展开）

| 只做 | 禁止 |
|------|------|
| 项目 / 无限目录 / 文件(CaseFile) / 文档型用例行 CRUD | 执行完整任务；恢复四类型可执行步骤编辑器 |
| 写操作经 `api.py`（`api_projects` / `api_directories` / `api_files` / `api_definitions`） | View 直接 ORM 写；跨 App 写本表绕过 api |

- 用例为**文档型**：`steps` / `expected_result` 为独立文本，不驱动 `test_runner`。
- 树叶子是 **文件**，不是单条用例；用例行挂在 `file` 下。
- 目录归属 `CaseProject`，不限层级；禁止拖入自身子孙（409）。

## 本 App 契约（特例 + 真相源）

真相源：`apps/case_manager/urls.py`（router：`projects` / `directories` / `files` / `definitions` + `move/`）+ `api.py`。

- 信封：标准 `{status, data}`（`EnvelopeJSONRenderer`）；View 返回裸 data。
- 用例 ID：`TC-YYYYMMDD-NNNN`（`api_ids.next_case_id`）。
- 枚举：`test_type` = `app|web|api|func`；`business_type` = `appliance|lighting|app`。
- 时间展示：`YYYY-MM-DD-HH:mm:ss`（序列化层 `format_display_time`）。
- **已删除**：四类型 ViewSet/legacy 平铺路径、step-types、YAML 导出、lock/visibility、`/ws/case-editing/`。

## 本 App 协议要点

无本 App 专属 WS。全站 WS 生产点以 `gateway/routing.py` 为准（当前 0）。

## 关单附加项（全局清单的 delta）

```
[ ] 写库只经 api.py；无四类型旧路径
[ ] 树节点 type 仅为 directory|file；definitions 必带 file_id
[ ] 拖拽环检测 409；用户项目隔离
[ ] 无 case-editing WS；gateway 路由与 ARCH 口径一致
```
