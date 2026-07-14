# 工作流 JSON 持久化（Django）

- 表：`wf_directories`、`wf_documents`（`config_json` + 唯一 `doc_id`）
- ID：`WF-{PF|TC}-YYYYMMDD-HHMMSS-XXXX`，导入同 ID 默认 409，可 `overwrite`
- 前端 `libraryStore` 权威源改为 `/api/workflow/*`，localStorage 仅存目录展开态
- Admin 可管目录与文档；删除目录会清下属文档
