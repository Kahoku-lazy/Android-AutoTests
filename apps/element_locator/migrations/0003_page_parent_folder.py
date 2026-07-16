# Generated manually — page tree folders

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('element_locator', '0002_unique_page_label'),
    ]

    operations = [
        migrations.AlterField(
            model_name='page',
            name='label',
            field=models.CharField(blank=True, default='', max_length=500),
        ),
        migrations.AddField(
            model_name='page',
            name='parent',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='children',
                to='element_locator.page',
            ),
        ),
        migrations.AddField(
            model_name='page',
            name='is_folder',
            field=models.BooleanField(default=False),
        ),
    ]
