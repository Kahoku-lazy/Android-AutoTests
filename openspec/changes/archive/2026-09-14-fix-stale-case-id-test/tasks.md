## 1. 复核

- [x] 1.1 复现失败；验证：`pytest tests/graybox/unit/test_case_manager_ids.py -q` → 1 failed（`django.db.utils.IntegrityError: NOT NULL constraint failed: cm_test_definitions.file_id`）
- [x] 1.2 约束真相源；验证：`apps/case_manager/models.py` 的 `TestDefinition.file` 无 `null=True`；迁移 `0021_case_file_sheets` 的 `AlterField` 亦非空；`apps/case_manager/AGENTS.md` 写「树叶子是文件」「definitions 必带 file_id」

## 2. 修改

- [x] 2.1 用例补 `CaseFile.objects.create(project=project, name="f1", created_by="u1")` 并传 `file=case_file`；顶部补 `from apps.case_manager.models import CaseFile`；验证：`git diff` 仅该测试文件 +3 行有效构造

## 3. 验证

- [x] 3.1 `pytest tests/graybox/unit/test_case_manager_ids.py -q` → **2 passed**
- [x] 3.2 `pytest tests/graybox/unit -q` → **75 passed**（修复前基线为 74 passed + 1 failed；无新增失败）
- [x] 3.3 范围核对：`git diff --numstat` 仅 `tests/graybox/unit/test_case_manager_ids.py`，源码与迁移 **0 改动**
