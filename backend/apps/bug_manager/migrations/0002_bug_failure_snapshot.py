from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('bug_manager', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='bugticket',
            name='failure',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
