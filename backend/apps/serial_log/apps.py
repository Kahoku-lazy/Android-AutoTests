import os
import sys
import threading

from django.apps import AppConfig

from utils.logs import backend_log


class SerialLogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "backend.apps.serial_log"
    verbose_name = "串口日志"

    def ready(self):
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
        from django.apps import apps as django_apps

        django_apps.ready_event.wait()

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
