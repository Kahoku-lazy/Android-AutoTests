"""知识库全局检索配置，种子用调过的阈值 0.45。

0.55 会漏掉「缺水提醒」这类短查询（实测最高 0.549），故种子不用代码默认 0.55。
向量模型指向 ai_model_configs 中 dashscope 的 text-embedding-v4；该行由
ai_assistant.0084 种入。找不到时不插入，检索会返回「检索不可用」。
"""

from django.db import migrations, models

_EMBEDDING_KEY = "DASHSCOPE_API_KEY"
_EMBEDDING_MODEL = "text-embedding-v4"


def seed_settings(apps, schema_editor):
    """表为空时写入一行检索配置，指向已种入的向量模型。"""
    settings_model = apps.get_model("knowledge_search", "RetrievalSettings")
    if settings_model.objects.exists():
        return
    config = apps.get_model("ai_assistant", "AIModelConfig")
    embedding = config.objects.filter(
        api_key_env=_EMBEDDING_KEY, model_name=_EMBEDDING_MODEL
    ).first()
    if embedding is None:
        return
    settings_model.objects.create(
        embedding_model_id=embedding.id,
        top_k=4,
        score_threshold=0.45,
        chunk_size=400,
        chunk_overlap=60,
        index_epoch=0,
    )


class Migration(migrations.Migration):

    dependencies = [
        ("ai_assistant", "0084_aimodelconfig_dimensions"),
        ("knowledge_search", "0004_ksevalrun_phase"),
    ]

    operations = [
        migrations.CreateModel(
            name="RetrievalSettings",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("embedding_model_id", models.PositiveIntegerField()),
                ("top_k", models.PositiveIntegerField(default=4)),
                ("score_threshold", models.FloatField(default=0.45)),
                ("chunk_size", models.PositiveIntegerField(default=400)),
                ("chunk_overlap", models.PositiveIntegerField(default=60)),
                ("index_epoch", models.PositiveIntegerField(default=0)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "知识库检索配置",
                "verbose_name_plural": "知识库检索配置",
                "db_table": "ks_retrieval_settings",
            },
        ),
        migrations.RunPython(seed_settings, migrations.RunPython.noop),
    ]
