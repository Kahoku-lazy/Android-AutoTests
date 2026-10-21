# Generated manually: attachment CharField→TextField；新增 attachment_filename / device_label

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ai_assistant", "0036_aitask_by_role"),
    ]

    operations = [
        migrations.AlterField(
            model_name="aitask",
            name="attachment",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="aitask",
            name="attachment_filename",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="aitask",
            name="device_label",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
    ]
