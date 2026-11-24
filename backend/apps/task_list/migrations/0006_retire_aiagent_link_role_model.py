from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('task_list', '0005_task_created_by'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='task',
            name='agent',
        ),
    ]
