from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ai_assistant", "0067_aimodelconfig_and_agent_key"),
    ]

    operations = [
        migrations.AddField(
            model_name="aimodelconfig",
            name="api_protocol",
            field=models.CharField(blank=True, default="", max_length=32),
        ),
    ]
