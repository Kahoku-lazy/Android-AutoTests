from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('serial_log', '0003_logport_origin'),
    ]

    operations = [
        migrations.CreateModel(
            name='LogKeyword',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('keyword', models.CharField(max_length=200)),
                ('feature_id', models.IntegerField()),
                ('module', models.CharField(max_length=100)),
                ('feature', models.CharField(max_length=200)),
                ('scope', models.CharField(default='*', max_length=100)),
                ('sort_order', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': '日志关键词对照',
                'verbose_name_plural': '日志关键词对照',
                'db_table': 'sl_log_keywords',
                'ordering': ['sort_order', 'id'],
                'indexes': [models.Index(fields=['scope'], name='sl_kw_scope_idx')],
                'constraints': [models.UniqueConstraint(fields=('keyword', 'feature_id', 'scope'), name='uniq_sl_kw_keyword_feature_scope')],
            },
        ),
    ]
