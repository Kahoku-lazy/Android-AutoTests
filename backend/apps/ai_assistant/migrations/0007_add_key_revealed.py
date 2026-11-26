from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('ai_assistant', '0006_add_content_blocks_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='aiagent',
            name='key_revealed',
            field=models.BooleanField(default=False),
        ),
    ]
