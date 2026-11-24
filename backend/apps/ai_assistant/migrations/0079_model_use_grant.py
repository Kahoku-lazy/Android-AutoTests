from django.db import migrations, models


def backfill_existing_use(apps=None, schema_editor=None):
    registry = apps
    if registry is None:
        from django.apps import apps as registry
    Grant = registry.get_model("ai_assistant", "ModelUseGrant")
    Config = registry.get_model("ai_assistant", "AIModelConfig")
    User = registry.get_model("auth", "User")
    superuser_ids = list(User.objects.filter(is_superuser=True).values_list("id", flat=True))
    for user_id in superuser_ids:
        for config_id in Config.objects.values_list("id", flat=True):
            Grant.objects.get_or_create(user_id=int(user_id), model_config_id=int(config_id))


def clear_backfill(apps, schema_editor):
    apps.get_model("ai_assistant", "ModelUseGrant").objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("ai_assistant", "0078_assistant_author_grant"),
    ]

    operations = [
        migrations.CreateModel(
            name="ModelUseGrant",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("user_id", models.PositiveIntegerField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "model_config",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="use_grants",
                        to="ai_assistant.aimodelconfig",
                    ),
                ),
            ],
            options={
                "verbose_name": "模型使用名单",
                "verbose_name_plural": "模型使用名单",
                "db_table": "ai_model_use_grants",
            },
        ),
        migrations.AddConstraint(
            model_name="modelusegrant",
            constraint=models.UniqueConstraint(
                fields=("user_id", "model_config"),
                name="uniq_ai_model_use_grant",
            ),
        ),
        migrations.RunPython(backfill_existing_use, clear_backfill),
    ]
