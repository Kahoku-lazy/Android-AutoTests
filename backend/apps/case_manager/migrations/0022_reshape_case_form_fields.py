"""重塑用例表单字段：系统/类型拆维、优先级、步骤子表。

旧字段到新字段的折叠规则（见 ``proposal.md`` / ``design.md``）：

- ``test_type`` → ``system`` + ``case_type``：app→ANDROID+AUTO、web→WEB+FUNC、
  api→WEB+AUTO、func→ANDROID+FUNC；
- 旧 ``steps`` 纯文本 → 该用例的**唯一一条**步骤的 ``action``（空则填占位）；
- 旧 ``expected_result`` 内容丢弃，断言统一填 ``（待补充断言）``。

WARNING: 反向迁移不重建 ``test_type`` / ``steps`` / ``expected_result``，
数据折叠不可逆；需要回滚时用迁移前的数据库备份恢复。
"""

import django.db.models.deletion
from django.db import migrations, models

#: 旧测试类型 → (system, case_type)
LEGACY_TYPE_MAP = {
    "app": ("ANDROID", "AUTO"),
    "web": ("WEB", "FUNC"),
    "api": ("WEB", "AUTO"),
    "func": ("ANDROID", "FUNC"),
}

#: 旧用例无步骤描述时的动作占位，保证「步骤至少 1 条」在迁移后自洽
EMPTY_ACTION_PLACEHOLDER = "（原用例无步骤描述）"

#: 断言占位文案，必须与运行时 ``api_definitions.STEPS_PLACEHOLDER_ASSERTION`` 一致
ASSERTION_PLACEHOLDER = "（待补充断言）"


def fold_legacy_cases(apps, schema_editor):
    """把旧字段折叠成新两维 + 单条步骤；空表直接跳过，重复执行不重复建步骤。

    这里刻意只用 ``values_list`` / ``update`` 读取旧字段而不实例化
    ``TestDefinition``：迁移状态里旧字段 ``steps``（TextField）与新表
    ``CaseStep`` 的反向关系 ``steps`` 同名，实例化会撞上反向关系描述器而报错。
    """
    TestDefinition = apps.get_model("case_manager", "TestDefinition")
    CaseStep = apps.get_model("case_manager", "CaseStep")
    if not TestDefinition.objects.exists():
        return
    legacy_rows = list(TestDefinition.objects.values_list("id", "test_type", "steps"))
    for case_id, legacy_type, legacy_steps in legacy_rows:
        system, case_type = LEGACY_TYPE_MAP.get(legacy_type, ("ANDROID", "FUNC"))
        TestDefinition.objects.filter(pk=case_id).update(system=system, case_type=case_type)
        if CaseStep.objects.filter(case_id=case_id).exists():
            continue
        CaseStep.objects.create(
            case_id=case_id,
            sort_order=1,
            action=(legacy_steps or "").strip() or EMPTY_ACTION_PLACEHOLDER,
            assertion=ASSERTION_PLACEHOLDER,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("case_manager", "0021_case_file_sheets"),
    ]

    operations = [
        migrations.AddField(
            model_name="testdefinition",
            name="case_type",
            field=models.CharField(
                choices=[("FUNC", "功能"), ("AUTO", "自动化")], default="AUTO", max_length=8
            ),
        ),
        migrations.AddField(
            model_name="testdefinition",
            name="priority",
            field=models.CharField(
                choices=[("P0", "P0 — 必测"), ("P1", "P1 — 应测"), ("P2", "P2 — 可测")],
                default="P1",
                max_length=4,
            ),
        ),
        migrations.AddField(
            model_name="testdefinition",
            name="system",
            field=models.CharField(
                choices=[("ANDROID", "ANDROID"), ("WEB", "WEB"), ("IOS", "IOS"), ("API", "API")],
                default="ANDROID",
                max_length=16,
            ),
        ),
        migrations.CreateModel(
            name="CaseStep",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("sort_order", models.PositiveIntegerField(default=1)),
                ("action", models.TextField(blank=True, default="")),
                ("assertion", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "case",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="steps",
                        to="case_manager.testdefinition",
                    ),
                ),
            ],
            options={
                "verbose_name": "用例步骤",
                "verbose_name_plural": "用例步骤",
                "db_table": "cm_case_steps",
                "ordering": ["sort_order", "id"],
                "indexes": [
                    models.Index(fields=["case", "sort_order"], name="cm_case_step_case_idx")
                ],
            },
        ),
        migrations.RunPython(fold_legacy_cases, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="testdefinition",
            name="expected_result",
        ),
        migrations.RemoveField(
            model_name="testdefinition",
            name="steps",
        ),
        migrations.RemoveField(
            model_name="testdefinition",
            name="test_type",
        ),
    ]
