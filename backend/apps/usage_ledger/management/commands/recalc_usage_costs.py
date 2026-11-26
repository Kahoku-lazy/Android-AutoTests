from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError
from django.db import OperationalError, ProgrammingError

from backend.apps.usage_ledger.api import recalculate_usage_costs


class Command(BaseCommand):
    help = "从 ai_usage_records 读 token 用量，按当前价目重算并回写费用。"

    def add_arguments(self, parser) -> None:
        parser.add_argument("--provider", default="", help="只重算该厂商：deepseek / dashscope")
        parser.add_argument("--source", default="", help="只重算该来源：task / voice / chat")
        parser.add_argument("--batch-size", type=int, default=500, help="每批行数")
        parser.add_argument("--dry-run", action="store_true", help="只计算，不写库")

    def handle(self, *args, **options) -> None:
        try:
            result = recalculate_usage_costs(
                provider=str(options.get("provider") or ""),
                source=str(options.get("source") or ""),
                batch_size=int(options.get("batch_size") or 500),
                dry_run=bool(options.get("dry_run")),
            )
        except (OperationalError, ProgrammingError) as exc:
            raise CommandError(f"重算失败：ai_usage_records 不可访问（{exc}）") from exc
        self.stdout.write(
            "扫描 {scanned} 条，变更 {changed} 条；费用 {before} -> {after} 元".format(
                scanned=result["scanned"],
                changed=result["changed"],
                before=f"{result['cost_before']:.8f}",
                after=f"{result['cost_after']:.8f}",
            )
        )
