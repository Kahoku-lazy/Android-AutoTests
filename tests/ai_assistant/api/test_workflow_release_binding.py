from __future__ import annotations

import importlib

import pytest

from django.apps import apps as django_apps
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIRequestFactory, force_authenticate

from backend.apps.ai_assistant import api as assistant_api
from backend.apps.ai_assistant.models import (
    AIAssistant,
    AIModelConfig,
    AIRole,
    AISopWorkflow,
    AssistantRelease,
)
from backend.apps.task_list import api as task_api
from backend.apps.task_list import task_runner
from backend.apps.task_list.models import Task
from backend.apps.task_list.views import TaskSubmitAPIView

pytestmark = [pytest.mark.django_db, pytest.mark.api]

MILESTONE = """
name: 回放
steps:
  - subject: 点一下
    description: 页面已打开
    max_attempts: 3
""".strip()


def _config() -> AIModelConfig:
    return AIModelConfig.objects.create(
        provider="deepseek",
        api_key_env="DEEPSEEK_API_KEY",
        model_name="deepseek-flash",
        base_url="https://api.example.com/v1",
    )


def _role(config: AIModelConfig, role_id: str, prompt: str) -> AIRole:
    return AIRole.objects.create(
        role_id=role_id,
        name=f"配置-{role_id}",
        model_config=config,
        system_prompt=prompt,
    )


def _card(role: AIRole, assistant_id: str, display_name: str) -> AIAssistant:
    return AIAssistant.objects.create(
        assistant_id=assistant_id,
        display_name=display_name,
        marker="teal",
        role_id=role.role_id,
        tools=[{"domain": "adb", "preset": "all", "add": [], "remove": []}],
        release_state="published",
    )


def _workflow(executor: AIAssistant, verifier: AIAssistant) -> AISopWorkflow:
    return AISopWorkflow.objects.create(
        name="发布流程",
        executor_assistant_id=executor.assistant_id,
        verifier_assistant_id=verifier.assistant_id,
        orchestration="sop",
        kind="ui_automation",
    )


def _submit(user, workflow: AISopWorkflow):
    factory = APIRequestFactory()
    request = factory.post(
        "/api/tasks/submit/",
        {
            "title": workflow.name,
            "workflow_id": str(workflow.id),
            "case_source": "yaml",
            "device_serial": "R5CT62RH88F",
        },
        format="multipart",
    )
    request.FILES["config"] = SimpleUploadedFile(
        "case.yaml", MILESTONE.encode("utf-8"), content_type="text/yaml"
    )
    request.user_id = str(user.id)
    force_authenticate(request, user=user)
    return TaskSubmitAPIView.as_view()(request)


@pytest.fixture(autouse=True)
def _no_dispatch(monkeypatch):
    monkeypatch.setattr(task_api, "dispatch_device", lambda serial: None)


def _user():
    from django.contrib.auth import get_user_model

    return get_user_model().objects.create_user(username="flow-author", password="pass")


def test_published_workflow_task_resolves_run_binding():
    user = _user()
    config = _config()
    executor = _card(_role(config, "20261118aa1", "执行提示词"), "exec-card", "执行名片")
    verifier = _card(_role(config, "20261118aa2", "验收提示词"), "verif-card", "验收名片")
    workflow = _workflow(executor, verifier)

    release = assistant_api.publish_workflow(workflow)
    stored = release.payload
    assert stored["executor"]["assistant_id"] == executor.assistant_id
    assert stored["executor"]["run_name"] == "执行名片"
    assert stored["executor"]["base_url"] == "https://api.example.com/v1"
    assert stored["verifier"]["run_name"] == "验收名片"

    response = _submit(user, workflow)
    assert response.status_code == 200
    task = Task.objects.latest("id")
    assert task.release_version == release.version

    resolved, yaml_text = task_runner._resolve_assistant_sop(task)
    assert "name: 回放" in yaml_text
    executor_binding = task_runner._binding(resolved["executor"])
    verifier_binding = task_runner._binding(resolved["verifier"])
    assert executor_binding.run_name == "执行名片"
    assert verifier_binding.run_name == "验收名片"
    assert executor_binding.base_url == "https://api.example.com/v1"
    assert resolved["executor"]["assistant_id"] == executor.assistant_id

    task.refresh_from_db()
    stored_release = AssistantRelease.objects.get(
        target_kind="workflow", target_id=str(workflow.id), version=task.release_version
    )
    assert stored_release.payload["executor"]["run_name"] == "执行名片"
    assert stored_release.payload["verifier"]["assistant_id"] == verifier.assistant_id


