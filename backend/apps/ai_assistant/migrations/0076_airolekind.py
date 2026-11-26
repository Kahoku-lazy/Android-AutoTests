import django.db.models.deletion
from django.db import migrations, models

_KIND_TOKENS = (
    ("EXECUTOR", "executor"),
    ("VERIFIER", "verifier"),
    ("PLANNER", "planner"),
)


def _kind_of(name: str) -> str:
    tokens = str(name or "").upper().replace("-", "_").split("_")
    for token, kind in _KIND_TOKENS:
        if token in tokens:
            return kind
    return ""


def backfill_kinds(apps, schema_editor):
    AIRole = apps.get_model("ai_assistant", "AIRole")
    AIRoleKind = apps.get_model("ai_assistant", "AIRoleKind")
    rows = []
    for role in AIRole.objects.all().only("id", "role_id", "name"):
        kind = _kind_of(role.name) or _kind_of(role.role_id)
        if kind:
            rows.append(AIRoleKind(role_id=role.id, kind=kind))
    AIRoleKind.objects.bulk_create(rows)


def clear_kinds(apps, schema_editor):
    AIRoleKind = apps.get_model("ai_assistant", "AIRoleKind")
    AIRoleKind.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ('ai_assistant', '0075_aisopworkflow'),
    ]

    operations = [
        migrations.CreateModel(
            name='AIRoleKind',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('kind', models.CharField(choices=[('executor', '执行者'), ('verifier', '验收者'), ('planner', '规划者')], max_length=16)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('role', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='kinds', to='ai_assistant.airole')),
            ],
            options={
                'verbose_name': 'Agent配置类型',
                'verbose_name_plural': 'Agent配置类型',
                'db_table': 'ai_role_kinds',
                'constraints': [models.UniqueConstraint(fields=('role',), name='uniq_ai_role_kind_role'), models.UniqueConstraint(fields=('role', 'kind'), name='uniq_ai_role_kind_pair')],
            },
        ),
        migrations.RunPython(backfill_kinds, clear_kinds),
    ]
