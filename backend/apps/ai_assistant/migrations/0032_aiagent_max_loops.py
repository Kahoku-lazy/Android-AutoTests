from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('ai_assistant', '0031_aiagent_route_configs_aitask_publish_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='aiagent',
            name='max_loops',
            field=models.IntegerField(default=3),
        ),
    ]
