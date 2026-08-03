"""execution_steps 纯逻辑测试 — _compute_perf_stats 和 _build_case_snapshots。

零 I/O，不依赖 DB/设备。
"""

from unittest.mock import MagicMock
from apps.test_runner.views.execution_steps import _compute_perf_stats, _build_case_snapshots


def _find_case(per_case: list, case_id: str) -> dict:
    """在 per_case 列表中按 case_id 查找。"""
    for c in per_case:
        if c["case_id"] == case_id:
            return c
    raise KeyError(f"case_id {case_id} not found in per_case")


class TestComputePerfStats:
    def test_empty_returns_none(self):
        assert _compute_perf_stats([]) is None

    def test_single_element(self):
        perfs = [{"case_id": "C1", "case_title": "T1", "iteration": 1, "duration": 1.5,
                  "description": "click"}]
        result = _compute_perf_stats(perfs)
        # 总览
        assert result["count"] == 1
        assert result["avg"] == 1.5
        assert result["median"] == 1.5
        # 每用例
        case = _find_case(result["per_case"], "C1")
        assert case["count"] == 1
        assert case["avg"] == 1.5
        assert case["median"] == 1.5

    def test_median_odd_count(self):
        perfs = [
            {"case_id": "C1", "iteration": i, "duration": d, "description": f"step{i}"}
            for i, d in enumerate([1.0, 2.0, 3.0], start=1)
        ]
        result = _compute_perf_stats(perfs)
        assert result["median"] == 2.0  # 排序: [1,2,3]

    def test_median_even_count(self):
        perfs = [
            {"case_id": "C1", "iteration": i, "duration": d, "description": f"step{i}"}
            for i, d in enumerate([1.0, 4.0], start=1)
        ]
        result = _compute_perf_stats(perfs)
        assert result["median"] == 2.5  # (1+4)/2

    def test_per_case_breakdown(self):
        perfs = [
            {"case_id": "C1", "case_title": "登录", "iteration": 1, "duration": 1.0, "description": "a"},
            {"case_id": "C2", "case_title": "退出", "iteration": 1, "duration": 3.0, "description": "b"},
            {"case_id": "C1", "case_title": "登录", "iteration": 2, "duration": 2.0, "description": "c"},
        ]
        result = _compute_perf_stats(perfs)
        assert result["count"] == 3
        assert len(result["per_case"]) == 2
        c1 = _find_case(result["per_case"], "C1")
        assert c1["count"] == 2
        assert c1["case_title"] == "登录"
        c2 = _find_case(result["per_case"], "C2")
        assert c2["count"] == 1

    def test_undefined_case_id(self):
        """没有 case_id 的条目归入空字符串组。"""
        perfs = [
            {"iteration": 1, "duration": 1.0, "description": "orphan"},
        ]
        result = _compute_perf_stats(perfs)
        case = _find_case(result["per_case"], "")
        assert case["count"] == 1

    def test_items_preserved(self):
        """每个 case 下的 items 列表保存原始记录。"""
        perfs = [
            {"case_id": "C1", "iteration": 1, "duration": 1.0, "description": "desc1"},
        ]
        result = _compute_perf_stats(perfs)
        case = _find_case(result["per_case"], "C1")
        assert len(case["items"]) == 1
        assert case["items"][0]["description"] == "desc1"


class TestBuildCaseSnapshots:
    def test_empty_list(self):
        assert _build_case_snapshots([]) == []

    def test_single_case(self):
        case = MagicMock()
        case.id = "TC-001"
        case.title = "登录"
        case.steps_data = []
        snapshots = _build_case_snapshots([case])
        assert len(snapshots) == 1
        assert snapshots[0]["case_id"] == "TC-001"
        assert snapshots[0]["title"] == "登录"
        assert snapshots[0]["steps_data"] == []

    def test_multiple_cases(self):
        cases = []
        for i in range(3):
            c = MagicMock()
            c.id = f"TC-00{i+1}"
            c.title = f"Case {i+1}"
            c.steps_data = []
            cases.append(c)
        snapshots = _build_case_snapshots(cases)
        assert len(snapshots) == 3
        assert [s["case_id"] for s in snapshots] == ["TC-001", "TC-002", "TC-003"]

    def test_steps_with_to_dict(self):
        """有 to_dict() 方法的对象用它来序列化。"""
        step = MagicMock()
        step.to_dict.return_value = {"type": "click", "xpath": "//btn"}

        case = MagicMock()
        case.id = "TC-001"
        case.title = "Test"
        case.steps_data = [step]

        snapshots = _build_case_snapshots([case])
        assert snapshots[0]["steps_data"][0] == {"type": "click", "xpath": "//btn"}

    def test_steps_with_dict_but_no_to_dict(self):
        """有 __dict__ 但没有 to_dict 的对象用 __dict__ 序列化。"""
        class PlainObj:
            pass
        step = PlainObj()
        step.type = "click"
        step.xpath = "//btn"

        case = MagicMock()
        case.id = "TC-001"
        case.title = "Test"
        case.steps_data = [step]

        snapshots = _build_case_snapshots([case])
        assert snapshots[0]["steps_data"][0]["type"] == "click"
