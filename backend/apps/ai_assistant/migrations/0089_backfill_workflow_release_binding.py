from django.db import migrations

SIDES = (
    ("executor", "executor_assistant_id"),
    ("verifier", "verifier_assistant_id"),
)


def _identity(card, config) -> dict:
    return {
        "assistant_id": card.assistant_id,
        "run_name": card.display_name,
        "base_url": (getattr(config, "base_url", "") if config is not None else "") or "",
    }


def backfill_workflow_release_binding(apps, schema_editor) -> None:
    release_model = apps.get_model("ai_assistant", "AssistantRelease")
    workflow_model = apps.get_model("ai_assistant", "AISopWorkflow")
    card_model = apps.get_model("ai_assistant", "AIAssistant")
    role_model = apps.get_model("ai_assistant", "AIRole")
    config_model = apps.get_model("ai_assistant", "AIModelConfig")

    for release in release_model.objects.filter(target_kind="workflow").iterator():
        try:
            workflow = workflow_model.objects.get(pk=int(release.target_id))
        except (workflow_model.DoesNotExist, TypeError, ValueError):
            continue
        payload = dict(release.payload or {})
        changed = False
        for side_name, card_field in SIDES:
            side = dict(payload.get(side_name) or {})
            if not side:
                continue
            card = card_model.objects.filter(assistant_id=getattr(workflow, card_field)).first()
            if card is None:
                continue
            role = role_model.objects.filter(role_id=card.role_id).first()
            config = (
                config_model.objects.filter(pk=role.model_config_id).first()
                if role is not None and role.model_config_id
                else None
            )
            for key, value in _identity(card, config).items():
                if not side.get(key):
                    side[key] = value
                    changed = True
            payload[side_name] = side
        if not changed:
            continue
        executor_name = (payload.get("executor") or {}).get("run_name") or ""
        verifier = dict(payload.get("verifier") or {})
        if executor_name and executor_name == (verifier.get("run_name") or ""):
            verifier["run_name"] = f"{executor_name}-{verifier.get('assistant_id') or ''}"
            payload["verifier"] = verifier
        release.payload = payload
        release.save(update_fields=["payload"])


class Migration(migrations.Migration):
    dependencies = [
        ("ai_assistant", "0088_eval_case_bank"),
    ]

    operations = [
        migrations.RunPython(backfill_workflow_release_binding, migrations.RunPython.noop),
    ]
