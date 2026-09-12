"""
Clear legacy four-type case data then reshape schema for project-based document cases.

WARNING: Deletes all rows in cm_* case tables. Irreversible without backup.
"""

from django.db import migrations, models
import django.db.models.deletion


def clear_legacy_case_data(apps, schema_editor):
    for name in (
        "ApiTestCase",
        "WebTestCase",
        "StorageTestCase",
        "TestDefinition",
        "CaseDirectory",
    ):
        try:
            model = apps.get_model("case_manager", name)
        except LookupError:
            continue
        model.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("case_manager", "0019_add_config_json_to_api"),
    ]

    operations = [
        migrations.RunPython(clear_legacy_case_data, migrations.RunPython.noop),
        migrations.DeleteModel(name="ApiTestCase"),
        migrations.DeleteModel(name="WebTestCase"),
        migrations.DeleteModel(name="StorageTestCase"),
        migrations.CreateModel(
            name="CaseProject",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200)),
                ("description", models.TextField(blank=True, default="")),
                ("created_by", models.CharField(blank=True, default="", max_length=200)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "用例项目",
                "verbose_name_plural": "用例项目",
                "db_table": "cm_case_projects",
            },
        ),
        migrations.AddConstraint(
            model_name="caseproject",
            constraint=models.UniqueConstraint(
                fields=("created_by", "name"),
                name="unique_project_owner_name",
            ),
        ),
        # CaseDirectory: drop old constraint/fields, add project
        migrations.RemoveConstraint(
            model_name="casedirectory",
            name="unique_directory_parent_name_type",
        ),
        migrations.RemoveField(model_name="casedirectory", name="case_type"),
        migrations.RemoveField(model_name="casedirectory", name="allow_create"),
        migrations.RemoveField(model_name="casedirectory", name="allow_delete"),
        migrations.AddField(
            model_name="casedirectory",
            name="project",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="directories",
                to="case_manager.caseproject",
            ),
        ),
        migrations.AddConstraint(
            model_name="casedirectory",
            constraint=models.UniqueConstraint(
                fields=("project", "parent", "name"),
                name="unique_directory_project_parent_name",
            ),
        ),
        # TestDefinition reshape
        migrations.RemoveConstraint(
            model_name="testdefinition",
            name="unique_directory_title",
        ),
        migrations.RemoveField(model_name="testdefinition", name="case_type"),
        migrations.RemoveField(model_name="testdefinition", name="category"),
        migrations.RemoveField(model_name="testdefinition", name="description"),
        migrations.RemoveField(model_name="testdefinition", name="steps_json"),
        migrations.RemoveField(model_name="testdefinition", name="watchers"),
        migrations.RemoveField(model_name="testdefinition", name="enabled"),
        migrations.RemoveField(model_name="testdefinition", name="package_name"),
        migrations.RemoveField(model_name="testdefinition", name="priority"),
        migrations.RemoveField(model_name="testdefinition", name="design_method"),
        migrations.RemoveField(model_name="testdefinition", name="metrics"),
        migrations.RemoveField(model_name="testdefinition", name="editing_by"),
        migrations.RemoveField(model_name="testdefinition", name="editing_since"),
        migrations.RemoveField(model_name="testdefinition", name="locked"),
        migrations.RemoveField(model_name="testdefinition", name="visibility"),
        migrations.RemoveField(model_name="testdefinition", name="permitted_users"),
        migrations.RemoveField(model_name="testdefinition", name="permission"),
        migrations.RemoveField(model_name="testdefinition", name="permitted_editors"),
        migrations.AddField(
            model_name="testdefinition",
            name="project",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="cases",
                to="case_manager.caseproject",
            ),
        ),
        migrations.AddField(
            model_name="testdefinition",
            name="test_type",
            field=models.CharField(
                choices=[("app", "APP"), ("web", "WEB"), ("api", "API"), ("func", "FUNC")],
                default="app",
                max_length=16,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="testdefinition",
            name="business_type",
            field=models.CharField(
                choices=[
                    ("appliance", "家电"),
                    ("lighting", "照明"),
                    ("app", "APP"),
                ],
                default="appliance",
                max_length=16,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="testdefinition",
            name="module",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
        migrations.AddField(
            model_name="testdefinition",
            name="sort_order",
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="testdefinition",
            name="steps",
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name="testdefinition",
            name="expected_result",
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name="testdefinition",
            name="directory",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="cases",
                to="case_manager.casedirectory",
            ),
        ),
        migrations.AddIndex(
            model_name="testdefinition",
            index=models.Index(
                fields=["project", "directory", "sort_order"],
                name="cm_test_def_project_032175_idx",
            ),
        ),
    ]
