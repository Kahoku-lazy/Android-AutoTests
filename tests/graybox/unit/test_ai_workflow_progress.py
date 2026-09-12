"""工作流运行中检查点 payload / 回调容错。"""

from types import SimpleNamespace

import pytest

from engines.ai.agentscope.workflow import Plan, Step, _emit_progress, _progress_payload


def _cfg():
    role = SimpleNamespace(model_name="m")
    return SimpleNamespace(planner=role, executor=role, verifier=role, max_loops=3)


@pytest.mark.unit
def test_progress_payload_is_running_and_keeps_plan():
    plan = Plan(goal="启动", steps=[Step(action="打开", assertion="在前台")])
    usage = {"input_tokens": 1, "output_tokens": 2, "cache_input_tokens": 0, "models": {}}
    payload = _progress_payload(
        _cfg(), usage, summary="已规划 1 个步骤", plan=plan, log=[], done=[]
    )
    assert payload["status"] == "running"
    assert payload["summary"] == "已规划 1 个步骤"
    assert payload["plans"][0]["goal"] == "启动"
    assert payload["plans"][0]["steps"][0]["assert"] == "在前台"
    assert payload["log"] == []
    assert payload["max_loops"] == 3


@pytest.mark.unit
def test_emit_progress_swallows_callback_errors():
    seen = []

    def boom(payload):
        seen.append(payload)
        raise RuntimeError("persist failed")

    _emit_progress(boom, {"status": "running"})
    assert seen == [{"status": "running"}]
    _emit_progress(None, {"status": "running"})
