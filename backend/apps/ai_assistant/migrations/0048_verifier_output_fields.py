from django.db import migrations

_VERIFIER_PAIRS: tuple[tuple[str, str], ...] = (
    (
        "- keep_local=true 时工具会在返回里带上 screenshot_path / screenshot_name（落盘证据）；"
        "你的最终 JSON 不要编造或抄写文件路径。",
        "- keep_local=true 时工具会在返回里带上 screenshot_path（落盘证据）；"
        "把该路径**原文照抄**进最终 JSON 的 screenshot，不要编造路径。",
    ),
    (
        "  - 等级「强证据」：窗口内首次出现且动作前基线未出现同名日志，可与截图共同支持判 true。\n"
        "  - 等级「疑似周期」：动作前基线已出现同名日志（设备在周期性打印），"
        "**不得单独作为通过依据**，必须有截图证据同时成立才可判 true；否则判 false 并在 actual 中说明。\n"
        "  - 等级「动作前」「超窗」：都不是本次动作的证据，不得据此判 true。",
        "  - 等级「强证据」：窗口内首次出现且动作前基线未出现同名日志，可与截图共同支持判 PASS。\n"
        "  - 等级「疑似周期」：动作前基线已出现同名日志（设备在周期性打印），"
        "**不得单独作为通过依据**，必须有截图证据同时成立才可判 PASS；否则判 FAIL 并在 actual 中说明。\n"
        "  - 等级「动作前」「超窗」：都不是本次动作的证据，不得据此判 PASS。",
    ),
    (
        "- actual：描述截图里的实际结果（实际看到了什么）。\n"
        "- result：true 表示操作成功（实际结果符合断言），false 表示未成功。\n"
        "- 对照「已完成步骤 / 当前步骤 / 剩余步骤」，判断当前这一步是否偏离整体目标；"
        "偏离则判 false 并在 actual 中说明原因。",
        "- actual：描述截图里的实际结果（实际看到了什么）。\n"
        "- result：PASS 表示操作成功（实际结果符合断言），FAIL 表示未成功或无法确认。\n"
        "- 对照「已完成步骤 / 当前步骤 / 剩余步骤」，判断当前这一步是否偏离整体目标；"
        "偏离则判 FAIL 并在 actual 中说明原因。",
    ),
    (
        "## 输出字段\n"
        "- action：被验证的操作。\n"
        "- assert：断言。\n"
        "- actual：截图里的实际结果（实际看到了什么）。\n"
        "- result：true（实际结果符合断言）或 false（不符合/无法确认）。",
        "## 输出字段\n"
        "- result：PASS（实际结果符合断言）或 FAIL（不符合/无法确认）。\n"
        "- click_timer：点击前的时间戳——取输入「执行结果」里给出的点击前时间戳（原文照抄）；"
        "本步没有点击时留空字符串。\n"
        "- logAssertionTimer：检测到日志关键词的时间戳——取输入「设备日志证据」里命中关键词那一次的"
        "日志时间戳（北京时间毫秒，原文照抄；多次命中取最早一次）；未采集日志、窗口内未命中或"
        "没有日志证据块时留空字符串，不要编造。\n"
        "- screenshot：验证截图的相对路径——取本次 screenshot_page(serial, keep_local=true) 返回的 "
        "screenshot_path（原文照抄）；没取到路径时留空字符串。\n"
        "- actual：截图里的实际结果（实际看到了什么）。",
    ),
    (
        "## 输出格式约束\n最终回答必须只输出一个 JSON 字符串，不要多余文字，不要 markdown 代码块包裹。",
        "## 输出格式约束\n最终回答必须只输出一个 JSON 字符串"
        "（只含 result / click_timer / logAssertionTimer / screenshot / actual 五个键），"
        "不要多余文字，不要 markdown 代码块包裹。",
    ),
    (
        '{"action": "在设备详情页找到「音乐模式」入口并点击", '
        '"assert": "页面出现「根据音乐节奏变换灯光」的提示文案", '
        '"actual": "截图确认页面出现该提示文案，音乐按钮蓝色选中", "result": true}',
        '{"result": "PASS", "click_timer": "2026-09-28 17:01:12.645", '
        '"logAssertionTimer": "2026-09-28 17:01:13.100", '
        '"screenshot": "device_inspector/screenshots/20260928/xxxxxx.jpg", '
        '"actual": "截图确认页面出现该提示文案，音乐按钮蓝色选中"}',
    ),
)


def apply_contract(text: str, pairs: tuple[tuple[str, str], ...]) -> str:
    for old, new in pairs:
        if old in text:
            text = text.replace(old, new, 1)
    return text


def revert_contract(text: str, pairs: tuple[tuple[str, str], ...]) -> str:
    for old, new in pairs:
        if new in text:
            text = text.replace(new, old, 1)
    return text


def _rewrite(apps, mutate) -> None:
    AIAgent = apps.get_model("ai_assistant", "AIAgent")
    for agent in AIAgent.objects.all().only("id", "prompt_verifier"):
        before = agent.prompt_verifier or ""
        after = mutate(before)
        if after != before:
            agent.prompt_verifier = after
            agent.save(update_fields=["prompt_verifier"])


def apply_verifier_output_fields(apps, schema_editor) -> None:
    _rewrite(apps, lambda text: apply_contract(text, _VERIFIER_PAIRS))


def revert_verifier_output_fields(apps, schema_editor) -> None:
    _rewrite(apps, lambda text: revert_contract(text, _VERIFIER_PAIRS))


class Migration(migrations.Migration):
    dependencies = [
        ("ai_assistant", "0047_executor_output_fields"),
    ]

    operations = [
        migrations.RunPython(apply_verifier_output_fields, revert_verifier_output_fields),
    ]
