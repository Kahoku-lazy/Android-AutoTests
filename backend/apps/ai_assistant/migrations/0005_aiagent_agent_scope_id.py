from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('ai_assistant', '0004_aiconversation_agent_scope_session_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='aiagent',
            name='agent_scope_id',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
    ]
