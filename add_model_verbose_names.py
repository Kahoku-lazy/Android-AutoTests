#!/usr/bin/env python3
"""给所有 Django Model 的 Meta 类添加 verbose_name / verbose_name_plural 中文名

   用法: python3 add_model_verbose_names.py
   效果: 修改 6 个 App 下 18 个 Model 的 Meta，添加中文 verbose_name
"""

import re
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))

# 每个模型: (文件路径, 类名, 单数中文名, 复数中文名)
MODELS = [
    # device_pool — 设备管理
    ("apps/device_pool/models.py", "Device", "设备", "设备"),
    ("apps/device_pool/models.py", "DeviceLock", "设备锁", "设备锁"),
    ("apps/device_pool/models.py", "DeviceQueue", "设备队列", "设备队列"),
    # element_locator — 元素定位
    ("apps/element_locator/models.py", "Page", "页面", "页面"),
    ("apps/element_locator/models.py", "Element", "元素", "元素"),
    ("apps/element_locator/models.py", "PageFlow", "页面跳转流", "页面跳转流"),
    # case_manager — 用例工程
    ("apps/case_manager/models.py", "CaseDirectory", "用例目录", "用例目录"),
    ("apps/case_manager/models.py", "TestDefinition", "用例定义", "用例定义"),
    # test_runner — 执行引擎
    ("apps/test_runner/models.py", "TestSOP", "测试SOP上下文", "测试SOP上下文"),
    ("apps/test_runner/models.py", "TestRunRecord", "测试运行记录", "测试运行记录"),
    ("apps/test_runner/models.py", "TestResult", "测试结果", "测试结果"),
    # report_generator — 报告分析
    ("apps/report_generator/models.py", "Report", "报告", "报告"),
    ("apps/report_generator/models.py", "ReportTemplate", "报告模板", "报告模板"),
    # ai_assistant — AI 助手
    ("apps/ai_assistant/models.py", "AIAgent", "智能体", "智能体"),
    ("apps/ai_assistant/models.py", "AITool", "工具配置", "工具配置"),
    ("apps/ai_assistant/models.py", "AIConversation", "对话", "对话"),
    ("apps/ai_assistant/models.py", "AIMessage", "消息", "消息"),
    ("apps/ai_assistant/models.py", "AITask", "任务", "任务"),
    ("apps/ai_assistant/models.py", "AIExecutionLog", "执行日志", "执行日志"),
]


def add_verbose_name(filepath, class_name, vn, vnp):
    """在指定 Model 的 class Meta 中添加 verbose_name，不修改已有字段"""
    full = os.path.join(BASE, filepath)
    with open(full, "r") as f:
        content = f.read()

    # 找到该类定义中包含 Meta 的部分
    # 策略：在 db_table 行之后插入 verbose_name
    pattern = rf"(class {class_name}\(.*?class Meta:.*?db_table\s*=\s*'[^']*')"
    replacement = rf"\1\n        verbose_name = '{vn}'\n        verbose_name_plural = '{vnp}'"

    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL, count=1)

    if new_content == content:
        # 尝试备选模式：db_table 用双引号
        pattern2 = rf'(class {class_name}\(.*?class Meta:.*?db_table\s*=\s*"[^"]*")'
        replacement2 = rf'\1\n        verbose_name = "{vn}"\n        verbose_name_plural = "{vnp}"'
        new_content = re.sub(pattern2, replacement2, content, flags=re.DOTALL, count=1)

    if new_content == content:
        print(f"  ✗ {class_name}: 未匹配到 db_table（可能已存在或格式不同）")
        return False

    with open(full, "w") as f:
        f.write(new_content)
    print(f"  ✓ {class_name} → {vn}")
    return True


if __name__ == "__main__":
    ok = 0
    fail = 0
    for fp, cls, vn, vnp in MODELS:
        full = os.path.join(BASE, fp)
        if not os.path.exists(full):
            print(f"  ✗ {cls}: 文件不存在 {fp}")
            fail += 1
            continue
        if add_verbose_name(fp, cls, vn, vnp):
            ok += 1
        else:
            fail += 1

    print(f"\n完成: {ok} 成功, {fail} 失败")
    if fail > 0:
        print("部分模型可能需要手动添加 verbose_name")
        sys.exit(1)
