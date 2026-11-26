from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('ai_assistant', '0032_aiagent_max_loops'),
    ]

    operations = [
        migrations.AddField(
            model_name='aitask',
            name='device_serial',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
    ]
