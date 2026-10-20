"""任务报告：按时间把事件折成开始 / 推理 / 执行 / 结束。"""

from __future__ import annotations

import pytest

from django.contrib.auth import get_user_model

from apps.ai_assistant.models import AIAgent, AITask, AITaskAttachment, AITaskEvent
from apps.report_generator.ai_task_reports import build_task_flow

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


def _task(owner) -> AITask:
    agent = AIAgent.objects.create(name="报告助手", owner=owner)
    return AITask.objects.create(
        agent=agent,
        title="流程任务",
        case_title="卡片页",
        status="completed",
        device_label="测试机",
    )


def _event(
    task,
    seq,
    event_type,
    phase,
    *,
    is_delta=False,
    payload=None,
    role="executor_role",
    step_seq=1,
    attempt=1,
):
    return AITaskEvent.objects.create(
        task=task,
        seq=seq,
        event_type=event_type,
        phase=phase,
        block_type="reply",
        is_delta=is_delta,
        role_name=role,
        step_seq=step_seq,
        attempt=attempt,
        payload=payload or {},
    )


def test_flow_groups_phases_and_collapses_deltas():
    owner = get_user_model().objects.create_user(username="flow-owner", password="pass")
    task = _task(owner)
    _event(task, 1, "ReplyStartEvent", "开始", payload={"role": "executor_role"})
    _event(task, 2, "ToolCallDeltaEvent", "推理", is_delta=True, payload={"delta": "a", "idx": 0})
    _event(task, 3, "ToolCallDeltaEvent", "推理", is_delta=True, payload={"delta": "b", "idx": 1})
    _event(task, 4, "ToolCallDeltaEvent", "推理", is_delta=True, payload={"delta": "c", "idx": 2})
    _event(
        task,
        5,
        "ToolCallEndEvent",
        "推理",
        payload={"tool_name": "tap", "args": '{"x": 1}'},
    )
    _event(
        task,
        6,
        "ToolResultEndEvent",
        "执行",
        payload={"tool_name": "tap", "status": "ok", "result": "已点击"},
    )
    _event(task, 7, "ReplyEndEvent", "结束", payload={"finished_reason": "stop"})

    flow = build_task_flow(str(owner.id), str(task.id))
    assert flow is not None
    assert flow["task"]["title"] == "流程任务"
    assert len(flow["rounds"]) == 1
    titles = [block["title"] for block in flow["rounds"][0]["blocks"]]
    assert titles == ["开始", "推理阶段", "执行阶段", "结束"]
    reason_items = flow["rounds"][0]["blocks"][1]["items"]
    assert reason_items[0]["event_type"] == "ToolCallDeltaEvent"
    assert reason_items[0]["count"] == 3
    assert reason_items[1]["event_type"] == "ToolCallEndEvent"
    assert "tap" in reason_items[1]["detail"]


def test_conclusion_comes_from_verifier_output():
    owner = get_user_model().objects.create_user(username="flow-owner-pass", password="pass")
    task = _task(owner)
    _event(
        task,
        1,
        "ToolCallEndEvent",
        "推理",
        payload={"tool_name": "submit", "args": '{"handover": "步骤：已打开首页"}'},
    )
    _event(
        task,
        2,
        "ToolCallEndEvent",
        "推理",
        role="verifier_role",
        payload={
            "tool_name": "GenerateStructuredOutput",
            "args": '{"passed": true, "message": "截图显示用户已登录"}',
        },
    )
    flow = build_task_flow(str(owner.id), str(task.id))
    assert flow["conclusion"]["outcome"] == "PASS"
    assert flow["conclusion"]["verdicts"][0]["message"] == "截图显示用户已登录"
    assert flow["conclusion"]["delivery"] == "步骤：已打开首页"


def test_executor_round_keeps_handover():
    owner = get_user_model().objects.create_user(username="flow-owner-hand", password="pass")
    task = _task(owner)
    _event(task, 1, "ReplyStartEvent", "开始", step_seq=1)
    _event(
        task,
        2,
        "ToolCallEndEvent",
        "推理",
        step_seq=1,
        payload={"tool_name": "submit", "args": '{"handover": "已打开首页并停在设备列表"}'},
    )

    flow = build_task_flow(str(owner.id), str(task.id))
    round_row = flow["cases"][0]["rounds"][0]
    assert round_row["handover"] == "已打开首页并停在设备列表"
    assert round_row["verdict"] is None
    leaked = [item.get("handover") for block in round_row["blocks"] for item in block["items"]]
    assert all(value is None for value in leaked)


