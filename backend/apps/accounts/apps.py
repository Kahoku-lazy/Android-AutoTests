"""平台认证应用。用户存在 Django 内置用户表；本应用自有表只有 `acc_token_revocations`（`models.TokenRevocation`，登出吊销记录，落库不依赖 Redis）。"""

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    # Django 6: default_auto_field 是 cached_property，读 settings.DEFAULT_AUTO_FIELD
    name = "backend.apps.accounts"
    label = "accounts"
    verbose_name = "平台认证"
