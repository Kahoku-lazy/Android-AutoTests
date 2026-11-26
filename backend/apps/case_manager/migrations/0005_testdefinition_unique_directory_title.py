from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('case_manager', '0004_delete_testcasecache'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='testdefinition',
            constraint=models.UniqueConstraint(fields=('directory', 'title'), name='unique_directory_title'),
        ),
    ]
