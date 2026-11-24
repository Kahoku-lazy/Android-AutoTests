from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('ai_assistant', '0016_add_shared_toolbox'),
    ]

    operations = [
        migrations.AlterField(
            model_name='aiagent',
            name='avatar',
            field=models.TextField(blank=True, default=''),
        ),
    ]
