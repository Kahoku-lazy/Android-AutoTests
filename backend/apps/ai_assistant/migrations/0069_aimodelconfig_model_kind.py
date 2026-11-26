from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ai_assistant", "0068_aimodelconfig_api_protocol"),
    ]

    operations = [
        migrations.AddField(
            model_name="aimodelconfig",
            name="model_kind",
            field=models.CharField(blank=True, default="chat", max_length=32),
        ),
        migrations.AddField(
            model_name="aimodelconfig",
            name="voice",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
    ]
