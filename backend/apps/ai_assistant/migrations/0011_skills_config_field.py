from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('ai_assistant', '0010_parallel_tool_calls_default_true'),
    ]

    operations = [
        migrations.AddField(
            model_name='aiagent',
            name='skills_config',
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
