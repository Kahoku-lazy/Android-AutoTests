from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('task_list', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='taskmedia',
            name='storage_key',
            field=models.CharField(blank=True, default='', max_length=300),
        ),
    ]
