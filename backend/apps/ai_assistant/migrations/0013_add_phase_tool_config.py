from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('ai_assistant', '0012_knowledge_sources_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='aiagent',
            name='phase_tool_config',
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
