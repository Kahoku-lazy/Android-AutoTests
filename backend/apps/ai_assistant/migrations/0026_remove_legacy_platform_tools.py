from django.db import migrations


def delete_legacy_platform_tools(apps, schema_editor):
    AITool = apps.get_model("ai_assistant", "AITool")
    AITool.objects.filter(tool_type="platform").delete()


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("ai_assistant", "0025_add_platform_tool_state"),
    ]

    operations = [
        migrations.RunPython(delete_legacy_platform_tools, noop),
    ]
