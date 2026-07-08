#!/usr/bin/env python3
"""修复 add_model_verbose_names.py 产生的缩进错误

   根本原因：部分 Model 的 Meta 类是单行格式 `class Meta: db_table = 'xxx'`
   脚本在匹配到的 db_table 后追加了 verbose_name，但缩进上下文错误。

   修复策略：重新读取每个文件，移除错误的 verbose_name 行，
   然后在每个 class Meta 块中正确插入 verbose_name。
"""

import re
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))

MODELS = [
    ("apps/device_pool/models.py", "Device", "设备", "设备"),
    ("apps/device_pool/models.py", "DeviceLock", "设备锁", "设备锁"),
    ("apps/device_pool/models.py", "DeviceQueue", "设备队列", "设备队列"),
    ("apps/element_locator/models.py", "Page", "页面", "页面"),
    ("apps/element_locator/models.py", "Element", "元素", "元素"),
    ("apps/element_locator/models.py", "PageFlow", "页面跳转流", "页面跳转流"),
    ("apps/case_manager/models.py", "CaseDirectory", "用例目录", "用例目录"),
    ("apps/case_manager/models.py", "TestDefinition", "用例定义", "用例定义"),
    ("apps/test_runner/models.py", "TestSOP", "测试SOP上下文", "测试SOP上下文"),
    ("apps/test_runner/models.py", "TestRunRecord", "测试运行记录", "测试运行记录"),
    ("apps/test_runner/models.py", "TestResult", "测试结果", "测试结果"),
    ("apps/report_generator/models.py", "Report", "报告", "报告"),
    ("apps/report_generator/models.py", "ReportTemplate", "报告模板", "报告模板"),
    ("apps/ai_assistant/models.py", "AIAgent", "智能体", "智能体"),
    ("apps/ai_assistant/models.py", "AITool", "工具配置", "工具配置"),
    ("apps/ai_assistant/models.py", "AIConversation", "对话", "对话"),
    ("apps/ai_assistant/models.py", "AIMessage", "消息", "消息"),
    ("apps/ai_assistant/models.py", "AITask", "任务", "任务"),
    ("apps/ai_assistant/models.py", "AIExecutionLog", "执行日志", "执行日志"),
]


def fix_file(filepath, model_info_list):
    """修复一个文件中的所有模型"""
    full = os.path.join(BASE, filepath)
    with open(full, "r") as f:
        content = f.read()
    original = content

    # 移除所有可能由脚本错误插入的 verbose_name 行
    content = re.sub(
        r"^\s*verbose_name\s*=\s*'[^']*'\s*$",
        "",
        content,
        flags=re.MULTILINE,
    )
    content = re.sub(
        r'^\s*verbose_name\s*=\s*"[^"]*"\s*$',
        "",
        content,
        flags=re.MULTILINE,
    )
    content = re.sub(
        r"^\s*verbose_name_plural\s*=\s*'[^']*'\s*$",
        "",
        content,
        flags=re.MULTILINE,
    )
    content = re.sub(
        r'^\s*verbose_name_plural\s*=\s*"[^"]*"\s*$',
        "",
        content,
        flags=re.MULTILINE,
    )

    # 清理多余空行（连续空行缩为一行）
    content = re.sub(r"\n{3,}", "\n\n", content)

    # 为每个模型正确插入 verbose_name
    for _, cls, vn, vnp in model_info_list:
        # 匹配 class XXX: ... class Meta: ... 并在 Meta 块内插入
        # 处理两种格式：
        # 1. class Meta:\n        db_table = 'xxx'
        # 2. class Meta: db_table = 'xxx'

        # 格式 1：多行 Meta
        pattern1 = rf"(class {cls}\(.*?class Meta:\s*\n\s*db_table\s*=\s*'[^']*')"
        repl1 = rf"\1\n        verbose_name = '{vn}'\n        verbose_name_plural = '{vnp}'"
        content, n1 = re.subn(pattern1, repl1, content, flags=re.DOTALL, count=1)

        if n1 == 0:
            # 格式 1b：双引号 db_table
            pattern1b = rf'(class {cls}\(.*?class Meta:\s*\n\s*db_table\s*=\s*"[^"]*")'
            repl1b = rf'\1\n        verbose_name = "{vn}"\n        verbose_name_plural = "{vnp}"'
            content, n1b = re.subn(pattern1b, repl1b, content, flags=re.DOTALL, count=1)

        if n1 == 0 and (n1b if 'n1b' in dir() else 0) == 0:
            # 格式 2：单行 Meta — class Meta: db_table = 'xxx'
            pattern2 = rf"(class {cls}\(.*?class Meta:\s*db_table\s*=\s*'[^']*')"
            repl2 = rf"\1\n        verbose_name = '{vn}'\n        verbose_name_plural = '{vnp}'"
            content, n2 = re.subn(pattern2, repl2, content, flags=re.DOTALL, count=1)

            if n2 == 0:
                pattern2b = rf'(class {cls}\(.*?class Meta:\s*db_table\s*=\s*"[^"]*")'
                repl2b = rf'\1\n        verbose_name = "{vn}"\n        verbose_name_plural = "{vnp}"'
                content, n2b = re.subn(pattern2b, repl2b, content, flags=re.DOTALL, count=1)

                if n2b == 0:
                    print(f"  ✗ {cls}: 无法匹配 Meta 格式")
                    continue

        print(f"  ✓ {cls} → {vn}")

    if content != original:
        with open(full, "w") as f:
            f.write(content)
        return True
    return False


if __name__ == "__main__":
    # 按文件分组
    files = {}
    for fp, cls, vn, vnp in MODELS:
        files.setdefault(fp, []).append((fp, cls, vn, vnp))

    for fp, models in files.items():
        print(f"\n修复 {fp}:")
        fix_file(fp, models)

    print("\n完成。运行 python manage.py check 验证")
