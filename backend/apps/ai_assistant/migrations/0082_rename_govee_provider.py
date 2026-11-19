"""把已保存的 govee 厂商改名为 openai。

历史 choices 留在 0067。本迁移只改库里的值，让旧配置在新代码下仍能读出来。
"""

from django.db import migrations


def forwards(apps, schema_editor):
    """govee / GOVEE_API_KEY 改成 openai / OPENAI_API_KEY。"""
    config = apps.get_model("ai_assistant", "AIModelConfig")
    config.objects.filter(provider="govee").update(provider="openai")
    config.objects.filter(api_key_env="GOVEE_API_KEY").update(api_key_env="OPENAI_API_KEY")


def backwards(apps, schema_editor):
    """回退时把 openai 厂商改回 govee。协议字段 openai 不动。"""
    config = apps.get_model("ai_assistant", "AIModelConfig")
    config.objects.filter(provider="openai").update(provider="govee")
    config.objects.filter(api_key_env="OPENAI_API_KEY").update(api_key_env="GOVEE_API_KEY")


class Migration(migrations.Migration):
    dependencies = [
        ("ai_assistant", "0081_assistant_live_eval"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
