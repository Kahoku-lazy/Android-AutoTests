from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('serial_log', '0002_copy_port_state'),
    ]

    operations = [
        migrations.AddField(
            model_name='logport',
            name='origin',
            field=models.CharField(choices=[('config', '配置'), ('custom', '自定义')], default='config', max_length=10),
        ),
    ]
