"""
文件名: ➡️ __init__.py 🏁
路径: ➡️ engines/backend_bridge/model_billing/__init__.py 🏁
模块功能：➡️ 平台侧模型费用计算子包：对外只导出 DeepSeekBilling 🏁
Python 调试：➡️ python -m engines.backend_bridge.model_billing 🏁
时间：➡️ 2026-11-15 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-15 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. 本子包是平台侧唯一的模型费用计算，价目与计费规则以 billing.py 为准。
2. 后端调用时只认 DeepSeekBilling：cost 出三项金额，snapshot 出本次取价快照。
3. 平台可从 ai_usage_records 读 token 后调 cost 重算费用；读库在 backend，本模块不碰数据库。
4. 不打印：金额通过返回值交给后端写账。
🏁
关联模块：➡️
1. engines.backend_bridge.model_billing.billing: 导入 DeepSeekBilling，唯一公开入口。
🏁
测试：➡️
1. tests/engines/backend_bridge/unit/test_model_billing.py: 8 位小数、未知模型免费、快照字段、高峰倍率
🏁
"""

from __future__ import annotations

from .billing import DeepSeekBilling

__all__ = ["DeepSeekBilling"]
