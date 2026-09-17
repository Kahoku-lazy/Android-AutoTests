"""尾斜杠规范化中间件 —— 真机发现 #1 修复 + 双向容错。

最初只处理一个方向：无斜杠的 /api/ 请求若「带斜杠版路由存在」，直接重写 path_info 补斜杠，
避免 CommonMiddleware 的 301 重定向——部分客户端重定向时会丢 Authorization 头，
导致 JWT 中间件误报 401。

但本平台各 App 的路径约定并不统一（同一 App 内也可能混用：元素定位同时有 move/、
files/batch-delete/ 与 pages），Django 也没有"去斜杠"的对应机制（APPEND_SLASH 只追加），
所以反方向一直是 404：调用方多打一个 '/' 就失败，而平台无法给出统一写法。
故本中间件补齐反方向，使两种写法都能命中。

改写**只在原路径无法解析时**发生：若路径本身即可解析（例如同一资源同时注册了
x 与 x/），一律不动，按原路径命中——否则会把本该命中 A 路由的请求静默改写到 B 路由。

挂载于 MIDDLEWARE 最前（CommonMiddleware 之前）。
"""

from django.urls import Resolver404, get_resolver


def _resolves(resolver, path: str) -> bool:
    """该路径能否被解析（不看视图内部返回什么）。"""
    try:
        resolver.resolve(path)
        return True
    except Resolver404:
        return False


class NormalizeTrailingSlashMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        if path.startswith("/api/"):
            resolver = get_resolver()
            # 先判原路径：能解析就什么都不做（两种写法并存的资源语义不能被改写）
            if not _resolves(resolver, path):
                if not path.endswith("/"):
                    # 无斜杠请求 / 带斜杠版路由存在 → 补斜杠，消除 301
                    if _resolves(resolver, path + "/"):
                        request.path_info = path + "/"
                else:
                    # 带斜杠请求 / 无斜杠版路由存在 → 去斜杠，消除 404
                    stripped = path.rstrip("/")
                    if stripped and _resolves(resolver, stripped):
                        request.path_info = stripped
        return self.get_response(request)
