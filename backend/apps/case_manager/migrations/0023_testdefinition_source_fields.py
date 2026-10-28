"""给用例增加来源字段：源文档用例编号与来源任务编号。"""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("case_manager", "0022_reshape_case_form_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="testdefinition",
            name="source_case_id",
            field=models.CharField(blank=True, db_index=True, default="", max_length=200),
        ),
        migrations.AddField(
            model_name="testdefinition",
            name="source_task_id",
            field=models.CharField(blank=True, db_index=True, default="", max_length=64),
        ),
    ]
