"""D0 日志配置契约：`LOGGING` 必须真正生效（不再依赖从未设置的 DOCKER_CONTAINER）。"""

from __future__ import annotations

import logging
import os

import pytest

from django.conf import settings

pytestmark = [pytest.mark.unit]


def test_root_logger_has_handlers():
    """根 logger 必须配置 handler —— 否则应用级 INFO 日志会被静默丢弃。"""
    root = settings.LOGGING["root"]
    assert root["handlers"], "根 logger 无 handler：日志会被丢弃"
    assert root["level"] == settings.LOG_LEVEL


def test_local_slot_has_console_and_file():
    """本地档位：控制台 + logs/django.log（容器档位只有 stdout）。"""
    handlers = settings.LOGGING["handlers"]
    assert "console" in handlers
    is_container = os.environ.get("DOCKER_CONTAINER", "").lower() in ("true", "1", "yes")
    if not is_container:
        assert "file" in handlers
        assert handlers["file"]["filename"].replace("\\", "/").endswith("logs/django.log")
        assert handlers["file"].get("delay") is True


def test_django_and_daphne_loggers_configured():
    """django / daphne 两个框架 logger 显式配置且不重复传播。"""
    loggers = settings.LOGGING["loggers"]
    assert "django" in loggers and "daphne" in loggers
    for name in ("django", "daphne"):
        assert loggers[name]["handlers"] == settings.LOGGING["root"]["handlers"]
        assert loggers[name]["propagate"] is False


def test_root_logger_is_live_at_runtime():
    """运行时根 logger 确实挂着 handler（Django dictConfig 已应用）。"""
    root = logging.getLogger()
    assert root.handlers, "运行时根 logger 无 handler：LOGGING 未生效"


def test_info_record_is_not_dropped(caplog):
    """应用级 logger 的 INFO 记录能被捕获（此前无 handler 时会被丢弃）。"""
    logger = logging.getLogger("apps.logging_probe")
    with caplog.at_level(logging.INFO):
        logger.info("d0-log-probe")
    assert "d0-log-probe" in caplog.text
