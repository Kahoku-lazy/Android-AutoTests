"""给 Task 增加发起人快照，供用例入库按用户隔离。"""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("task_list", "0004_task_task_kind"),
    ]

    operations = [
        migrations.AddField(
            model_name="task",
            name="created_by",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
    ]
