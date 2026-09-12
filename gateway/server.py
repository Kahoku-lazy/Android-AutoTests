"""Gateway — [DEPRECATED] HTTP route registration has moved to per-app urls.py.

This file is kept for reference. Current routing:
  config/urls.py → include('apps.xxx.urls') → apps/xxx/urls.py

WebSocket routing remains in gateway/routing.py.
"""
# All HTTP routes are now registered in:
#   config/urls.py → include('apps.element_locator.urls')
#   config/urls.py → include('apps.device_pool.urls')
#   config/urls.py → include('apps.case_manager.urls')
#   config/urls.py → include('apps.report_generator.urls')
