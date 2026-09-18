## Why

`python manage.py makemigrations --check --dry-run` **exit 1**：模型索引名与迁移状态漂移，autodetector 每次都提议生成 3 个无信息量的 rename 迁移。实测输出：

```
Migrations for 'case_manager':
  ~ Rename index cm_case_fil_project_9a1b2c_idx on casefile to cm_case_fil_project_e6945c_idx
  ~ Rename index cm_test_def_project_file_idx on testdefinition to cm_test_def_project_76cd9e_idx
Migrations for 'workflow':
  ~ Rename index wf_document_prototy_idx on workflowdocument to wf_document_prototy_2f0bed_idx
exit=1
```

根因：这 3 个 `models.Index` 在模型里**没有显式 `name=`**，Django 按「表名_字段前缀_哈希」现算；而迁移里记录的是当时写入的名字。哈希算法/输入变化后，现算名与迁移记录名不再相等 → 每次 `makemigrations` 都提议改名。

影响：`makemigrations --check` 是关单门禁红线项，当前**任何后端关单跑它都会失败**；且一旦有人顺手 `makemigrations` 落盘，线上会执行一串无意义的 `ALTER TABLE … RENAME INDEX`。

## What Changes

给这 3 个索引补上**与迁移状态一致**的显式 `name=`：

| 模型 | 索引字段 | 补的 name（取自迁移） |
|------|----------|------------------------|
| `case_manager.CaseFile` | project / directory / sort_order | `cm_case_fil_project_9a1b2c_idx`（0021_case_file_sheets） |
| `case_manager.TestDefinition` | project / file / sort_order | `cm_test_def_project_file_idx`（0021_case_file_sheets） |
| `workflow.WorkflowDocument` | prototype / doc_type / directory | `wf_document_prototy_idx`（0003_workflowprototype） |

- **不改**：索引字段、`Meta.constraints`、`db_table`、任何迁移文件；不生成迁移；不动其它 App 的索引（autodetector 对它们当前无异议）
- **BREAKING**：无（索引名不变、字段不变 → 数据库 DDL 无变化）
- 按 schema 约定设 `skip_specs: true`

## 关联文档

- 门禁依据：`.agents/skills/django-backend-check/references/calibration.md` §7（`makemigrations --check` 必跑）· §2（漏 migration / 模型与库不一致 = 🔴）
- App 约束：`apps/case_manager/AGENTS.md` · `apps/workflow/AGENTS.md`
- 发现来源：本次 D0（边界与配置）复查 —— 该红线由 D0 门禁批次扫出，但落在模型层（D1/D2）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 不改 Requirement 文本，故无 delta）

## Impact

- 源码：`apps/case_manager/models.py`（2 处索引名）· `apps/workflow/models.py`（1 处）
- 数据库：**无 DDL 变化**（名字与迁移状态一致，`makemigrations` 不再产生任何操作）
- 验证：`makemigrations --check` exit 0 · `manage.py check` 0 issues · `ruff check` 两文件 · case_manager / workflow 相关单测
