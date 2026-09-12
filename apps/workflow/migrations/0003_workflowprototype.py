"""新增 wf_prototypes，目录/文档挂 prototype；历史数据迁入「默认原型」."""

from django.db import migrations, models
import django.db.models.deletion


def attach_default_prototype(apps, schema_editor):
    WorkflowPrototype = apps.get_model("workflow", "WorkflowPrototype")
    WorkflowDirectory = apps.get_model("workflow", "WorkflowDirectory")
    WorkflowDocument = apps.get_model("workflow", "WorkflowDocument")

    proto = WorkflowPrototype.objects.create(
        name="默认原型",
        description="由历史全局资源库自动迁移",
    )
    WorkflowDirectory.objects.filter(prototype__isnull=True).update(prototype_id=proto.id)
    WorkflowDocument.objects.filter(prototype__isnull=True).update(prototype_id=proto.id)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("workflow", "0002_purge_test_case_documents"),
    ]

    operations = [
        migrations.CreateModel(
            name="WorkflowPrototype",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200)),
                ("description", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "页面流原型",
                "verbose_name_plural": "页面流原型",
                "db_table": "wf_prototypes",
            },
        ),
        migrations.AddConstraint(
            model_name="workflowprototype",
            constraint=models.UniqueConstraint(fields=("name",), name="unique_wf_prototype_name"),
        ),
        migrations.AddField(
            model_name="workflowdirectory",
            name="prototype",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="directories",
                to="workflow.workflowprototype",
            ),
        ),
        migrations.AddField(
            model_name="workflowdocument",
            name="prototype",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="documents",
                to="workflow.workflowprototype",
            ),
        ),
        migrations.RunPython(attach_default_prototype, noop_reverse),
        migrations.AlterField(
            model_name="workflowdirectory",
            name="prototype",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="directories",
                to="workflow.workflowprototype",
            ),
        ),
        migrations.AlterField(
            model_name="workflowdocument",
            name="prototype",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="documents",
                to="workflow.workflowprototype",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="workflowdirectory",
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name="workflowdirectory",
            constraint=models.UniqueConstraint(
                fields=("prototype", "parent", "name"),
                name="unique_wf_directory_prototype_parent_name",
            ),
        ),
        migrations.RemoveIndex(
            model_name="workflowdocument",
            name="wf_document_doc_typ_754ed9_idx",
        ),
        migrations.AddIndex(
            model_name="workflowdocument",
            index=models.Index(
                fields=["prototype", "doc_type", "directory"],
                name="wf_document_prototy_idx",
            ),
        ),
    ]
