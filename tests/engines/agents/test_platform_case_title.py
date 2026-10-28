"""平台 SOP 指定用例：空=全部、指定=只跑一条、不存在=可读失败。"""

from __future__ import annotations

from engines.agents.workflow.platform_run import run_platform_sop

YAML_TEXT = """
- title: 甲
  steps:
    - action: 点一下
      assert: 页面已打开
- title: 乙
  steps:
    - action: 再点一下
      assert: 页面已切换
""".strip()


def _run(tmp_path, case_title: str):
    path = tmp_path / "cases.yaml"
    path.write_text(YAML_TEXT, encoding="utf-8")
    seen: list[tuple[str, list[tuple[str, str]], str]] = []

    def runner(title: str, steps: list[tuple[str, str]], opening: str) -> str:
        seen.append((title, steps, opening))
        return "completed"

    result = run_platform_sop(
        str(path),
        "本次要操作的设备 serial 是：R5CT62RH88F。每一步的设备动作都必须带上它。",
        case_title=case_title,
        run_case=runner,
    )
    return seen, result


def test_empty_case_title_runs_all_in_file_order(tmp_path):
    seen, result = _run(tmp_path, "")
    assert [item[0] for item in seen] == ["甲", "乙"]
    assert result["status"] == "success"
    assert result["completed"] == ["甲", "乙"]


def test_case_title_runs_only_that_case(tmp_path):
    seen, result = _run(tmp_path, "乙")
    assert [item[0] for item in seen] == ["乙"]
    assert result["status"] == "success"
    assert result["completed"] == ["乙"]


def test_unknown_case_title_fails_readably(tmp_path):
    seen, result = _run(tmp_path, "丙")
    assert seen == []
    assert result["status"] == "fail"
    assert result["completed"] == []
    assert "丙" in result["reason"]
    assert result["load_message"] == "配置加载成功"
