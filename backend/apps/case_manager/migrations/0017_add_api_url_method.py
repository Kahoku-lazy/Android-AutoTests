from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('case_manager', '0016_add_web_testcase'),
    ]

    operations = [
        migrations.AddField(
            model_name='apitestcase',
            name='method',
            field=models.CharField(blank=True, default='GET', max_length=10, verbose_name='HTTP 方法'),
        ),
        migrations.AddField(
            model_name='apitestcase',
            name='url',
            field=models.TextField(blank=True, default='', verbose_name='请求 URL'),
        ),
    ]
