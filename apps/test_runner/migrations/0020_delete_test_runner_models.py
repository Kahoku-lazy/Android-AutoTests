from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("test_runner", "0019_backfill_lowercase_run_status"),
    ]

    operations = [
        migrations.DeleteModel(name="TaskCard"),
        migrations.DeleteModel(name="TestResult"),
        migrations.DeleteModel(name="TestSOP"),
        migrations.DeleteModel(name="TestRunRecord"),
    ]