def test_same_display_name_keeps_snapshot_and_live_names_aligned():
    config = _config()
    executor = _card(_role(config, "20261118ab1", "提示词"), "exec-card", "同名名片")
    verifier = _card(_role(config, "20261118ab2", "提示词"), "verif-card", "同名名片")
    workflow = _workflow(executor, verifier)

    release = assistant_api.publish_workflow(workflow)
    live = assistant_api.resolve_workflow(workflow)

    assert release.payload["executor"]["run_name"] == "同名名片"
    assert release.payload["verifier"]["run_name"] == "同名名片-verif-card"
    assert live["verifier"]["run_name"] == release.payload["verifier"]["run_name"]


def test_task_without_version_follows_latest_release():
    user = _user()
    config = _config()
    executor = _card(_role(config, "20261118ad1", "发布时提示词"), "exec-card", "执行名片")
    verifier = _card(_role(config, "20261118ad2", "验收提示词"), "verif-card", "验收名片")
    workflow = _workflow(executor, verifier)
    assistant_api.publish_workflow(workflow)

    role = AIRole.objects.get(role_id=executor.role_id)
    role.system_prompt = "改过但未发布的提示词"
    role.save(update_fields=["system_prompt"])

    def _unpinned(target) -> Task:
        task = task_api.create_task(
            title="无版本任务",
            goal="目标编排",
            device_serial="R5CT62RH88F",
            task_kind="assistant_sop",
            created_by=str(user.id),
            workflow_id=target.id,
            orchestration="goal",
            kind="ui_automation",
        )
        task_api.add_task_attachment(
            task, kind="config", filename="case.yaml", body=MILESTONE, sort_order=0
        )
        task_api.save_task_run_payload(task, {"workflow_id": target.id})
        return task

    resolved, _yaml = task_runner._resolve_assistant_sop(_unpinned(workflow))
    assert resolved["executor"]["system_prompt"] == "发布时提示词"

    never_published = AISopWorkflow.objects.create(
        name="从未发布",
        executor_assistant_id=executor.assistant_id,
        verifier_assistant_id=verifier.assistant_id,
        orchestration="sop",
        kind="ui_automation",
    )
    live, _yaml = task_runner._resolve_assistant_sop(_unpinned(never_published))
    assert live["executor"]["system_prompt"] == "改过但未发布的提示词"


def test_legacy_release_payload_is_backfilled_for_run():
    config = _config()
    executor = _card(_role(config, "20261118ac1", "旧执行提示词"), "exec-card", "旧执行名片")
    verifier = _card(_role(config, "20261118ac2", "旧验收提示词"), "verif-card", "旧验收名片")
    workflow = _workflow(executor, verifier)
    legacy = {
        "name": workflow.name,
        "orchestration": "sop",
        "kind": "ui_automation",
        "executor_assistant_id": executor.assistant_id,
        "verifier_assistant_id": verifier.assistant_id,
        "executor": {
            "role_id": executor.role_id,
            "system_prompt": "发布当时的执行提示词",
            "tools": [{"domain": "adb", "preset": "all"}],
            "model_config_id": config.id,
            "model_name": config.model_name,
            "provider": config.provider,
            "api_key_env": config.api_key_env,
        },
        "verifier": {
            "role_id": verifier.role_id,
            "system_prompt": "发布当时的验收提示词",
            "tools": [{"domain": "adb", "preset": "readonly"}],
            "model_config_id": config.id,
            "model_name": config.model_name,
            "provider": config.provider,
            "api_key_env": config.api_key_env,
        },
    }
    release = AssistantRelease.objects.create(
        target_kind="workflow", target_id=str(workflow.id), version=1, payload=legacy
    )

    migration = importlib.import_module(
        "backend.apps.ai_assistant.migrations.0089_backfill_workflow_release_binding"
    )
    migration.backfill_workflow_release_binding(django_apps, None)
    release.refresh_from_db()
    assert release.payload["executor"]["assistant_id"] == executor.assistant_id
    assert release.payload["executor"]["run_name"] == "旧执行名片"
    assert release.payload["verifier"]["run_name"] == "旧验收名片"
    assert release.payload["executor"]["system_prompt"] == "发布当时的执行提示词"
    assert release.payload["executor"]["tools"] == [{"domain": "adb", "preset": "all"}]

    first_pass = dict(release.payload)
    migration.backfill_workflow_release_binding(django_apps, None)
    release.refresh_from_db()
    assert release.payload == first_pass

    resolved = assistant_api.resolve_sop_release(workflow.id, 1)
    assert task_runner._binding(resolved["executor"]).run_name == "旧执行名片"
    assert task_runner._binding(resolved["verifier"]).run_name == "旧验收名片"
