from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ai_assistant", "0066_airole"),
    ]

    operations = [
        migrations.AddField(
            model_name="aiagent",
            name="api_key_env",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
        migrations.CreateModel(
            name="AIModelConfig",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "provider",
                    models.CharField(
                        choices=[
                            ("deepseek", "deepseek"),
                            ("dashscope", "dashscope"),
                            ("govee", "govee"),
                        ],
                        max_length=32,
                    ),
                ),
                (
                    "api_key_env",
                    models.CharField(
                        choices=[
                            ("DEEPSEEK_API_KEY", "DEEPSEEK_API_KEY"),
                            ("DASHSCOPE_API_KEY", "DASHSCOPE_API_KEY"),
                            ("GOVEE_API_KEY", "GOVEE_API_KEY"),
                        ],
                        max_length=64,
                    ),
                ),
                ("base_url", models.CharField(blank=True, default="", max_length=500)),
                ("model_name", models.CharField(max_length=100)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "模型配置",
                "verbose_name_plural": "模型配置",
                "db_table": "ai_model_configs",
                "constraints": [
                    models.UniqueConstraint(
                        fields=("api_key_env", "model_name"),
                        name="uniq_ai_model_config_key_model",
                    )
                ],
            },
        ),
    ]
