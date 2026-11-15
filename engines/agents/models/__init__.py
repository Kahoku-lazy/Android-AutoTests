"""
文件名: ➡️ __init__.py 🏁
路径: ➡️ engines/agents/models/__init__.py 🏁
模块功能：➡️ 新模型层门面：唯一出口 create_model 🏁
Python 调试：➡️ python -m engines.agents.models 🏁
时间：➡️ 2026-11-11 🏁
作者：➡️ kahoku 🏁
版本：➡️ 3.0.0 🏁
修改时间: ➡️ 2026-11-11 🏁
类型: ➡️ 模型配置模块 🏁
简介说明：➡️
1. create_model(整张表, 短名) → 模型实例；用哪个模型由 agent 决定。
2. 内部三层：schema 定义形状、loader 按族校验解析、create 分派构造。
3. 密钥由 config 加密后注入条目，本包只调 reveal()，不参与加解密。
4. 本包是模型实例的唯一创建出口；查规格走 config.model_view。
🏁
关联模块：➡️
1. engines.agents.config.config: load_model_config 读表并注入加密密钥（调用方使用）。
2. engines.agents.models.create: create_model 的实现。
3. engines.agents.models.schema: 参数类与 ModelConfigError。
🏁
测试：➡️
1. 待功能定型后补：四族创建、视觉选路与密钥打码
🏁
"""

from __future__ import annotations

from .create import create_model
from .schema import ModelConfigError

__all__ = ["ModelConfigError", "create_model"]
