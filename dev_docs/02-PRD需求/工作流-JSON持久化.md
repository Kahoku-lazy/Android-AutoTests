# PRD — 工作流 JSON 持久化（Django）

> 状态：实现中 · 2026-07

## 目标

页面流、测试用例以 **JSON 配置** 存入数据库；每条配置有全局唯一 `doc_id`，支持按 ID 管理、JSON 导入/导出。

## 范围

| 纳入 | 说明 |
|------|------|
| `wf_directories` | 工作流目录树 |
| `wf_documents` | `page_flow` / `test_case` 文档，`config_json` + 唯一 `doc_id` |
| REST CRUD | `/api/workflow/*` |
| 导入/导出 | envelope：`format` + `doc_id` + `doc_type` + `title` + `config` |
| 前端 | 目录/文件改走 API，替换 localStorage 权威存储 |

## 唯一 ID

- 自动生成：`WF-{PF|TC}-YYYYMMDD-HHMMSS-XXXX`
- 导入若带 `doc_id`：已存在则 **拒绝（409）**；空则自动生成

## 验收

- [x] migrate 成功
- [x] 新建页面流/用例写入 DB
- [x] export → import 同 doc_id 冲突报错，换 id 可成功
- [x] 前端目录浏览读自 API
