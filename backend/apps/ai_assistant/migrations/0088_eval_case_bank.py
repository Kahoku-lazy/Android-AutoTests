import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ai_assistant", "0087_eval_case_results"),
    ]

    operations = [
        migrations.CreateModel(
            name="AssistantEvalCase",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("title", models.CharField(max_length=200)),
                ("note", models.TextField(blank=True, default="")),
                ("enabled", models.BooleanField(default=True)),
                ("sort_order", models.PositiveIntegerField(default=1)),
                ("created_by", models.CharField(blank=True, default="", max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "UI 执行评测题",
                "verbose_name_plural": "UI 执行评测题",
                "db_table": "ai_eval_cases",
                "ordering": ["sort_order", "id"],
            },
        ),
        migrations.CreateModel(
            name="AssistantEvalCaseStep",
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
                ("anchor", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "case",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="steps",
                        to="ai_assistant.assistantevalcase",
                    ),
                ),
            ],
            options={
                "verbose_name": "评测题步骤",
                "verbose_name_plural": "评测题步骤",
                "db_table": "ai_eval_case_steps",
                "ordering": ["sort_order", "id"],
            },
        ),
        migrations.AddField(
            model_name="assistantevalscore",
            name="method_key",
            field=models.CharField(blank=True, default="", max_length=32),
        ),
        migrations.AddField(
            model_name="assistantevalscore",
            name="report_html",
            field=models.CharField(blank=True, default="", max_length=300),
        ),
        migrations.AddField(
            model_name="assistantevalscore",
            name="test_run_json",
            field=models.CharField(blank=True, default="", max_length=300),
        ),
        migrations.RemoveField(
            model_name="assistantevalcaseresult",
            name="handover_score",
        ),
        migrations.RemoveField(
            model_name="assistantevalcaseresult",
            name="handover_reason",
        ),
        migrations.AddField(
            model_name="assistantevalcaseresult",
            name="score",
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=4, null=True),
        ),
        migrations.AddField(
            model_name="assistantevalcaseresult",
            name="reason",
            field=models.TextField(blank=True, default=""),
        ),
    ]
