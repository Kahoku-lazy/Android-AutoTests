"""Add CaseFile sheet entity; convert legacy case leaves into files."""

import django.db.models.deletion
from django.db import migrations, models


def convert_cases_to_files(apps, schema_editor):
    TestDefinition = apps.get_model("case_manager", "TestDefinition")
    CaseFile = apps.get_model("case_manager", "CaseFile")
    for case in TestDefinition.objects.all().order_by("id"):
        base_name = (case.title or case.id or "未命名文件").strip()[:180]
        name = base_name
        n = 1
        while CaseFile.objects.filter(
            project_id=case.project_id,
            directory_id=case.directory_id,
            name=name,
        ).exists():
            n += 1
            name = f"{base_name}-{n}"
        case_file = CaseFile.objects.create(
            project_id=case.project_id,
            directory_id=case.directory_id,
            name=name,
            sort_order=case.sort_order or 0,
            created_by=case.created_by or "",
        )
        case.file_id = case_file.id
        case.save(update_fields=["file_id"])


class Migration(migrations.Migration):
    dependencies = [
        ("case_manager", "0020_project_document_cases"),
    ]

    operations = [
        migrations.CreateModel(
            name="CaseFile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200)),
                ("sort_order", models.IntegerField(default=0)),
                ("created_by", models.CharField(blank=True, default="", max_length=200)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "directory",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="files",
                        to="case_manager.casedirectory",
                    ),
                ),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="files",
                        to="case_manager.caseproject",
                    ),
                ),
            ],
            options={
                "verbose_name": "用例文件",
                "verbose_name_plural": "用例文件",
                "db_table": "cm_case_files",
            },
        ),
        migrations.AddConstraint(
            model_name="casefile",
            constraint=models.UniqueConstraint(
                fields=("project", "directory", "name"),
                name="unique_file_project_directory_name",
            ),
        ),
        migrations.AddIndex(
            model_name="casefile",
            index=models.Index(
                fields=["project", "directory", "sort_order"],
                name="cm_case_fil_project_9a1b2c_idx",
            ),
        ),
        migrations.AddField(
            model_name="testdefinition",
            name="file",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="cases",
                to="case_manager.casefile",
            ),
        ),
        migrations.RunPython(convert_cases_to_files, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="testdefinition",
            name="file",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="cases",
                to="case_manager.casefile",
            ),
        ),
        migrations.AddIndex(
            model_name="testdefinition",
            index=models.Index(
                fields=["project", "file", "sort_order"],
                name="cm_test_def_project_file_idx",
            ),
        ),
    ]
