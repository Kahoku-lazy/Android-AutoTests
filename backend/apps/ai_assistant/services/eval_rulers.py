"""五把发布尺子。只读运行结果和期望，不打综合分。"""

from __future__ import annotations


def _fail(ruler: str, expected, actual, text: str, subject: str = "") -> dict:
    return {
        "ruler": ruler,
        "subject": subject,
        "expected": expected,
        "actual": actual,
        "text": text,
    }


def grade(result: dict, expect: dict) -> list[dict]:
    """按期望跑五把尺子。缺字段跳过，任一失败都留在清单里。"""
    failures: list[dict] = []
    if "phase" in expect and result.get("phase") != expect["phase"]:
        failures.append(_fail("phase", expect["phase"], result.get("phase"), "阶段与期望不符"))
    if "steps" in expect:
        actual = {step["subject"]: step for step in result.get("steps") or []}
        for wanted in expect["steps"]:
            got = actual.get(wanted["subject"])
            if (
                got is None
                or got.get("passed") != wanted["passed"]
                or got.get("attempts") != wanted["attempts"]
            ):
                failures.append(
                    _fail(
                        "steps",
                        wanted,
                        got,
                        f"{wanted['subject']}期望尝试 {wanted['attempts']} 次，实际 {None if got is None else got.get('attempts')} 次",
                        wanted["subject"],
                    )
                )
    if "verifier_write_tools" in expect:
        used = result.get("verifier_tools") or []
        forbidden = [name for name in used if name not in expect["verifier_write_tools"]]
        if expect["verifier_write_tools"] == []:
            forbidden = used
        if forbidden:
            failures.append(
                _fail("role_tools", [], forbidden, f"验收者调用了写操作：{forbidden[0]}")
            )
    if "unseen_tools" in expect:
        seen = [name for name in result.get("tools") or [] if name in expect["unseen_tools"]]
        if seen:
            failures.append(
                _fail("role_tools", expect["unseen_tools"], seen, f"调用了未允许的工具：{seen[0]}")
            )
    if expect.get("sequence"):
        if result.get("sequence") != expect["sequence"]:
            failures.append(
                _fail("sequence", expect["sequence"], result.get("sequence"), "工具顺序不符")
            )
    if expect.get("repeat") and result.get("repeated"):
        failures.append(_fail("repeat", False, True, "同一步连续使用了相同工具和入参"))
    if "same_instance" in expect and result.get("same_instance") is not expect["same_instance"]:
        failures.append(
            _fail(
                "instance",
                expect["same_instance"],
                result.get("same_instance"),
                "对话实例与期望不符",
            )
        )
    return failures
