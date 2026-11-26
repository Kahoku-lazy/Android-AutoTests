from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('ai_assistant', '0017_avatar_to_textfield'),
    ]

    operations = [
        migrations.AlterField(
            model_name='aiagent',
            name='knowledge_sources',
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
