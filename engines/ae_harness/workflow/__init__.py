"""
文件名: ➡️ __init__.py 🏁
路径: ➡️ engines/ae_harness/workflow/__init__.py 🏁
模块功能：➡️ 多智能体编排包：当前只有 SOP 一条链路 🏁
Python 调试：➡️ python -m engines.ae_harness.workflow 🏁
时间：➡️ 2026-11-13 🏁
作者：➡️ kahoku 🏁
版本：➡️ 0.1.0 🏁
修改时间: ➡️ 2026-11-13 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. 本包负责把多个角色按流程串起来，不定义角色、不造模型。
2. 当前只有 sop_runner：执行者与验收者按里程碑推进。
🏁
关联模块：➡️
1. engines.ae_harness.assistant: 单角色入口与运行时骨架。
2. engines.ae_harness.event: 记录与渲染。
3. agentscope.sop: 流程引擎。
🏁
测试：➡️
1. python -m engines.ae_harness.workflow.sop_runner "回到桌面再进设置"
🏁
"""
