from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('ai_assistant', '0030_aiagent_strong_enabled_aiagent_strong_model_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='aiagent',
            name='route_configs',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='aitask',
            name='goal',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='aitask',
            name='requirements',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='aitask',
            name='attachment',
            field=models.CharField(blank=True, default='', max_length=500),
        ),
        migrations.AddField(
            model_name='aitask',
            name='route',
            field=models.CharField(default='device_control', max_length=50),
        ),
        migrations.AddField(
            model_name='aitask',
            name='checklist',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='aitask',
            name='report_name',
            field=models.CharField(blank=True, default='', max_length=200),
        ),
    ]
