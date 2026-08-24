"""清除积木用例文档（doc_type=test_case），并收窄 doc_type choices。"""

from django.db import migrations, models


def purge_test_cases(apps, schema_editor):
    WorkflowDocument = apps.get_model("workflow", "WorkflowDocument")
    WorkflowDocument.objects.filter(doc_type="test_case").delete()


def noop_reverse(apps, schema_editor):
    # 已删除的积木用例无法恢复
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("workflow", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(purge_test_cases, noop_reverse),
        migrations.AlterField(
            model_name="workflowdocument",
            name="doc_type",
            field=models.CharField(
                choices=[("page_flow", "页面流")],
                max_length=32,
            ),
        ),
    ]
