"""SOP 工作流：只存名称与两个名片编号，运行时现读。"""

from __future__ import annotations

import pytest

from backend.apps.ai_assistant import api
from backend.apps.ai_assistant.models import AIAssistant, AIModelConfig, AIRole, AISopWorkflow
from backend.apps.ai_assistant.services.sop_workflows import WORKFLOW_FIELDS

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


def _config(model_name: str = "deepseek-flash") -> AIModelConfig:
    return AIModelConfig.objects.create(
        provider="deepseek",
        api_key_env="DEEPSEEK_API_KEY",
        model_name=model_name,
        base_url="https://api.deepseek.com",
    )


def _role(name: str, prompt: str, model_name: str = "deepseek-flash") -> AIRole:
    return AIRole.objects.create(
        role_id=f"20261117{name[-3:]}",
        name=name,
        model_config=_config(model_name),
        system_prompt=prompt,
    )


def _card(
    assistant_id: str, role: AIRole, display_name: str, tools: list | None = None
) -> AIAssistant:
    return AIAssistant.objects.create(
        assistant_id=assistant_id,
        display_name=display_name,
        marker="teal",
        role_id=role.role_id,
        tools=tools or [],
    )


def test_workflow_create_keeps_only_name_and_ids():
    """绑定两张已有名片后，工作流表不含提示词、模型参数和工具勾选。"""
    role = _role("执行配置abc", "执行提示词")
    executor = _card("20261117_EX1", role, "执行助手", [{"domain": "adb", "preset": "all"}])
    verifier = _card("20261117_VF1", role, "验收助手")

    workflow = api.create_sop_workflow("桌面检查", executor.assistant_id, verifier.assistant_id)

    assert workflow.name == "桌面检查"
    assert set(WORKFLOW_FIELDS).isdisjoint({"system_prompt", "model_name", "tools"})
    assert "system_prompt" not in {field.name for field in AISopWorkflow._meta.fields}
    stored = AISopWorkflow.objects.get(pk=workflow.pk)
    assert stored.executor_assistant_id == executor.assistant_id
    assert stored.verifier_assistant_id == verifier.assistant_id


def test_workflow_accepts_same_card_on_both_sides():
    """同一张名片可以同时担任两侧。"""
    role = _role("共用配置abc", "共用提示词")
    card = _card("20261117_SM1", role, "共用助手")

    workflow = api.create_sop_workflow("自检", card.assistant_id, card.assistant_id)

    assert workflow.executor_assistant_id == workflow.verifier_assistant_id == card.assistant_id
    assert workflow.orchestration == "sop"
    assert workflow.kind == "ui_automation"


def test_allowed_pairs_create_and_crossed_pairs_do_not_persist():
    role = _role("组合配置abc", "提示词")
    one = _card("20261117_P01", role, "甲")
    two = _card("20261117_P02", role, "乙")
    three = _card("20261117_P03", role, "丙")

    goal = api.create_sop_workflow(
        "编写",
        one.assistant_id,
        two.assistant_id,
        orchestration="goal",
        kind="case_authoring",
    )
    team = api.create_sop_workflow(
        "拆解",
        orchestration="team",
        kind="requirement_breakdown",
        leader_assistant_id=one.assistant_id,
        members=[
            {"assistant_id": two.assistant_id, "description": "拆边界"},
            {"assistant_id": three.assistant_id, "description": "列测试点"},
        ],
    )

    assert (goal.orchestration, goal.kind) == ("goal", "case_authoring")
    assert team.leader_assistant_id == one.assistant_id
    assert len(team.members) == 2
    before = AISopWorkflow.objects.count()
    with pytest.raises(api.WorkflowPairError, match="不能组合"):
        api.create_sop_workflow(
            "错配", one.assistant_id, two.assistant_id, orchestration="sop", kind="case_authoring"
        )
    assert AISopWorkflow.objects.count() == before


def test_workflow_rejects_blank_name():
    """名称为空时拒绝。"""
    role = _role("空名配置abc", "提示词")
    card = _card("20261117_NM1", role, "有名助手")

    with pytest.raises(api.WorkflowNameError):
        api.create_sop_workflow("   ", card.assistant_id, card.assistant_id)


def test_workflow_rejects_missing_card_and_names_the_side():
    """任一侧名片不存在时拒绝，并说明是哪一侧。"""
    role = _role("缺卡配置abc", "提示词")
    card = _card("20261117_MS1", role, "还在的助手")

    with pytest.raises(api.WorkflowAssistantMissingError, match="验收助手"):
        api.create_sop_workflow("缺验收", card.assistant_id, "20261117_NO1")


