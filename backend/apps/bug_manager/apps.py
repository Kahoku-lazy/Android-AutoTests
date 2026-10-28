"""bug-manager app configuration."""

from django.apps import AppConfig


class BugManagerConfig(AppConfig):
    """Register the BUG ticket ledger app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "backend.apps.bug_manager"
    verbose_name = "BUG 单管理"
