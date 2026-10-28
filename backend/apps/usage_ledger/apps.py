"""Usage ledger app config."""

from django.apps import AppConfig


class UsageLedgerConfig(AppConfig):
    """模型用量明细账本。"""

    default_auto_field = "django.db.models.BigAutoField"
    name = "backend.apps.usage_ledger"
    verbose_name = "模型用量账本"
