import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ai_assistant", "0086_delete_assistantevalrun_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="AssistantEvalCaseResult",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("case_id", models.CharField(max_length=64)),
                ("case_title", models.CharField(blank=True, default="", max_length=200)),
                ("steps_total", models.PositiveIntegerField(default=0)),
                ("steps_passed", models.PositiveIntegerField(default=0)),
                ("attempts", models.PositiveIntegerField(default=0)),
                ("cost_s", models.DecimalField(decimal_places=2, default=0, max_digits=8)),
                (
                    "handover_score",
                    models.DecimalField(blank=True, decimal_places=3, max_digits=4, null=True),
                ),
                ("handover_reason", models.TextField(blank=True, default="")),
                ("failed_steps", models.JSONField(default=list)),
                ("source_ref", models.CharField(blank=True, default="", max_length=200)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "run",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="cases",
                        to="ai_assistant.assistantevalscore",
                    ),
                ),
            ],
            options={
                "verbose_name": "助手评测真题结果",
                "verbose_name_plural": "助手评测真题结果",
                "db_table": "ai_eval_case_results",
                "ordering": ["id"],
            },
        ),
    ]
