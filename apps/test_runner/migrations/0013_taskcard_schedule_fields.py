from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("test_runner", "0012_taskcard_runtime_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="taskcard",
            name="start_at",
            field=models.CharField(blank=True, default="", max_length=100),
        ),
        migrations.AddField(
            model_name="taskcard",
            name="end_at",
            field=models.CharField(blank=True, default="", max_length=100),
        ),
    ]
