from django.db import migrations


def forwards(apps, schema_editor):
    config = apps.get_model("ai_assistant", "AIModelConfig")
    config.objects.filter(provider="govee").update(provider="openai")
    config.objects.filter(api_key_env="GOVEE_API_KEY").update(api_key_env="OPENAI_API_KEY")


def backwards(apps, schema_editor):
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
