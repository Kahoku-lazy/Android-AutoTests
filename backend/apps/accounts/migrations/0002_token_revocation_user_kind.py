from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tokenrevocation',
            name='kind',
            field=models.CharField(choices=[('session', '会话'), ('token', '单令牌'), ('user', '停用账号')], max_length=16, verbose_name='吊销粒度'),
        ),
    ]
