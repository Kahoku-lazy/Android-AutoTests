"""
UI 提取脚本 — Airtest (截图) + uiautomator2 (UI 层级 dump)
输出: ui_data.json (结构化层级数据), screenshot.png (截图)
"""
import json
import os
import sys
import time
import uiautomator2 as u2
import xml.etree.ElementTree as ET
from airtest.core.android.android import Android

# 修复 Windows 控制台编码
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

def bounds_to_rect(bounds_str: str) -> dict:
    """解析 "[left,top][right,bottom]" 格式的 bounds"""
    parts = bounds_str.replace("][", ",").strip("[]").split(",")
    left, top, right, bottom = map(int, parts)
    return {
        "x": left,
        "y": top,
        "width": right - left,
        "height": bottom - top,
    }

def parse_node(node: ET.Element) -> dict:
    """递归解析 XML 节点为结构化 dict"""
    bounds_str = node.attrib.get("bounds", "[0,0][0,0]")
    rect = bounds_to_rect(bounds_str)

    info = {
        "class": node.attrib.get("class", ""),
        "text": node.attrib.get("text", ""),
        "resource_id": node.attrib.get("resource-id", ""),
        "content_desc": node.attrib.get("content-desc", ""),
        "package": node.attrib.get("package", ""),
        "checkable": node.attrib.get("checkable", "false") == "true",
        "checked": node.attrib.get("checked", "false") == "true",
        "clickable": node.attrib.get("clickable", "false") == "true",
        "enabled": node.attrib.get("enabled", "false") == "true",
        "focusable": node.attrib.get("focusable", "false") == "true",
        "focused": node.attrib.get("focused", "false") == "true",
        "scrollable": node.attrib.get("scrollable", "false") == "true",
        "long_clickable": node.attrib.get("long-clickable", "false") == "true",
        "password": node.attrib.get("password", "false") == "true",
        "selected": node.attrib.get("selected", "false") == "true",
        "index": node.attrib.get("index", ""),
        "rect": rect,
        "children": [],
    }
    for child in node:
        info["children"].append(parse_node(child))
    return info

def main():
    serial = os.environ.get('DEVICE_SERIAL', '')
    if not serial:
        print("请设置环境变量 DEVICE_SERIAL=你的设备串号")
        sys.exit(1)
    print(f"[1/4] 连接手机 {serial} ...")
    d = u2.connect(serial)
    ad = Android(serialno=serial)

    info = d.info
    print(f"      屏幕: {info['displayWidth']}×{info['displayHeight']}")
    print(f"      当前App: {d.app_current()['package']}")

    print("[2/4] 获取 UI 层级 (结构化) ...")
    t0 = time.time()
    raw = d.dump_hierarchy()
    t1 = time.time()
    # uiautomator2 可能返回 bytes 或 str；统一转为正确编码的 str
    if isinstance(raw, bytes):
        xml_str = raw.decode("utf-8")
    else:
        xml_str = raw
    # 确保 XML 声明了 UTF-8 编码（有些设备返回的 XML 缺少 declaration）
    if not xml_str.startswith("<?xml"):
        xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str
    print(f"      耗时 {t1 - t0:.2f}s, XML 大小 {len(xml_str)} chars")

    print("[3/4] 解析节点树 ...")
    root = ET.fromstring(xml_str.encode("utf-8") if isinstance(xml_str, str) else xml_str)
    hierarchy = parse_node(root)
    element_count = count_nodes(root)
    print(f"      解析到 {element_count} 个元素")

    # 保存结构化 JSON
    json_path = os.path.join(OUT_DIR, "ui_data.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(hierarchy, f, ensure_ascii=False, indent=2)
    print(f"      [OK] 已保存: {json_path}")

    print("[4/4] 截屏 (Airtest) ...")
    screenshot_path = os.path.join(OUT_DIR, "screenshot.png")
    ad.snapshot().save(screenshot_path)
    print(f"      [OK] 已保存: {screenshot_path}")

    print("\n[OK] 完成。运行 generate_html.py 生成 HTML 页面。")

def count_nodes(node: ET.Element) -> int:
    return 1 + sum(count_nodes(c) for c in node)

if __name__ == "__main__":
    main()
