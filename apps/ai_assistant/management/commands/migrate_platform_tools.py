"""One-shot data migration: write all platform tool records for existing active agents.

Usage:
    python manage.py migrate_platform_tools [--dry-run]

After the factory.py change (no config → no tools), existing agents without
AITool records would lose all platform tools. This command ensures backward
compatibility by writing all 24 platform tool names as AITool records
(tool_type='platform', enabled=True) for every active agent that doesn't
already have platform tool records.
"""

from django.core.management.base import BaseCommand

from apps.ai_assistant.agent_scope.tool_registry import TOOL_SCHEMAS
from apps.ai_assistant.models import AIAgent, AITool


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview changes without writing to DB.",
        )

    def handle(self, **options):
        dry_run = options["dry_run"]
        tool_names = sorted(t["name"] for t in TOOL_SCHEMAS)
        self.stdout.write(f"Platform tools in registry: {len(tool_names)}")
        self.stdout.write(f"  {', '.join(tool_names[:8])}...")

        agents = AIAgent.objects.filter(status="active")
        created_total = 0
        skipped_total = 0

        for agent in agents:
            existing_platform = AITool.objects.filter(
                agent=agent,
                name__in=tool_names,
            ).values_list("name", flat=True)

            missing = [n for n in tool_names if n not in existing_platform]

            if not missing:
                skipped_total += 1
                continue

            if dry_run:
                self.stdout.write(
                    f"  [DRY-RUN] Agent #{agent.id} '{agent.name}': "
                    f"would create {len(missing)} tool records"
                )
            else:
                objs = [
                    AITool(
                        agent=agent,
                        name=name,
                        tool_type="platform",
                        config_json="{}",
                        enabled=True,
                    )
                    for name in missing
                ]
                AITool.objects.bulk_create(objs)
                created_total += 1
                self.stdout.write(
                    f"  Created {len(missing)} platform tools for Agent #{agent.id} '{agent.name}'"
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Agents updated: {created_total}, "
                f"already configured: {skipped_total}" + (" [DRY-RUN]" if dry_run else "")
            )
        )
