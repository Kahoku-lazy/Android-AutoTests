"""
临时脚本：将两条登录页用例合并到一个任务中执行
用法: python tools/run_login_cases.py
"""

import asyncio
import json
import os
import sys
import time

from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()

from apps.case_manager.models_web import WebTestCase
from apps.test_runner.models import TaskCard, TestResult, TestRunRecord
from apps.test_runner.views.execution import _execute_unified_remote
from models.step_types import TestStep
from models.test_models import TestCaseDef

CASE_IDS = [
    "WEB-20260728-155438-7389",  # 登录页面跳转登录
    "WEB-20260728-160030-1116",  # 登录页面——记住账号
]


def build_testcase_def(row):
    steps_raw = json.loads(getattr(row, "steps_json", "[]") or "[]")
    steps_data = [TestStep.from_dict(s) for s in steps_raw]
    return TestCaseDef(
        id=row.id,
        title=row.title,
        steps_data=steps_data,
        task_type="web_automation",
        extra_data={
            "url": getattr(row, "url", ""),
            "steps": getattr(row, "steps", ""),
            "expected_result": getattr(row, "expected_result", ""),
        },
    )


def main():
    # 1. Load both cases
    test_cases = []
    titles = []
    for cid in CASE_IDS:
        try:
            row = WebTestCase.objects.get(id=cid, enabled=True)
            test_cases.append(build_testcase_def(row))
            titles.append(f"[{row.id}] {row.title}")
        except WebTestCase.DoesNotExist:
            print(
                json.dumps(
                    {"status": False, "error": f"用例不存在或未启用: {cid}"}, ensure_ascii=False
                )
            )
            sys.exit(1)

    print(f"用例加载完成:\n" + "\n".join(f"  • {t}" for t in titles))

    loop_count = 1
    timeout = 5
    ts = str(int(time.time()))[-6:]
    task_id = f"WEB-{ts}-BATCH"[:50]

    # 2. Create TaskCard
    task_card = TaskCard.objects.create(
        task_id=task_id,
        name="登录页测试合集",
        creator="cli",
        task_type="web_automation",
        mode="immediate",
        device_serial="web",
        case_ids=CASE_IDS,
        loop_count=loop_count,
        interval_seconds=timeout,
        status="queued",
        running=False,
        start_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )

    print(f"任务卡片已创建: {task_id}")

    # 3. Execute
    async def _exec():
        try:
            await _execute_unified_remote(
                task_id,
                test_cases,
                loop_count,
                timeout,
                client_task_id=task_id,
                task_type="web_automation",
                device_label="web",
            )
        except Exception:
            import traceback

            traceback.print_exc()

    print("开始执行...")
    asyncio.run(_exec())

    # 4. Collect results
    results = list(
        TestResult.objects.filter(run__run_id=task_id).values(
            "case_id",
            "case_type",
            "iteration",
            "result",
            "duration_ms",
            "detail",
        )
    )
    run_record = (
        TestRunRecord.objects.filter(run_id=task_id)
        .values(
            "status",
            "summary",
            "started_at",
            "finished_at",
        )
        .first()
    )

    task_card.refresh_from_db()

    passed = sum(1 for r in results if r["result"] == "pass")
    failed = sum(1 for r in results if r["result"] == "fail")

    # Print results grouped by case
    by_case = {}
    for r in results:
        by_case.setdefault(r["case_id"], []).append(r)

    print("\n" + "=" * 60)
    print("执行结果:")
    for case_id, case_results in by_case.items():
        cp = sum(1 for r in case_results if r["result"] == "pass")
        cf = sum(1 for r in case_results if r["result"] == "fail")
        status_icon = "✅" if cf == 0 else "❌"
        print(f"  {status_icon} {case_id}: {cp}/{len(case_results)} 通过")
        for r in case_results:
            detail = (r["detail"] or "")[:150]
            icon = "  ✓" if r["result"] == "pass" else "  ✗"
            print(
                f"    {icon} iter={r['iteration']} | {r['result']} | {r['duration_ms']:.0f}ms | {detail}"
            )

    print(f"\n总计: {passed}/{len(results)} 通过")

    if task_card.outcome == "interrupted" and task_card.status == "done":
        task_card.outcome = "completed"
    task_card.save(update_fields=["outcome"])

    print(f"任务状态: {task_card.status}, 结果: {task_card.outcome}")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
