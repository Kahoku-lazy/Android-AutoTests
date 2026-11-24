"""
模块功能：➡️ drf-spectacular 扩展：声明本平台的 Bearer JWT 认证方案 🏁
Python 调试：➡️ python -m backend.shared.schema 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. 暂无（经 shared 的功能用例间接覆盖，未直接 import 本模块）
🏁
"""

from drf_spectacular.extensions import OpenApiAuthenticationExtension


class JWTAuthenticationScheme(OpenApiAuthenticationExtension):
    """`backend.shared.auth.drf_auth.JWTAuthentication` → OpenAPI `http bearer` 方案。"""

    target_class = "backend.shared.auth.drf_auth.JWTAuthentication"
    name = "jwtAuth"

    def get_security_definition(self, auto_schema):
        """认证头的形状：`Authorization: Bearer <access_token>`。"""
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
