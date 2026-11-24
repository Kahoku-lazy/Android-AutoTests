from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('report_generator', '0002_alter_report_options_alter_reporttemplate_options'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Report',
        ),
        migrations.DeleteModel(
            name='ReportTemplate',
        ),
    ]
