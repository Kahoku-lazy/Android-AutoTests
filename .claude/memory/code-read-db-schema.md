---
name: code-read-db-schema
description: How to read database table structure from Django models.py instead of .claude/rules/database.md
metadata:
  type: reference
---

# 数据库表结构 — 从代码读取

**不要依赖 `.claude/rules/database.md` 中的表结构**（那是手工维护的、可能过时的副本）。

## 如何获取

```bash
# 列出所有 Django Model
python manage.py shell -c "
from django.apps import apps
for model in apps.get_models():
    print(model._meta.db_table, '→', model.__module__)
"
```

## 在对话中获取

每个 App 的 `models.py` 文件是唯一真相源：

| 表前缀 | Model 文件 |
|--------|-----------|
| `dp_` | `apps/device_pool/models.py` |
| `el_` | `apps/element_locator/models.py` |
| `cm_` | `apps/case_manager/models.py` |
| `tr_` | `apps/test_runner/models.py` |
| `rg_` | `apps/report_generator/models.py` |
| `ai_` | `apps/ai_assistant/models.py` |

直接 Read 相应文件查看字段、类型、外键、索引、Meta 选项。

## 为什么

- 规则文件中的表结构是手工抄录的，可能已过时
- `models.py` 是代码级真相源，永远与迁移文件一致
- 字段类型、约束、索引一目了然
