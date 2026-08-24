"""Root conftest — pytest_plugins 只能声明在 rootdir 顶层 conftest（pytest ≥ 8.1 起强制）。

tests/auth/e2e/conftest.py 需要加载 tests/e2e 的共享 fixtures（非父目录、不会自动加载），
因此在此顶层文件统一注册插件。
"""

pytest_plugins = ["tests.e2e.conftest"]
