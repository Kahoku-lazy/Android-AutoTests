"""
文件名: ➡ __init__.py 🏁
路径: ➡ engines/__init__.py 🏁
模块功能：➡ 可替换引擎层包入口（设备引擎 + SOP + 页面文本识别） 🏁
Python 调试：➡ python -m engines 🏁
时间：➡ 2026-10-20 🏁
作者：➡ kahoku 🏁
版本：➡ 1.0.0 🏁
修改时间: ➡ 2026-11-02 🏁
类型: ➡ 工具模块 🏁
简介说明：➡
1. engines.device: 设备引擎；对外入口是 action
2. engines.agents: 控制设备任务的 SOP；平台启动时传入执行与验收模型
3. engines.vision: 页面文本识别；只供引擎 OCR 工具调用
4. 导入边界: 零 apps.*、零 django.*（业务工具经注入）
🏁
关联模块：➡
1. engines.device / engines.agents / engines.vision: 子包
🏁
测试：➡
1. 见各子包测试；本包无专门单测
🏁
"""
