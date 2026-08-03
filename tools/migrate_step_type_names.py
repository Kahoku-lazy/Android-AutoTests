"""
Migrate step type names in all test case definitions.

Old names → New names (Android):
  start_app          → adb_start_app
  kill_app           → adb_kill_app
  wait_toast         → adb_wait_toast
  perf_element_time  → adb_perf_element_time
  if_element_appear  → adb_if_appear
  if_element_disappear → adb_if_disappear
  loop_n             → adb_loop_n
  loop_elements      → adb_loop_elements
  poll_text          → adb_poll_text

Usage:
  python manage.py shell < tools/migrate_step_type_names.py
  # or
  python tools/migrate_step_type_names.py --dry-run  (preview only)
  python tools/migrate_step_type_names.py --execute   (apply changes)
"""

import json
import sys

RENAMES = {
    "start_app": "adb_start_app",
    "kill_app": "adb_kill_app",
    "wait_toast": "adb_wait_toast",
    "perf_element_time": "adb_perf_element_time",
    "if_element_appear": "adb_if_appear",
    "if_element_disappear": "adb_if_disappear",
    "loop_n": "adb_loop_n",
    "loop_elements": "adb_loop_elements",
    "poll_text": "adb_poll_text",
}


def migrate_steps_json(steps_json_str):
    """Replace old type names in a steps_json string. Returns (new_str, count_changes)."""
    if not steps_json_str:
        return steps_json_str, 0

    try:
        steps = json.loads(steps_json_str)
    except (json.JSONDecodeError, TypeError):
        return steps_json_str, 0

    if not isinstance(steps, list):
        return steps_json_str, 0

    changes = 0

    def _walk(items):
        nonlocal changes
        for step in items:
            if not isinstance(step, dict):
                continue
            old_type = step.get("type", "")
            if old_type in RENAMES:
                step["type"] = RENAMES[old_type]
                changes += 1
            children = step.get("children", [])
            if children:
                _walk(children)

    _walk(steps)
    return json.dumps(steps, ensure_ascii=False), changes


def main(dry_run=True):
    from django.apps import apps

    models = []
    # UI automation
    try:
        models.append(apps.get_model("case_manager", "TestDefinition"))
    except LookupError:
        pass
    # Web automation
    try:
        models.append(apps.get_model("case_manager", "WebTestCase"))
    except LookupError:
        pass
    # API testing
    try:
        models.append(apps.get_model("case_manager", "ApiTestCase"))
    except LookupError:
        pass

    total_changes = 0
    total_cases = 0

    for Model in models:
        for row in Model.objects.all():
            total_cases += 1
            old_json = getattr(row, "steps_json", "[]") or "[]"
            new_json, changes = migrate_steps_json(old_json)
            if changes > 0:
                total_changes += changes
                print(f"  [{Model.__name__}] {row.id}: {changes} renames")
                if not dry_run:
                    row.steps_json = new_json
                    row.save(update_fields=["steps_json"])

    print(f"\nTotal: {total_cases} cases checked, {total_changes} step renames")
    if dry_run:
        print("DRY RUN — no changes applied. Use --execute to apply.")
    else:
        print("All changes saved.")


if __name__ == "__main__":
    dry_run = "--execute" not in sys.argv
    if "shell" in sys.argv[0] or "manage.py" in sys.argv[0]:
        import django

        django.setup()
    main(dry_run=dry_run)
