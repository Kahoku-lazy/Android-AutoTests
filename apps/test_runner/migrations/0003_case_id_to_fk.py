# Generated migration: change case_id from CharField to FK(TestDefinition)
# Uses SeparateDatabaseAndState because the column already exists in both
# SQLite and MySQL, we're just upgrading Django's understanding of it.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('test_runner', '0002_add_test_sop'),
        ('case_manager', '0004_delete_testcasecache'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RemoveField(
                    model_name='testresult',
                    name='case_id',
                ),
                migrations.AddField(
                    model_name='testresult',
                    name='case',
                    field=models.ForeignKey(
                        blank=True,
                        db_column='case_id',
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name='test_results',
                        to='case_manager.TestDefinition',
                        to_field='id',
                    ),
                ),
                migrations.AlterField(
                    model_name='testrunrecord',
                    name='selected_cases',
                    field=models.JSONField(default=list),
                ),
            ],
            database_operations=[
                # No DB-level changes needed:
                # - case_id column already exists in tr_test_results
                # - Django FK uses db_column='case_id' so column name stays the same
                # - selected_cases JSONField default change is state-only
            ],
        ),
    ]
