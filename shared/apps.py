"""`shared` 应用配置 — 在 app 就绪时注册 drf-spectacular 扩展。"""

from django.apps import AppConfig


class SharedConfig(AppConfig):
    """`shared` 的 AppConfig：`ready()` 里导入 `schema` 模块完成扩展注册。"""

    name = "shared"
    verbose_name = "Shared 基础设施"

    def ready(self):
        # drf-spectacular 通过「类定义即注册」的元类收集扩展，因此模块必须在生成 schema 前被导入。
        # 放在 ready() 而不是模块顶层：确保 django.setup() 之后、任何 schema 生成之前完成注册。
        from . import schema  # noqa: F401
