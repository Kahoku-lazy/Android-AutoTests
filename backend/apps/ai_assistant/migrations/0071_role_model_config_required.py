import django.db.models.deletion
from django.db import migrations, models


def drop_unlinked_roles(apps, schema_editor):
    """没有模型配置的 Agent 配置无法创建角色，收紧外键前删除。"""
    role = apps.get_model("ai_assistant", "AIRole")
    role.objects.filter(model_config__isnull=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("ai_assistant", "0070_retire_aiagent_link_role_model"),
    ]

    operations = [
        migrations.RunPython(drop_unlinked_roles, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="airole",
            name="model_config",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="roles",
                to="ai_assistant.aimodelconfig",
            ),
        ),
    ]
