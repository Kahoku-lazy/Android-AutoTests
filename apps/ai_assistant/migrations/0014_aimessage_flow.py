from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ai_assistant", "0013_add_phase_tool_config"),
    ]

    operations = [
        migrations.AddField(
            model_name="aimessage",
            name="flow",
            field=models.CharField(blank=True, default="", max_length=20),
        ),
    ]
