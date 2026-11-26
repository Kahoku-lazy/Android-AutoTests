from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('case_manager', '0003_testdefinition_iot_fields'),
    ]

    operations = [
        migrations.DeleteModel(
            name='TestCaseCache',
        ),
    ]
