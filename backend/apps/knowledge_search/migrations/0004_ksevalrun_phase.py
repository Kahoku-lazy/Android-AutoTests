from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('knowledge_search', '0003_ksevalrun_ksevalquery'),
    ]

    operations = [
        migrations.AddField(
            model_name='ksevalrun',
            name='phase',
            field=models.CharField(blank=True, default='', max_length=16),
        ),
    ]
