"""内部令牌中间件 — 保护工具网关前缀 `/api/ai/tools/`。

该前缀在 `gateway.middleware.PUBLIC_PREFIXES` 中豁免 JWT（服务间调用不持有用户令牌），
因此必须另设一道凭据：请求头 `X-Internal-Token` 必须等于 `settings.AI_TOOL_GATEWAY_TOKEN`。

fail-closed：令牌未配置时该前缀一律 401。「未配置就放开」会让这道防线变成空防线。
"""

import hmac
import logging

from django.conf import settings
from django.http import JsonResponse

logger = logging.getLogger("gateway.internal_token")

# 受保护前缀（与 gateway.middleware.PUBLIC_PREFIXES 中的 /api/ai/tools/ 对应）
PROTECTED_PREFIX = "/api/ai/tools/"
TOKEN_META_KEY = "HTTP_X_INTERNAL_TOKEN"

# 统一文案：不暴露「令牌未配置」还是「令牌不匹配」
_UNAUTHORIZED_PAYLOAD = {"status": False, "message": "内部令牌无效"}


def _token_matches(provided: str, expected: str) -> bool:
    """常量时间比较，避免时序侧信道。"""
    return hmac.compare_digest(provided.encode("utf-8"), expected.encode("utf-8"))


class InternalToolTokenMiddleware:
    """只校验工具网关前缀；其余请求直接放行（不改变既有中间件语义）。"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # CORS 预检不携带自定义头，也不应被凭据校验拦截
        if request.method == "OPTIONS" or not request.path.startswith(PROTECTED_PREFIX):
            return self.get_response(request)

        expected = getattr(settings, "AI_TOOL_GATEWAY_TOKEN", "")
        provided = request.META.get(TOKEN_META_KEY, "")
        if not expected or not provided or not _token_matches(provided, expected):
            logger.warning("工具网关凭据校验失败: %s", request.path)
            return JsonResponse(_UNAUTHORIZED_PAYLOAD, status=401)

        return self.get_response(request)
