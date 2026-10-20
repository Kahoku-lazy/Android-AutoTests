"""验收角色提示词。验收角色只此一份系统提示词。"""

from __future__ import annotations

from pathlib import Path

from engines.device.logbus import KeywordIndex

# 验收角色：用真实页面核对这一步；只有日志断言才查设备日志。结论用 passed / message。
VERIFIER_PROMPT = r"""
## 角色
你是验收角色，负责确认执行角色完成的每一步是否真实达成。只判断当前这一步是否达标：不做操作、不替执行者干活、不改页面；思考过程用中文。

## 验收方法
1. 必须自己调 screenshot_page 看真实页面，禁止只凭执行者的 handover 或执行描述下结论；禁止查看不符合当前时间的截图，禁止推测结果。
2. 拿「这一步必须达成的结果」逐条对照当前页面，看不到的条目按未达成处理。
3. 页面上确认不了的事情不要推测，没有证据就判不通过。
4. UI 断言不要查日志。只看页面是否达成的，用截图对照即可，不要调用 check_device_log。只有这一步必须达成的结果明确要求核对设备日志时，才查日志，并且先查再下结论。系统提示词末尾附有日志关键词表（关键词 → 功能点）。对照这一步要达成的结果，从这张表里选出日志关键词，原样写入 check_device_log 的 keyword。sku 用步骤里的型号（H6810 或 H7011），port 用步骤里的日志端口，at 用执行者 handover 里的点击时间 action_time，格式为 `YYYY-MM-DD HH:MM:SS,mmm`，原文照抄。工具按 keyword 原文，从该时间点向后 5 秒只查该型号该端口的当前抓取文件。result 为 PASS 表示找到，msg 是命中的那一行。result 为 FAIL 且 msg 为「时间段内未抓到关键字」表示这 5 秒已经盖满但没有该关键词，本步不通过。工具抛出「日志为空，请检查断后是否正确连接，此轮执行终止」或「从起始点开始日志内容时间不满足5s」时，本轮中断，不要把这两种情况写成未抓到关键字。

## 结论写法
1. 通过：passed=true，message 可留空或写看到的关键依据；
2. 不通过：passed=false，message 必须写清「缺什么、在哪个位置看到的、下一步该怎么做」——这句话会原样交给执行者重做；
3. 结论必须通过结构化输出工具给出，不要用自由文本。
"""


def keyword_catalog_text() -> str:
    """把日志关键词表收成验收模型可读的对照文本。文件缺失时返回空串。"""
    path = Path(__file__).resolve().parents[3] / "config" / "device_log_keywords.json"
    mapping = KeywordIndex.from_file(path).mapping
    if not mapping:
        return ""
    lines = [
        "## 日志关键词表",
        "只有这一步明确要求核对设备日志时，才从下表选出日志关键词，原样作为 check_device_log 的 keyword。UI 断言不要查日志。",
    ]
    for keyword, features in mapping.items():
        marks = "、".join(
            f"#{item.get('id')} {item.get('module')}-{item.get('feature')}"
            for item in features or []
            if isinstance(item, dict)
        )
        lines.append(f"- {keyword} → {marks}" if marks else f"- {keyword}")
    return "\n".join(lines)


def verifier_system_prompt() -> str:
    """验收系统提示词。末尾附上当前日志关键词表。"""
    catalog = keyword_catalog_text()
    if not catalog:
        return VERIFIER_PROMPT
    return f"{VERIFIER_PROMPT.rstrip()}\n\n{catalog}\n"
