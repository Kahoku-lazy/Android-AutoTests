from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('ai_assistant', '0011_skills_config_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='aiagent',
            name='knowledge_sources',
            field=models.JSONField(blank=True, default=list),
        ),
    ]
