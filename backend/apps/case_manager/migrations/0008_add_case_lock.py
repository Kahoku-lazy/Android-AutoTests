from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('case_manager', '0007_add_collab_tracking'),
    ]

    operations = [
        migrations.AddField(
            model_name='testdefinition',
            name='locked',
            field=models.BooleanField(default=False),
        ),
    ]
