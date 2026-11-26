from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("ai_assistant", "0085_eval_scores"),
    ]

    operations = [
        migrations.DeleteModel(
            name="AssistantEvalRun",
        ),
        migrations.RemoveField(
            model_name="assistantlivesample",
            name="run",
        ),
        migrations.DeleteModel(
            name="AssistantLiveSample",
        ),
        migrations.DeleteModel(
            name="AssistantLiveRun",
        ),
    ]
