"""运营后台 App（注册用）。

只提供 `/api/ops/*` 管理接口，没有自有数据表：账号数据全部经
`backend.apps.accounts` 的 `api.py` 读写。
"""

from django.apps import AppConfig


class OpsConsoleConfig(AppConfig):
    """运营后台模块的 App 配置。"""

    default_auto_field = "django.db.models.BigAutoField"
    name = "backend.apps.ops_console"
    verbose_name = "运营后台"
