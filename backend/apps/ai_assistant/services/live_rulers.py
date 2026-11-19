"""四条发布规则。只读一次评测的过程，不打综合分。"""

from __future__ import annotations

_WRITE_TOOLS = {"adb_tap", "adb_swipe", "adb_input_text", "adb_press_key", "save_authored_case"}


def _fail(ruler: str, text: str) -> dict:
    return {"ruler": ruler, "text": text}


def grade_process(
    steps: list[dict], *, allowed: set[str], same_instance: bool | None = None
) -> list[dict]:
    """按过程判定四条规则。缺过程时不制造失败。"""
    failures: list[dict] = []
    for step in steps:
        name = str(step.get("tool") or "")
        if name and name not in allowed:
            failures.append(_fail("unseen", f"调用了未勾选的工具：{name}"))
        if step.get("role") == "verifier" and name in _WRITE_TOOLS:
            failures.append(_fail("verifier_write", f"验收者调用了写操作：{name}"))
    previous = None
    for step in steps:
        if step.get("role") == "verifier":
            previous = None
            continue
        key = (step.get("role"), step.get("tool"), str(step.get("input")))
        if previous == key and step.get("tool"):
            failures.append(_fail("repeat", f"连续重复调用：{step.get('tool')}"))
        previous = key
    if same_instance is False:
        failures.append(_fail("instance", "第二轮不再是同一个实例"))
    return failures
