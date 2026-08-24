"""通用用户工具 — 跨 App 可 import 的共享能力（shared 层）。"""

import logging

logger = logging.getLogger(__name__)


def resolve_username(user_id):
    """Convert Django user ID to username string. Already-usernames pass through."""
    if not user_id:
        return ""
    s = str(user_id)
    if not s.isdigit():
        return s
    try:
        from django.contrib.auth.models import User

        return User.objects.get(id=int(s)).username
    except Exception:
        return s
