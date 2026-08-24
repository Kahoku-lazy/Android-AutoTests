"""case-manager shared view helpers — re-export 自 shared 层（fix-cross-app-firewall）。

resolve_username 为通用能力，已下沉 shared/users.py；此处 re-export 仅保
本 App 内部兼容，跨 App 请直接 import shared.users。
"""

import logging

from shared.users import resolve_username  # noqa: F401

logger = logging.getLogger(__name__)
