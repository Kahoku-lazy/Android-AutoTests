"""L1b 枚举收敛：tr_test_runs.status 大写存量 → 小写回填（幂等）。

历史写库口径混用：state_machine 写大写（COMPLETED/RUNNING/FAILED/STOPPED），
执行器枚举为小写。收敛后唯一真相源 TestRunStatus 为小写（models/test_models.py），
本迁移把存量统一为小写，保证统计口径一致。
"""

from django.db import migrations

_STATUS_MAP = {
    "PENDING": "pending",
    "RUNNING": "running",
    "COMPLETED": "completed",
    "PASSED": "passed",  # 幽灵值（枚举曾定义，无写库方），一并归并
    "FAILED": "failed",
    "STOPPED": "stopped",
    "SUCCESS": "completed",  # 历史别名，统计归入完成
}


def _backfill(apps, schema_editor):
    TestRunRecord = apps.get_model("test_runner", "TestRunRecord")
    for old, new in _STATUS_MAP.items():
        TestRunRecord.objects.filter(status=old).update(status=new)


def _revert(apps, schema_editor):
    TestRunRecord = apps.get_model("test_runner", "TestRunRecord")
    reverse = {v: k for k, v in _STATUS_MAP.items()}
    for new, old in reverse.items():
        TestRunRecord.objects.filter(status=new).update(status=old)


class Migration(migrations.Migration):
    dependencies = [
        ("test_runner", "0018_testresult_step_details"),
    ]

    operations = [
        migrations.RunPython(_backfill, _revert),
    ]
