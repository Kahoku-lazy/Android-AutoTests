from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ai_assistant", "0074_message_report_id"),
    ]

    operations = [
        migrations.CreateModel(
            name="AISopWorkflow",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200)),
                ("executor_assistant_id", models.CharField(max_length=12)),
                ("verifier_assistant_id", models.CharField(max_length=12)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "SOP 工作流",
                "verbose_name_plural": "SOP 工作流",
                "db_table": "ai_sop_workflows",
            },
        ),
    ]
