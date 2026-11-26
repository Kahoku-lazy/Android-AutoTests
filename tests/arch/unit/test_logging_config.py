from __future__ import annotations

import logging

import pytest

from django.conf import settings

pytestmark = [pytest.mark.unit]


def test_root_logger_has_handlers():
    root = settings.LOGGING["root"]
    assert root["handlers"], "根 logger 无 handler：日志会被丢弃"
    assert root["level"] == settings.LOG_LEVEL


def test_console_handler_is_the_only_frame_handler():
    handlers = settings.LOGGING["handlers"]
    assert "console" in handlers
    assert "file" not in handlers


def test_django_and_daphne_loggers_configured():
    loggers = settings.LOGGING["loggers"]
    assert "django" in loggers and "daphne" in loggers
    for name in ("django", "daphne"):
        assert loggers[name]["handlers"] == settings.LOGGING["root"]["handlers"]
        assert loggers[name]["propagate"] is False


def test_root_logger_is_live_at_runtime():
    root = logging.getLogger()
    assert root.handlers, "运行时根 logger 无 handler：LOGGING 未生效"


def test_info_record_is_not_dropped(caplog):
    logger = logging.getLogger("backend.apps.logging_probe")
    with caplog.at_level(logging.INFO):
        logger.info("d0-log-probe")
    assert "d0-log-probe" in caplog.text
