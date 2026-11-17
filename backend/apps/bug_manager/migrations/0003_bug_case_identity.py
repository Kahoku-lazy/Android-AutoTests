from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bug_manager", "0002_bug_failure_snapshot"),
    ]

    operations = [
        migrations.AddField(
            model_name="bugticket",
            name="case_label",
            field=models.CharField(blank=True, default="", max_length=500),
        ),
        migrations.AddField(
            model_name="bugticket",
            name="case_rows",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
