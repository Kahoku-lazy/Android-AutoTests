import django.db.models.deletion
from django.db import migrations, models

LEGACY_TYPE_MAP = {
    "app": ("ANDROID", "AUTO"),
    "web": ("WEB", "FUNC"),
    "api": ("WEB", "AUTO"),
    "func": ("ANDROID", "FUNC"),
}

EMPTY_ACTION_PLACEHOLDER = "（原用例无步骤描述）"

ASSERTION_PLACEHOLDER = "（待补充断言）"


def fold_legacy_cases(apps, schema_editor):
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