def test_resolve_reads_current_card_and_does_not_copy_fields():
    """改名片后再次解析得到新提示词，工作流表不增加字段副本。"""
    role = _role("活绑配置abc", "旧提示词", "deepseek-flash")
    card = _card("20261117_LV1", role, "活绑助手", [{"domain": "adb", "preset": "readonly"}])
    other = _card("20261117_LV2", role, "另一侧")
    workflow = api.create_sop_workflow("活绑", card.assistant_id, other.assistant_id)
    before = AISopWorkflow.objects.count()

    first = api.resolve_sop_workflow(workflow.id)
    role.system_prompt = "新提示词"
    role.save(update_fields=["system_prompt"])
    second = api.resolve_sop_workflow(workflow.id)

    assert first["executor"]["system_prompt"] == "旧提示词"
    assert second["executor"]["system_prompt"] == "新提示词"
    assert second["executor"]["model_name"] == "deepseek-flash"
    assert second["executor"]["tools"] == [{"domain": "adb", "preset": "readonly"}]
    assert AISopWorkflow.objects.count() == before
    assert "system_prompt" not in {field.name for field in AISopWorkflow._meta.fields}


def test_resolve_disambiguates_identical_display_names():
    """两侧显示名相同时，验收侧运行名追加自己的编号。"""
    role = _role("同名配置abc", "提示词")
    left = _card("20261117_A01", role, "同名")
    right = _card("20261117_B02", role, "同名")
    workflow = api.create_sop_workflow("同名流程", left.assistant_id, right.assistant_id)

    resolved = api.resolve_sop_workflow(workflow.id)

    assert resolved["executor"]["run_name"] == "同名"
    assert resolved["verifier"]["run_name"] == "同名-20261117_B02"


def test_resolve_fails_when_card_or_role_is_gone():
    """名片或 Agent 配置缺失时给出可读错误，不写工作流表。"""
    role = _role("缺失配置abc", "提示词")
    card = _card("20261117_GN1", role, "将被删除")
    workflow = api.create_sop_workflow("缺失", card.assistant_id, card.assistant_id)

    card.delete()
    with pytest.raises(api.WorkflowAssistantMissingError, match="执行助手"):
        api.resolve_sop_workflow(workflow.id)

    card = _card("20261117_GN2", role, "配置将被删除")
    workflow.executor_assistant_id = card.assistant_id
    workflow.verifier_assistant_id = card.assistant_id
    workflow.save()
    role.delete()
    with pytest.raises(api.WorkflowRoleMissingError, match="Agent 配置不存在"):
        api.resolve_sop_workflow(workflow.id)


def test_workflow_update_renames_and_rebinds():
    """编辑只改名称与两侧编号，不往工作流表复制名片字段。"""
    role = _role("编辑配置abc", "旧提示词")
    executor = _card("20261117_ED1", role, "旧执行")
    verifier = _card("20261117_ED2", role, "旧验收")
    replacement = _card("20261117_ED3", role, "新执行")
    workflow = api.create_sop_workflow("旧名字", executor.assistant_id, verifier.assistant_id)

    updated = api.update_sop_workflow(
        workflow, "新名字", replacement.assistant_id, verifier.assistant_id
    )

    stored = AISopWorkflow.objects.get(pk=workflow.pk)
    assert updated.pk == stored.pk
    assert stored.name == "新名字"
    assert stored.executor_assistant_id == replacement.assistant_id
    assert stored.verifier_assistant_id == verifier.assistant_id
    assert "system_prompt" not in {field.name for field in AISopWorkflow._meta.fields}
    resolved = api.resolve_sop_workflow(stored.id)
    assert resolved["executor"]["assistant_id"] == replacement.assistant_id


def test_workflow_update_rejects_missing_card_without_touching_record():
    """任一侧名片不存在时整条拒绝，记录保持编辑前的值。"""
    role = _role("拒绝编辑abc", "提示词")
    executor = _card("20261117_RJ1", role, "执行")
    verifier = _card("20261117_RJ2", role, "验收")
    workflow = api.create_sop_workflow("原名字", executor.assistant_id, verifier.assistant_id)

    with pytest.raises(api.WorkflowAssistantMissingError, match="验收助手"):
        api.update_sop_workflow(workflow, "改坏的名字", executor.assistant_id, "20261117_NO1")

    stored = AISopWorkflow.objects.get(pk=workflow.pk)
    assert stored.name == "原名字"
    assert stored.executor_assistant_id == executor.assistant_id
    assert stored.verifier_assistant_id == verifier.assistant_id


def test_workflow_delete_keeps_cards_and_roles():
    """删除工作流只删记录，名片与 Agent 配置都还在。"""
    role = _role("删除配置abc", "提示词")
    card = _card("20261117_DL1", role, "删后仍在")
    workflow = api.create_sop_workflow("待删", card.assistant_id, card.assistant_id)

    api.delete_sop_workflow(workflow)

    assert not AISopWorkflow.objects.filter(pk=workflow.pk).exists()
    assert AIAssistant.objects.filter(pk=card.pk).exists()
    assert AIRole.objects.filter(pk=role.pk).exists()
