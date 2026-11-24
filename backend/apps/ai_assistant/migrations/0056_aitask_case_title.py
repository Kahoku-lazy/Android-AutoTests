from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('ai_assistant', '0055_retire_ai_toolbox'),
    ]

    operations = [
        migrations.AddField(
            model_name='aitask',
            name='case_title',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
    ]
