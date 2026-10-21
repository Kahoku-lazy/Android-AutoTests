from django.apps import AppConfig


class AccountsConfig(AppConfig):
    # Django 6: default_auto_field 是 cached_property，读 settings.DEFAULT_AUTO_FIELD
    name = "apps.accounts"
    label = "accounts"
    verbose_name = "平台认证"
