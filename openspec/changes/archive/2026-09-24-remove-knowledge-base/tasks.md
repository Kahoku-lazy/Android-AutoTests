## 1. 立项与范围

- [x] 1.1 变更立项 `2026-09-24-remove-knowledge-base`：proposal / 新增能力规格 `knowledge-base-retirement` / 四个既有规格的 delta / design 全部产出；验证：`openspec validate "2026-09-24-remove-knowledge-base" --strict` 通过
- [x] 1.2 破坏面确认（用户裁决）：删两列 + 清 chromadb；确认 `data/rag_datas` 与 `data/rag_vector` 均不存在，无文件删除

## 2. 后端下线

- [x] 2.1 删除知识库视图与 RAG 服务（`views_knowledge_drf.py`、`rag_service.py`），并从 `urls.py` 摘掉 5 条 knowledge 路由与 import；验证：`python manage.py check` 通过（System check identified no issues）
- [x] 2.2 清理 `api.py`：删 4 个知识库包装函数与 `__all__` 条目，删平台配置里 `enable_knowledge_base` / `knowledge_sources` 的全部读写点；验证：`python -m ruff check apps/ai_assistant config` 全过、全仓 grep 无残留
- [x] 2.3 清理模型调试链路：`model_debug._knowledge()` 与其返回值 / `views_model_debug_drf.py` 响应里的 `knowledge` 键；验证：`pytest tests/graybox/unit/test_ai_model_debug.py -q` 19 项全绿
- [x] 2.4 清理遗留工具网关里的知识库分支（`views/tool_gateway.py`）；验证：`ruff check` 通过 + `manage.py check` 通过
- [x] 2.5 `kb_files.py` 重命名为 `attachments.py`、`KbFileError` 改名 `AttachmentError`，只保留任务附件解析；更新视图与用例引用；验证：`pytest tests/graybox/unit/test_ai_task_title_attach_dispatch.py -q` 14 项全绿（附件行为不变）

## 3. 数据与依赖

- [x] 3.1 删除 `AIAgent.enable_knowledge_base` 与 `knowledge_sources` 字段并生成删列迁移（0043，仅 2 条 RemoveField）；验证：`python manage.py makemigrations --check --dry-run` → No changes detected
- [x] 3.2 `requirements.txt` 移除 `chromadb>=0.4.0`，并清掉 `config/settings.py` 中无人引用的 5 项知识库嵌入模型设置；验证：活代码 grep 无 chromadb / EMBEDDING_ 残留

## 4. 前端下线

- [x] 4.1 删除知识库页面与私有件（`KnowledgeBase.vue`、导入弹窗、预览抽屉、`KbTreeView.vue`、`helpers/kb-tree.ts`）；验证：5 个文件均不存在，`npx vue-tsc --noEmit` 0 error
- [x] 4.2 摘掉入口与路由：侧栏子项、`routes.ts` 的 knowledge 路由、`index.vue` 的 viewMode / VIEW_META / 模板分支；验证：前端路由表与侧栏均无知识库
- [x] 4.3 清理契约与常量：`api/toolbox.ts`、`constants.ts`、`usePlatformConfig.ts`、`AgentDetail.vue`、`shared/types/ai.ts`；验证：`npx vue-tsc --noEmit` 0 error
- [x] 4.4 清理文案与样式：`ModelDebugPage.vue`（含死规则 `.md-badge.warn`）、`helpers/toolbox-assembly.ts`、`index.logic.ts`、`index.style.css`；验证：`frontend/src` 与 `frontend/tests` grep `knowledge|Knowledge|rag_datas|kb-tree|KbTree|知识库` 均 0 命中

## 5. 测试与文档

- [x] 5.1 删除 `tests/graybox/unit/test_kb_files.py`；更新 `test_ai_model_debug.py` 的知识库断言与附件用例 import；验证：`pytest` 相关三文件 42 项全绿
- [x] 5.2 更新前端用例（`useModelDebug.spec.ts`、`ToolboxPanel-tool-debug.spec.ts`）；验证：`cd frontend && npx vitest run tests/ai-assistant/p0/` 16 文件 / 106 用例全绿
- [x] 5.3 文档同步：接口文档删 knowledge 组整章（章节编号顺延、交叉引用同步）；`README.md` / `apps/自测与检测指令.md` / `.gitignore` 清掉 ChromaDB 与已不存在的知识库初始化命令；模块 `AGENTS.md` 改为两子项口径

## 6. 验证与归档

- [x] 6.1 路径一致性对拍：`pytest tests/graybox/unit/test_api_path_callers.py -q` 9 项全绿（前后端路径同批删除后仍一致）
- [x] 6.2 残留扫描：活代码（`apps/` 排除历史迁移、`config/`、`frontend/src`、`frontend/tests`、`tests/`）grep `knowledge` / `rag_service` / `kb_files` / `chromadb` / `EMBEDDING_` / `rag_datas` 均无实质命中（仅剩历史迁移里的旧字段记录与 `storage` / `paragraphs` 之类子串误报）
- [x] 6.3 改动范围静态检查：后端 `manage.py check` + `ruff check` + `ruff format --check`；前端 `vue-tsc` + `prettier --check` + `eslint`，均无新增报错
- [x] 6.4 归档关单：delta 并入主规格（`ai-model-debug` / `workbench-header-copy` / `evaluator-retirement` / `frontend-doodle-subpage-nav` 四条改动 + 新增 `knowledge-base-retirement`），变更目录移入 archive
