from pathlib import Path

import yaml

from django.db import migrations


def seed_modules(apps, schema_editor):
    module_model = apps.get_model("knowledge_search", "KnowledgeModule")
    if module_model.objects.exists():
        return
    bases_path = (
        Path(__file__).resolve().parents[4]
        / "engines"
        / "ae_harness"
        / "knowledge"
        / "config"
        / "knowledge_bases.yaml"
    )
    try:
        raw = yaml.safe_load(bases_path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return
    if not isinstance(raw, dict):
        return
    for name, entry in raw.items():
        if name == "defaults" or not isinstance(entry, dict):
            continue
        description = str(entry.get("description") or "").strip()
        data_dir = str(entry.get("data_dir") or "").strip()
        if not description or not data_dir:
            continue
        dir_path = Path(data_dir)
        if not dir_path.is_absolute():
            dir_path = bases_path.parent / dir_path
        module_model.objects.create(
            name=str(name),
            description=description[:200],
            data_dir=str(dir_path.resolve()),
            enabled=bool(entry.get("enabled", True)),
        )


class Migration(migrations.Migration):
    dependencies = [
        ("knowledge_search", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_modules, migrations.RunPython.noop),
    ]