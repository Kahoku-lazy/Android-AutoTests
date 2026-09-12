"""新增 doc_type=api_flow（接口流），与 page_flow 并列。"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("workflow", "0003_workflowprototype"),
    ]

    operations = [
        migrations.AlterField(
            model_name="workflowdocument",
            name="doc_type",
            field=models.CharField(
                choices=[("page_flow", "页面流"), ("api_flow", "接口流")],
                max_length=32,
            ),
        ),
    ]
