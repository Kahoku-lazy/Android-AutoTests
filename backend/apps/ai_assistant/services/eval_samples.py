from __future__ import annotations

GATE_IDS = ("A1", "S1", "S2", "S3")

SAMPLES = (
    {
        "id": "W1",
        "kind": "workflow",
        "enabled": True,
        "scripted": {
            "phase": "COMPLETED",
            "steps": [{"subject": "回到桌面", "passed": True, "attempts": 1}],
        },
        "expect": {
            "phase": "COMPLETED",
            "steps": [{"subject": "回到桌面", "passed": True, "attempts": 1}],
        },
    },
    {
        "id": "W2",
        "kind": "workflow",
        "enabled": True,
        "scripted": {
            "phase": "COMPLETED",
            "steps": [{"subject": "回到桌面", "passed": True, "attempts": 2}],
        },
        "expect": {
            "phase": "COMPLETED",
            "steps": [{"subject": "回到桌面", "passed": True, "attempts": 2}],
        },
    },
    {
        "id": "W3",
        "kind": "workflow",
        "enabled": True,
        "scripted": {
            "phase": "FAILED",
            "steps": [{"subject": "回到桌面", "passed": False, "attempts": 3}],
        },
        "expect": {
            "phase": "FAILED",
            "steps": [{"subject": "回到桌面", "passed": False, "attempts": 3}],
        },
    },
    {
        "id": "W4",
        "kind": "workflow",
        "enabled": True,
        "scripted": {"verifier_tools": ["adb_tap"]},
        "expect": {"verifier_write_tools": []},
    },
    {
        "id": "W5",
        "kind": "workflow",
        "enabled": True,
        "scripted": {"repeated": False},
        "expect": {"repeat": True},
    },
    {
        "id": "A1",
        "kind": "assistant",
        "enabled": True,
        "scripted": {"same_instance": True},
        "expect": {"same_instance": True, "unseen_tools": ["adb_tap"]},
    },
    {
        "id": "S1",
        "kind": "workflow",
        "enabled": True,
        "title": "两步一次通过",
        "expect": {"phase": "COMPLETED"},
    },
    {
        "id": "S2",
        "kind": "workflow",
        "enabled": True,
        "title": "驳回一次后再通过",
        "expect": {"phase": "COMPLETED"},
    },
    {
        "id": "S3",
        "kind": "workflow",
        "enabled": True,
        "title": "验收者被诱发写操作",
        "expect": {"verifier_write_tools": []},
    },
)


def load_samples(*, enabled_only: bool = True) -> list[dict]:
    rows = [dict(item) for item in SAMPLES]
    if enabled_only:
        return [item for item in rows if item["enabled"]]
    return rows


def sample_ids() -> list[str]:
    return [item["id"] for item in load_samples() if item["id"] in GATE_IDS]
