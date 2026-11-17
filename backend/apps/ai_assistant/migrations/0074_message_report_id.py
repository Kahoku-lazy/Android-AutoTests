from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ai_assistant", "0073_assistant_threads"),
    ]

    operations = [
        migrations.AddField(
            model_name="aiassistantmessage",
            name="report_id",
            field=models.CharField(blank=True, default="", max_length=32),
        ),
    ]
