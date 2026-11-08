"""
文件名: ➡ __init__.py 🏁
路径: ➡ engines/device/__init__.py 🏁
模块功能：➡ 设备引擎包入口；对外只使用 action 🏁
Python 调试：➡ python -m engines.device 🏁
时间：➡ 2026-10-20 🏁
作者：➡ kahoku 🏁
版本：➡ 1.0.0 🏁
修改时间: ➡ 2026-11-02 🏁
类型: ➡ 工具模块 🏁
简介说明：➡
1. 设备引擎包：连接 / 信息 / 控制动作由 engines.device.action 统一导出
2. Android 实现由 action 按系统加载，调用方不直接依赖 android 子包
🏁
关联模块：➡
1. engines.device.action: 对外动作与系统解析入口
🏁
测试：➡
1. tests/engines/devices/test_android_device.py: Android 设备控制
2. tests/engines/agents/test_tool_device.py: 设备工具封装
🏁
"""
