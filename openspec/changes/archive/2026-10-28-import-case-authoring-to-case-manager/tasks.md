## 1. 数据模型与归属

- [x] 1.1 为 `Task` 增加 `created_by` 字段与迁移（`task_list/migrations/0005_task_created_by.py`），字段可空、默认空；`python manage.py makemigrations --check` 与 `python manage.py check` 通过。
- [x] 1.2 `create_task` 增加 `created_by` 参数并由 `TaskSubmitAPIView` 写入 `request.user_id`，`rerun_task` 复制原任务创建人；补 `tests/api/test_task_case_authoring.py` 断言提交/重跑归属，pytest 通过。
- [x] 1.3 为 `TestDefinition` 增加 `source_case_id`、`source_task_id` 与迁移（`case_manager/migrations/0023_testdefinition_source_fields.py`），加查询索引；序列化补充两个只读字段；`makemigrations --check` 与 `check` 通过。

## 2. 文档解析扩展

- [x] 2.1 `parse_case_document` 跟踪 `## 模块：NAME（KEY）` 标题并写入 `CaseRow.module`；补 `tests/graybox/unit/test_case_document_check.py` 断言模块归属。
- [x] 2.2 新增 `case_step_pairs`：按 `<br>` 拆分步骤/预期、去掉 `1)`/`1.` 前缀、按序号配对；数量不一致退化为一条完整步骤；补单测覆盖 3 步、数量不一致、空值。
- [x] 2.3 运行 `python -m pytest -c tests/pytest.ini tests/graybox/unit/test_case_document_check.py`，全部通过。

## 3. 用例库导入服务

- [x] 3.1 新增 `backend/apps/case_manager/api_import.py`：`get_or_create`「AI 生成用例」项目与 `{任务标题}（任务 {id}）` 文件，构造 `TestDefinition` 行与 `CaseStep`，写入来源字段；所有写操作在单事务内。
- [x] 3.2 实现幂等：按 `source_task_id` 查已导入用例，存在则返回原项目/文件/条数；不存在才创建；项目/文件唯一约束冲突时重查一次。
- [x] 3.3 定义返回契约 `{status, project_id, file_id, path, case_count, skipped_count, message}`；全部行被跳过时返回 `skipped` 且不建空文件；失败返回 `failed` 并回滚。
- [x] 3.4 通过 `case_manager/api.py` 导出 `import_case_rows`；补 `tests/graybox/unit/test_case_import.py` 覆盖首次导入、重复导入、跳过行、事务回滚，pytest 通过。

## 4. 任务收尾接入

- [x] 4.1 `_run_case_authoring` 在 `passed=true` 且 `document` 非空时解析文档并调用 `case_manager.api.import_case_rows`，把结果写入 `case_import`；导入异常捕获后记 `failed`，不改变任务状态。
- [x] 4.2 `passed=false` / `cancelled` / `interrupted` 的结果写入 `case_import.status=skipped` 与原因；不创建项目或文件。
- [x] 4.3 补 `tests/graybox/unit/test_case_authoring_task_runner.py` 与 `tests/api/test_task_case_authoring.py`：通过任务有 `case_import.path`、失败任务无路径、导入异常仍 `completed`；pytest 通过。

## 5. 报告契约与页面

- [x] 5.1 `_case_authoring_flow` 返回 `case_import`，移除 `document` 字段；结构化交付事件的提示改为「完整文档不在此展开」；补 API 测试断言不再下发 `document`、`case_import` 形状正确。
- [x] 5.2 `TaskDetailPage.vue` 删除 `renderMarkdown`/`documentHtml`/「生成的测试用例」区块，加入「用例入库结果」卡：成功显示条数与 `router-link`，失败/跳过显示原因；运行中保留等待提示。
- [x] 5.3 删除 `helpers/markdown.ts` 与 `tests/task-list/p0/task-document-markdown.spec.ts`，清理未用依赖引用；`npm run typecheck` 通过。
- [x] 5.4 运行 `npx vitest run tests/task-list` 与 `npm run build:check`，通过。

## 6. 门禁与人工验收

- [x] 6.1 运行 `ruff check backend/apps/case_manager backend/apps/task_list engines/agents/workflow/case_document_check.py` 与 `ruff format --check`，通过。
- [x] 6.2 运行 `python utils/gen_arch_stats.py --check-boundaries`，确认 `task_list → case_manager` 只走 `api.py`。
- [x] 6.3 启动前后端，提交一个 Agent-02 任务，确认：任务 `completed`、`Task.result.case_import.status=imported`、用例管理「AI 生成用例」项目出现文件、报告卡可跳转到文件页且无 Markdown 文档区。
- [x] 6.4 对同一任务重复触发导入（或重跑），确认用例条数不翻倍；完成后运行 `openspec validate import-case-authoring-to-case-manager --strict`。
