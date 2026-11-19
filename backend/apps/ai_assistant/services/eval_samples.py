"""评测样本。页面自测与 pytest 都从这里读取。"""

from __future__ import annotations

# 发布样本只含会真跑的探针。故意写坏的轨迹留在尺子单测，不挡发布。
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
    """返回样本副本。停用的样本在 enabled_only 时不参加新自测。"""
    rows = [dict(item) for item in SAMPLES]
    if enabled_only:
        return [item for item in rows if item["enabled"]]
    return rows


def sample_ids() -> list[str]:
    """当前启用的发布样本。页面自测与发布认账读这一份。"""
    return [item["id"] for item in load_samples() if item["id"] in GATE_IDS]
