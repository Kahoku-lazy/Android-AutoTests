"""串口日志 App 配置：平台启动时按持久化开关恢复端口监听。"""

import os
import sys
import threading

from django.apps import AppConfig

from utils.logs import backend_log


class SerialLogConfig(AppConfig):
    """串口日志模块的 App 配置。"""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.serial_log"
    verbose_name = "串口日志"

    def ready(self):
        """仅在 ASGI 服务进程起后台线程恢复监听；管理命令不触发。

        `migrate` / `shell` / 测试进程绝不能触发——否则会在建表前查库，
        或在测试里顺手占用现场日志端口。
        """
        argv = " ".join(sys.argv)
        is_asgi_server = (
            os.environ.get("DJANGO_ASGI_SERVER") == "1" or "daphne" in argv or "runserver" in argv
        )
        if not is_asgi_server:
            return

        threading.Thread(
            target=self._restore_ports,
            name="serial-log-startup-restore",
            daemon=True,
        ).start()

    def _restore_ports(self):
        """等 apps 完全 ready 后按开关恢复监听，避免装配期访问数据库。"""
        from django.apps import apps as django_apps

        django_apps.ready_event.wait()

        # autoreload 的父进程只做文件监控：它若先占用日志端口，真正服务的
        # 子进程反而一条日志都收不到。
        if (
            os.environ.get("DJANGO_AUTORELOAD_PARENT") == "1"
            and os.environ.get("RUN_MAIN") != "true"
        ):
            backend_log.info("Skip device log port restore in autoreload parent process")
            return
        try:
            from . import port_service

            enabled = port_service.reconcile()
            backend_log.info("Device log ports enabled after startup: %s", enabled)
        except Exception as e:
            backend_log.exception("Device log port restore failed: %s", e)
