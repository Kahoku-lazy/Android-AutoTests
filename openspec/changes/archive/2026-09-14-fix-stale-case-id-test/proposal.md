## Why

`tests/graybox/unit/test_case_manager_ids.py::test_next_case_id_increments_same_day` **既有失败**（本次 D0 复查扫出）：

```
django.db.utils.IntegrityError: NOT NULL constraint failed: cm_test_definitions.file_id
```

根因：该用例用 `TestDefinition.objects.create(...)` 建行但**不传 `file`**；而 `TestDefinition.file` 自 `case_manager/migrations/0021_case_file_sheets` 起为 **NOT NULL** FK（`CaseFile` 表格页重构后，用例行必须挂文件，见 `apps/case_manager/AGENTS.md` 关单附加项「definitions 必带 file_id」）。测试没跟上这次模型变更。

影响：`pytest -m unit` 常红一条，掩盖真实回归；且它是 `next_case_id` 唯一的行为用例（同日递增）。

## What Changes

- `tests/graybox/unit/test_case_manager_ids.py`：先建 `CaseFile`（`project` + `name`），再在 `TestDefinition.objects.create(...)` 里传 `file=file_obj`；补 `CaseFile` 的 import
- **不改**：`next_case_id()` 实现、模型、迁移（本单只修测试数据构造）
- **BREAKING**：无
- 按 schema 约定设 `skip_specs: true`

## 关联文档

- App 约束：`apps/case_manager/AGENTS.md`（「树叶子是文件，不是单条用例；用例行挂在 file 下」·「definitions 必带 file_id」）
- 模型真相源：`apps/case_manager/models.py`（`CaseFile` / `TestDefinition`）· 迁移 `0021_case_file_sheets`
- 发现来源：`stabilize-drifted-index-names` 的门禁回归（索引名修复后跑 case/workflow 单测时暴露；该失败与索引名无关，是既有失败）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 不改 Requirement 文本，故无 delta）

## Impact

- 测试：`tests/graybox/unit/test_case_manager_ids.py`（+3 行）
- 源码：**0 行改动**
- 验证：该文件 2 个用例全绿；`pytest tests/graybox/unit -q` 无新增失败
