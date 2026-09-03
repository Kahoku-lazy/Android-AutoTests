"""项目根 conftest — 保留给跨层全局钩子。

三层测试框架（api / graybox / e2e / arch）的共享 fixture 定义在各自目录的 conftest.py 中，
pytest 按目录层级自动加载，无需 pytest_plugins 手动注册。
"""
