"""
模块功能：➡️ Central WebSocket URL routing — aggregates all module consumers. 🏁
Python 调试：➡️ python -m backend.gateway.routing 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. tests/arch/unit/test_channels.py: 覆盖本模块
🏁
"""

from django.urls import URLPattern

websocket_urlpatterns: list[URLPattern] = []
