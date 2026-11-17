"""
文件名: ➡️ __init__.py 🏁
路径: ➡️ engines/backend_bridge/models/__init__.py 🏁
模块功能：➡️ 导出平台侧模型名单查询 🏁
Python 调试：➡️ python -m engines.backend_bridge.models 🏁
时间：➡️ 2026-11-16 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-16 🏁
类型: ➡️ 模型配置模块 🏁
简介说明：➡️
1. discover_models: 平台查询厂商模型名单的唯一出口。
2. 本包不读密钥明文给调用方，不写库。
🏁
关联模块：➡️
1. engines.backend_bridge.models.discover: 真正发查询请求。
🏁
测试：➡️
1. tests/engines/backend_bridge/unit/test_model_discover.py: 查询失败改手填。
🏁
"""

from .discover import discover_models

__all__ = ["discover_models"]
