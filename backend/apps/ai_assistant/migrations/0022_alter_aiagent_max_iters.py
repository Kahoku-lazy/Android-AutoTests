from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('ai_assistant', '0021_add_capability_db_defaults'),
    ]

    operations = [
        migrations.AlterField(
            model_name='aiagent',
            name='max_iters',
            field=models.IntegerField(default=20),
        ),
    ]
