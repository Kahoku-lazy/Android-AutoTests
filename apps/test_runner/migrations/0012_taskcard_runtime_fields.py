from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("test_runner", "0011_fix_interval_seconds_default"),
    ]

    operations = [
        migrations.AddField(
            model_name="taskcard",
            name="current_case_title",
            field=models.CharField(blank=True, default="", max_length=500),
        ),
        migrations.AddField(
            model_name="taskcard",
            name="current_iteration",
            field=models.IntegerField(default=0),
        ),
    ]
