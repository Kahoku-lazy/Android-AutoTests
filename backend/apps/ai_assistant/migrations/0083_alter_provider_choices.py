from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ai_assistant", "0082_rename_govee_provider"),
    ]

    operations = [
        migrations.AlterField(
            model_name="aimodelconfig",
            name="api_key_env",
            field=models.CharField(
                choices=[
                    ("DEEPSEEK_API_KEY", "DEEPSEEK_API_KEY"),
                    ("DASHSCOPE_API_KEY", "DASHSCOPE_API_KEY"),
                    ("OPENAI_API_KEY", "OPENAI_API_KEY"),
                ],
                max_length=64,
            ),
        ),
        migrations.AlterField(
            model_name="aimodelconfig",
            name="provider",
            field=models.CharField(
                choices=[
                    ("deepseek", "deepseek"),
                    ("dashscope", "dashscope"),
                    ("openai", "openai"),
                ],
                max_length=32,
            ),
        ),
    ]
