"""ai-assistant view decorators — re-export 自 shared 层（fix-cross-app-firewall）。

require_auth 为通用鉴权能力，已下沉 shared/auth/require_auth.py；此处 re-export
仅保本 App 内部兼容，跨 App 请直接 import shared.auth.require_auth。
"""

from shared.auth.require_auth import require_auth  # noqa: F401
