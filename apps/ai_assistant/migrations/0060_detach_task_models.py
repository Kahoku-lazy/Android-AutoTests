from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("ai_assistant", "0059_rename_task_tables"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.DeleteModel(name="AITaskEvent"),
                migrations.DeleteModel(name="AITaskMedia"),
                migrations.DeleteModel(name="AITaskAttachment"),
                migrations.DeleteModel(name="AIUsageHourly"),
                migrations.DeleteModel(name="AITask"),
            ],
        ),
    ]
