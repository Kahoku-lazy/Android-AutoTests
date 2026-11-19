# Generated for model-use-grant. Existing use is backfilled once and can be rerun.

from django.db import migrations, models


def backfill_existing_use(apps=None, schema_editor=None):
    """给现有超级管理员补上当前全部模型。同一对关系重复执行时跳过。

    角色配置没有使用者归属，不能据此给普通用户补名单。
    查不到使用关系的人保持空名单，由超级管理员随后授予。
    """
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
    """反向迁移只清补齐产生的名单，不删模型配置。"""
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
