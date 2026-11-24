from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('bug_manager', '0003_bug_case_identity'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bugticket',
            name='category',
            field=models.CharField(choices=[('ui_automation', 'UI 自动化'), ('case_authoring', '测试用例编写'), ('requirement_breakdown', '需求拆解')], db_index=True, max_length=32),
        ),
    ]
