from __future__ import annotations

from django.db import migrations

MAX_AVATAR_CHARS = 4096


def trim_oversized_avatars(apps, schema_editor):
    AIAgent = apps.get_model("ai_assistant", "AIAgent")
    for agent in AIAgent.objects.all().only("id", "avatar", "route_configs"):
        changed_fields = []

        avatar = agent.avatar or ""
        if len(avatar) > MAX_AVATAR_CHARS:
            agent.avatar = ""
            changed_fields.append("avatar")

        route_configs = agent.route_configs
        if isinstance(route_configs, dict) and _trim_routes(route_configs):
            agent.route_configs = route_configs
            changed_fields.append("route_configs")

        if changed_fields:
            agent.save(update_fields=changed_fields)


def _trim_routes(route_configs: dict) -> bool:
    changed = False
    for route_data in route_configs.values():
        if not isinstance(route_data, dict):
            continue
        avatar = route_data.get("avatar")
        if isinstance(avatar, str) and len(avatar) > MAX_AVATAR_CHARS:
            route_data["avatar"] = ""
            changed = True
    return changed


class Migration(migrations.Migration):
    dependencies = [
        ("ai_assistant", "0062_agent02_flash_model"),
    ]

    operations = [
        migrations.RunPython(trim_oversized_avatars, migrations.RunPython.noop),
    ]
