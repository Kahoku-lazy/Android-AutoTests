"""
文件名: ➡️ __init__.py 🏁
路径: ➡️ engines/ae_harness/agents/__init__.py 🏁
模块功能：➡️ 角色定义子包：配置读取、模型创建与 Agent 装配 🏁
Python 调试：➡️ python -m engines.ae_harness.agents 🏁
时间：➡️ 2026-11-13 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-13 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. 本包无公开符号：config / models / creator 三个模块各自独立，调用方按需导入。
2. 不在此处再导出，避免把「读配置 → 造模型 → 拼 Agent」的依赖方向藏进包入口。
🏁
关联模块：➡️
1. engines.ae_harness.agents.config: 读模型表与提示词正文。
2. engines.ae_harness.agents.models: 按短名造聊天模型。
3. engines.ae_harness.agents.creator: create_agent，唯一装配出口。
🏁
测试：➡️
1. 见 engines.ae_harness.assistant.agent_executor
🏁
"""
