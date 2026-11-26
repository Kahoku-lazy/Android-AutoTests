import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ai_assistant", "0084_aimodelconfig_dimensions"),
    ]

    operations = [
        migrations.CreateModel(
            name="AssistantEvalScore",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("target_kind", models.CharField(max_length=16)),
                ("target_id", models.CharField(max_length=32)),
                ("prompt_fingerprint", models.CharField(blank=True, default="", max_length=64)),
                ("source_ref", models.CharField(blank=True, default="", max_length=200)),
                ("judge_model", models.CharField(blank=True, default="", max_length=64)),
                ("created_by", models.CharField(blank=True, default="", max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "助手评测评分",
                "verbose_name_plural": "助手评测评分",
                "db_table": "ai_eval_scores",
                "ordering": ["-id"],
            },
        ),
        migrations.CreateModel(
            name="AssistantEvalScoreItem",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("metric_key", models.CharField(max_length=32)),
                ("score", models.DecimalField(decimal_places=3, max_digits=4)),
                ("reason", models.TextField(blank=True, default="")),
                ("threshold", models.DecimalField(decimal_places=3, default=0.5, max_digits=4)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "run",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="ai_assistant.assistantevalscore",
                    ),
                ),
            ],
            options={
                "verbose_name": "助手评测评分项",
                "verbose_name_plural": "助手评测评分项",
                "db_table": "ai_eval_score_items",
                "ordering": ["id"],
            },
        ),
    ]
