"""drf-spectacular 扩展：声明本平台的 Bearer JWT 认证方案。

背景：`REST_FRAMEWORK.DEFAULT_AUTHENTICATION_CLASSES` 指向自定义的 `JWTAuthentication`，
drf-spectacular 不认识它，会对**每一个端点**报一次
`W001 could not resolve authenticator <class shared.auth.drf_auth.JWTAuthentication>`。
这里注册一个 `OpenApiAuthenticationExtension`，把认证方案声明成标准的 `http bearer`，
使 `/api/schema` 与 `/api/swagger` 能正确展示并在 UI 里输入令牌。

注：drf-spectacular 通过「类定义即注册」的元类收集扩展，故本模块必须在生成 schema 前被导入；
`shared` 是注册在 `INSTALLED_APPS` 的应用，其根级 `schema.py` 由 drf-spectacular 自动加载。
"""

from drf_spectacular.extensions import OpenApiAuthenticationExtension


class JWTAuthenticationScheme(OpenApiAuthenticationExtension):
    """`shared.auth.drf_auth.JWTAuthentication` → OpenAPI `http bearer` 方案。"""

    target_class = "shared.auth.drf_auth.JWTAuthentication"
    name = "jwtAuth"

    def get_security_definition(self, auto_schema):
        """认证头的形状：`Authorization: Bearer <access_token>`。"""
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
