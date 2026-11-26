from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('ai_assistant', '0056_aitask_case_title'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='aiagent',
            name='available_models',
        ),
        migrations.RemoveField(
            model_name='aiagent',
            name='is_connected',
        ),
        migrations.RemoveField(
            model_name='aiagent',
            name='last_checked_at',
        ),
    ]
