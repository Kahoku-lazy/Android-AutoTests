## 1. Backend models & migration

- [x] 1.1 新增 `LocatorProject` / `LocatorDirectory`；`Page`/`WebElement`/`ApiEndpoint` 增加 `directory` FK
- [x] 1.2 Data migration：seed 三项目；文件夹/分组→目录；叶子挂接
- [x] 1.3 `api_projects.py` / `api_directories.py`：list/tree/CRUD/move/batch-delete
- [x] 1.4 DRF views + urls：projects/directories/move/batch-delete；项目写 405；分组写 410
- [x] 1.5 叶子创建支持 `directory_id`；`import_snapshot_page` 改 LocatorDirectory
- [x] 1.6 更新 AGENTS.md 与 API 文档摘要

## 2. Frontend workspace

- [x] 2.1 路由与旧路径重定向
- [x] 2.2 侧栏单项；api/types/composables
- [x] 2.3 ProjectList（三固定卡片）
- [x] 2.4 ProjectWorkspace + LocatorTree + LocatorFilePanel
- [x] 2.5 更新模块 AGENTS.md

## 3. Downstream

- [x] 3.1 检查器导入走新目录解析
- [x] 3.2 workflow 仍可读旧分组表（未删表）
- [ ] 3.3 dashboard 计数按项目汇总（可选，未做）

## 4. Verification

- [x] 4.1 migrate + check + list/tree smoke
- [ ] 4.2 前端全量 typecheck（既有无关错误）
- [ ] 4.3 边界扫描（未改跨 App 写路径）