def test_flow_hides_another_users_task():
    owner = get_user_model().objects.create_user(username="flow-owner-2", password="pass")
    other = get_user_model().objects.create_user(username="flow-other", password="pass")
    task = _task(owner)
    assert build_task_flow(str(other.id), str(task.id)) is None
    assert build_task_flow(str(owner.id), "abc") is None


def test_two_cases_keep_step_and_result():
    owner = get_user_model().objects.create_user(username="flow-owner-cases", password="pass")
    task = _task(owner)
    task.case_title = ""
    task.save(update_fields=["case_title"])
    AITaskAttachment.objects.create(
        task=task,
        kind=AITaskAttachment.KIND_CONFIG,
        body=(
            "- title: 卡片页\n"
            "  steps:\n"
            "    - action: 启动应用\n"
            "      assert: 进入主页\n"
            "    - action: 点击开关\n"
            "      assert: 日志有开关记录\n"
            "- title: 基础模式\n"
            "  steps:\n"
            "    - action: 返回桌面\n"
            "      assert: 应用已关闭\n"
        ),
    )
    _event(task, 1, "ReplyStartEvent", "开始", step_seq=1)
    _event(task, 2, "ReplyStartEvent", "开始", role="verifier_role", step_seq=1)
    _event(
        task,
        3,
        "ToolCallEndEvent",
        "推理",
        role="verifier_role",
        step_seq=1,
        payload={
            "tool_name": "GenerateStructuredOutput",
            "args": '{"passed": true, "message": "已进主页"}',
        },
    )
    _event(task, 4, "ReplyStartEvent", "开始", step_seq=2)
    _event(task, 5, "ReplyStartEvent", "开始", role="verifier_role", step_seq=2)
    _event(
        task,
        6,
        "ToolCallEndEvent",
        "推理",
        role="verifier_role",
        step_seq=2,
        payload={
            "tool_name": "GenerateStructuredOutput",
            "args": '{"passed": true, "message": "开关日志已看到"}',
        },
    )
    _event(task, 7, "ReplyStartEvent", "开始", step_seq=1)
    _event(task, 8, "ReplyStartEvent", "开始", role="verifier_role", step_seq=1)
    _event(
        task,
        9,
        "ToolCallEndEvent",
        "推理",
        role="verifier_role",
        step_seq=1,
        payload={
            "tool_name": "GenerateStructuredOutput",
            "args": '{"passed": false, "message": "还在应用里"}',
        },
    )

    flow = build_task_flow(str(owner.id), str(task.id))
    cases = flow["cases"]
    assert [item["title"] for item in cases] == ["卡片页", "基础模式"]
    assert cases[0]["outcome"] == "PASS"
    assert [step["outcome"] for step in cases[0]["steps"]] == ["PASS", "PASS"]
    assert cases[0]["rounds"][0]["role_kind"] == "executor"
    assert cases[0]["rounds"][0]["subject"] == "启动应用"
    assert cases[0]["rounds"][0]["verdict"] is None
    assert cases[0]["rounds"][0]["handover"] == ""
    assert cases[0]["rounds"][1]["role_kind"] == "verifier"
    assert cases[0]["rounds"][1]["subject"] == "进入主页"
    assert cases[0]["rounds"][1]["verdict"] == {"passed": True, "message": "已进主页"}
    assert cases[0]["rounds"][2]["subject"] == "点击开关"
    assert cases[1]["outcome"] == "FAIL"
    assert cases[1]["steps"][0]["outcome"] == "FAIL"
    assert cases[1]["rounds"][0]["subject"] == "返回桌面"
    assert cases[1]["rounds"][1]["subject"] == "应用已关闭"
    assert cases[1]["rounds"][1]["verdict"] == {"passed": False, "message": "还在应用里"}
