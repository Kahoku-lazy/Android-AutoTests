# Manual fix: add DB-level default for interval_seconds
# The model already has default=5 but MySQL doesn't inherit it

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('test_runner', '0010_add_interval_seconds'),
    ]

    operations = [
        migrations.AlterField(
            model_name='taskcard',
            name='interval_seconds',
            field=models.IntegerField(default=5),
        ),
    ]
