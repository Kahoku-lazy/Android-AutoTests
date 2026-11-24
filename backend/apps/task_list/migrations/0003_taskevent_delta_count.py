from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('task_list', '0002_taskmedia_storage_key'),
    ]

    operations = [
        migrations.AddField(
            model_name='taskevent',
            name='delta_count',
            field=models.PositiveIntegerField(default=1),
        ),
    ]
