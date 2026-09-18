## 1. 复核

- [x] 1.1 漂移现状；验证：`makemigrations --check --dry-run` exit 1，且恰好 3 条 `Rename index`（casefile ×1 · testdefinition ×1 · workflowdocument ×1）
- [x] 1.2 取准名字与字段；验证：`apps/case_manager/migrations/0021_case_file_sheets.py:83`（`cm_case_fil_project_9a1b2c_idx`，字段 project/directory/sort_order）· `:110`（`cm_test_def_project_file_idx`，字段 project/file/sort_order）· `apps/workflow/migrations/0003_workflowprototype.py:108`（`wf_document_prototy_idx`，字段 prototype/doc_type/directory）

## 2. 修改

- [x] 2.1 `apps/case_manager/models.py`：`CaseFile` 与 `TestDefinition` 两处索引补显式 `name=`（与迁移一致）
- [x] 2.2 `apps/workflow/models.py`：`WorkflowDocument` 索引补显式 `name=`

## 3. 验证

- [x] 3.1 **判据达成**：`python manage.py makemigrations --check --dry-run` → `No changes detected`，**exit 0**
- [x] 3.2 `python manage.py check` → `System check identified no issues`，exit 0；`python -m ruff check` 两文件 → All checks passed；`ruff format --check` → 2 files already formatted
- [x] 3.3 回归：`test_case_manager_ids.py` · `test_case_manager_projects.py` · `test_ai_workflow_progress.py` → **8 passed, 1 failed**。⚠️ 失败的 `test_case_manager_ids.py::test_next_case_id_increments_same_day` 是**既有失败、与本变更无关**：该测试用 `TestDefinition.objects.create(...)` 建行但**不传 `file`**，而 `file` FK 自 `0021_case_file_sheets` 起为 NOT NULL（`IntegrityError: NOT NULL constraint failed: cm_test_definitions.file_id`）。证据：`git diff --stat apps/case_manager/models.py` = 8 insertions/2 deletions 全为索引名行；`tests/graybox/unit/test_case_manager_ids.py` 无工作区改动；`file` 字段在 HEAD 与工作区均为非空 —— 本变更未触碰字段/null 语义
- [x] 3.4 范围核对：`git diff --stat` 仅 `apps/case_manager/models.py`（+8/−2）与 `apps/workflow/models.py`（+4/−1），**无新增迁移文件**

## 4. 范围外登记（发现但不在本单）

- [x] 4.1 `tests/graybox/unit/test_case_manager_ids.py::test_next_case_id_increments_same_day` 是**过期测试**（未跟 `CaseFile` 表格页重构：`definitions` 必带 `file_id`，见 `apps/case_manager/AGENTS.md` 关单附加项）。修复需给该用例补 `file=CaseFile.objects.create(...)`；属测试层，另单处理
- [x] 4.2 其它 App 仍有未显式命名的 `models.Index`（`device_inspector` / `device_pool` / `workflow` 等）——当前 autodetector 无异议，但同一哈希漂移风险仍在；显式命名全仓索引可作为独立「命名规范」单
