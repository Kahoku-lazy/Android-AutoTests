from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("evaluator", "0002_framework_field"),
    ]

    operations = [
        migrations.DeleteModel(name="EvalResult"),
        migrations.DeleteModel(name="EvalRun"),
        migrations.DeleteModel(name="Question"),
        migrations.DeleteModel(name="QuestionBank"),
    ]
