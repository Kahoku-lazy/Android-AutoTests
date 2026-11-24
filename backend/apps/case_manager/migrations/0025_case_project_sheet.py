from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("case_manager", "0024_case_step_execution_hints"),
    ]

    operations = [
        migrations.DeleteModel(name="CaseStep"),
        migrations.DeleteModel(name="TestDefinition"),
        migrations.DeleteModel(name="CaseFile"),
        migrations.DeleteModel(name="CaseDirectory"),
        migrations.AddField(
            model_name="caseproject",
            name="library_kind",
            field=models.CharField(
                choices=[("automation", "自动化"), ("functional", "功能")],
                default="functional",
                max_length=16,
            ),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name="AutomationCase",
            fields=[
                ("id", models.CharField(max_length=200, primary_key=True, serialize=False)),
                ("title", models.CharField(max_length=500)),
                ("priority", models.CharField(choices=[("P0", "P0 — 必测"), ("P1", "P1 — 应测"), ("P2", "P2 — 可测")], default="P1", max_length=4)),
                ("system", models.CharField(choices=[("ANDROID", "ANDROID"), ("WEB", "WEB"), ("IOS", "IOS"), ("API", "API")], default="ANDROID", max_length=16)),
                ("business_type", models.CharField(choices=[("appliance", "家电"), ("lighting", "照明"), ("app", "APP")], max_length=16)),
                ("module", models.CharField(blank=True, default="", max_length=200)),
                ("precondition", models.TextField(blank=True, default="")),
                ("source_case_id", models.CharField(blank=True, db_index=True, default="", max_length=200)),
                ("source_task_id", models.CharField(blank=True, db_index=True, default="", max_length=64)),
                ("sort_order", models.IntegerField(default=0)),
                ("created_by", models.CharField(blank=True, default="", max_length=200)),
                ("updated_by", models.CharField(blank=True, default="", max_length=200)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("project", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="automation_cases", to="case_manager.caseproject")),
            ],
            options={"db_table": "cm_automation_cases", "verbose_name": "自动化用例", "verbose_name_plural": "自动化用例"},
        ),
        migrations.CreateModel(
            name="FunctionalCase",
            fields=[
                ("id", models.CharField(max_length=200, primary_key=True, serialize=False)),
                ("title", models.CharField(max_length=500)),
                ("priority", models.CharField(choices=[("P0", "P0 — 必测"), ("P1", "P1 — 应测"), ("P2", "P2 — 可测")], default="P1", max_length=4)),
                ("system", models.CharField(choices=[("ANDROID", "ANDROID"), ("WEB", "WEB"), ("IOS", "IOS"), ("API", "API")], default="ANDROID", max_length=16)),
                ("business_type", models.CharField(choices=[("appliance", "家电"), ("lighting", "照明"), ("app", "APP")], max_length=16)),
                ("module", models.CharField(blank=True, default="", max_length=200)),
                ("precondition", models.TextField(blank=True, default="")),
                ("source_case_id", models.CharField(blank=True, db_index=True, default="", max_length=200)),
                ("source_task_id", models.CharField(blank=True, db_index=True, default="", max_length=64)),
                ("sort_order", models.IntegerField(default=0)),
                ("created_by", models.CharField(blank=True, default="", max_length=200)),
                ("updated_by", models.CharField(blank=True, default="", max_length=200)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("project", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="functional_cases", to="case_manager.caseproject")),
            ],
            options={"db_table": "cm_functional_cases", "verbose_name": "功能用例", "verbose_name_plural": "功能用例"},
        ),
        migrations.CreateModel(
            name="AutomationStep",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("sort_order", models.PositiveIntegerField(default=1)),
                ("action", models.TextField(blank=True, default="")),
                ("assertion", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("anchor", models.JSONField(blank=True, default=dict)),
                ("log", models.JSONField(blank=True, default=dict)),
                ("case", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="steps", to="case_manager.automationcase")),
            ],
            options={"db_table": "cm_automation_steps", "ordering": ["sort_order", "id"], "verbose_name": "自动化步骤", "verbose_name_plural": "自动化步骤"},
        ),
        migrations.CreateModel(
            name="FunctionalStep",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("sort_order", models.PositiveIntegerField(default=1)),
                ("action", models.TextField(blank=True, default="")),
                ("assertion", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("case", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="steps", to="case_manager.functionalcase")),
            ],
            options={"db_table": "cm_functional_steps", "ordering": ["sort_order", "id"], "verbose_name": "功能步骤", "verbose_name_plural": "功能步骤"},
        ),
        migrations.CreateModel(
            name="CaseSheetView",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("user_id", models.CharField(max_length=200)),
                ("payload", models.JSONField(blank=True, default=dict)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("project", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="sheet_views", to="case_manager.caseproject")),
            ],
            options={"db_table": "cm_case_sheet_views", "verbose_name": "用例表视图", "verbose_name_plural": "用例表视图"},
        ),
        migrations.AddIndex(
            model_name="automationcase",
            index=models.Index(fields=["project", "sort_order"], name="cm_auto_case_project_idx"),
        ),
        migrations.AddIndex(
            model_name="functionalcase",
            index=models.Index(fields=["project", "sort_order"], name="cm_func_case_project_idx"),
        ),
        migrations.AddIndex(
            model_name="automationstep",
            index=models.Index(fields=["case", "sort_order"], name="cm_auto_step_case_idx"),
        ),
        migrations.AddIndex(
            model_name="functionalstep",
            index=models.Index(fields=["case", "sort_order"], name="cm_func_step_case_idx"),
        ),
        migrations.AddConstraint(
            model_name="casesheetview",
            constraint=models.UniqueConstraint(fields=("project", "user_id"), name="unique_case_sheet_view_owner"),
        ),
    ]
