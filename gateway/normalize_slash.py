"""尾斜杠规范化中间件 — 真机发现 #1 修复。

无尾斜杠的 /api/ 请求若"带斜杠版路由存在"，直接重写 path_info 补斜杠，
避免 CommonMiddleware 的 301 重定向——部分客户端重定向时会丢 Authorization
头，导致 JWT 中间件误报 401。挂载于 MIDDLEWARE 最前（CommonMiddleware 之前）。
"""

from django.urls import Resolver404, get_resolver


class NormalizeTrailingSlashMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        if path.startswith("/api/") and not path.endswith("/"):
            resolver = get_resolver()
            try:
                # 无斜杠版路由存在（如 /api/runner/tasks）→ 原生无斜杠约定，不动
                resolver.resolve(path)
            except Resolver404:
                try:
                    # 仅带斜杠版存在 → 补斜杠，消除 301
                    resolver.resolve(path + "/")
                    request.path_info = path + "/"
                except Resolver404:
                    pass
        return self.get_response(request)
