"""模型配置增加向量维度，并在缺失时种入知识库现用的嵌入模型。

已有同一密钥与模型名的行不覆盖：运营改过的值保持原样。
"""

from django.db import migrations, models

_EMBEDDING_KEY = "DASHSCOPE_API_KEY"
_EMBEDDING_MODEL = "text-embedding-v4"


def seed_embedding(apps, schema_editor):
    """不存在 dashscope 的 text-embedding-v4 时插入一条向量模型。"""
    config = apps.get_model("ai_assistant", "AIModelConfig")
    if config.objects.filter(api_key_env=_EMBEDDING_KEY, model_name=_EMBEDDING_MODEL).exists():
        return
    config.objects.create(
        provider="dashscope",
        api_key_env=_EMBEDDING_KEY,
        api_protocol="dashscope",
        model_kind="embedding",
        model_name=_EMBEDDING_MODEL,
        dimensions=1024,
        base_url="",
        voice="",
    )


class Migration(migrations.Migration):

    dependencies = [
        ("ai_assistant", "0083_alter_provider_choices"),
    ]

    operations = [
        migrations.AddField(
            model_name="aimodelconfig",
            name="dimensions",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.RunPython(seed_embedding, migrations.RunPython.noop),
    ]
