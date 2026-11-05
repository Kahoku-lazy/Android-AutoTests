"""清空存量超长头像：ai_agents.avatar 与 route_configs.*.avatar。

只清长度超过 4096 字符的值（都是误写入的 MB 级 base64），不触碰其它字段。
可重复执行；反向迁移不做数据恢复（原始值已无业务意义）。
"""

from __future__ import annotations

from django.db import migrations

MAX_AVATAR_CHARS = 4096


def trim_oversized_avatars(apps, schema_editor):
    """把超长头像字段置空。"""
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
    """递归清理 route_configs 里超长的 avatar 值；有改动返回 True。"""
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
