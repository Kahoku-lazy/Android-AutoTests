from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('ai_assistant', '0042_aidevicepromptarchive'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='aiagent',
            name='enable_knowledge_base',
        ),
        migrations.RemoveField(
            model_name='aiagent',
            name='knowledge_sources',
        ),
    ]
