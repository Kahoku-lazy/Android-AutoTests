"""
CLI 工具 — 元素定位 + 用例管理 CRUD + 任务执行
用法:
  python tools/cli.py element list    [--page-url /login] [--search 关键词]
  python tools/cli.py element create  --name xxx --type css_selector --value "xxx" --page-url /login [--group 分组名]
  python tools/cli.py element delete  <element_id>
  python tools/cli.py element batch   --file elements.json

  python tools/cli.py case list       [--type web] [--search 关键词]
  python tools/cli.py case create     --type web --title xxx [--file case.json]
  python tools/cli.py case show       <case_id>
  python tools/cli.py case delete     <case_id>

  python tools/cli.py run             --case-id WEB-xxx [--loop 3] [--timeout 5]

输出: JSON {ok, data/error}
"""
import argparse
import asyncio
import json
import os
import random
import string
import sys
import textwrap
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()

from apps.element_locator.models import WebGroup, WebElement  # noqa: E402
from apps.case_manager.models import CaseDirectory  # noqa: E402
from apps.case_manager.models_web import WebTestCase  # noqa: E402
from apps.test_runner.models import TaskCard, TestRunRecord, TestResult  # noqa: E402
from models.test_models import TestCaseDef  # noqa: E402
from models.step_types import TestStep  # noqa: E402
from apps.test_runner.views.execution import _execute_unified_remote  # noqa: E402


# ═══════════════════════════════════════════
# helpers
# ═══════════════════════════════════════════

def ok(data=None):
    print(json.dumps({"ok": True, "data": data}, ensure_ascii=False, indent=2))


def err(msg):
    print(json.dumps({"ok": False, "error": msg}, ensure_ascii=False, indent=2))
    sys.exit(1)


def get_or_create_group(name, parent=None):
    """Find or create a WebGroup. Returns (group, created)."""
    qs = WebGroup.objects.filter(name=name)
    if parent:
        qs = qs.filter(parent=parent)
    g = qs.first()
    if g:
        return g, False
    g = WebGroup.objects.create(name=name, parent=parent, is_folder=False)
    return g, True


# ═══════════════════════════════════════════
# element commands
# ═══════════════════════════════════════════

def element_list(args):
    qs = WebElement.objects.all()
    if args.page_url:
        qs = qs.filter(page_url__icontains=args.page_url)
    if args.search:
        from django.db.models import Q
        qs = qs.filter(
            Q(name__icontains=args.search) | Q(locator_value__icontains=args.search) | Q(
                description__icontains=args.search)
        )
    rows = []
    for el in qs.select_related("group").order_by("page_url", "group__name", "name"):
        rows.append({
            "id": el.id,
            "name": el.name,
            "locator_type": el.locator_type,
            "locator_value": el.locator_value,
            "page_url": el.page_url,
            "group": el.group.name if el.group else None,
            "description": el.description,
            "is_test_point": el.is_test_point,
        })
    ok({"count": len(rows), "elements": rows})


def element_create(args):
    group = None
    if args.group:
        group, _ = get_or_create_group(args.group)
    el = WebElement.objects.create(
        name=args.name,
        locator_type=args.type,
        locator_value=args.value,
        page_url=args.page_url,
        description=args.description or "",
        group=group,
    )
    ok({"id": el.id, "name": el.name, "action": "created"})


def element_delete(args):
    try:
        el = WebElement.objects.get(id=args.id)
        name = el.name
        el.delete()
        ok({"id": args.id, "name": name, "action": "deleted"})
    except WebElement.DoesNotExist:
        err(f"元素不存在: {args.id}")


def element_batch(args):
    with open(args.file, "r", encoding="utf-8") as f:
        data = json.load(f)
    groups = data.get("groups", {})
    elements = data.get("elements", [])

    created_groups = {}
    group_cache = {g.name: g for g in WebGroup.objects.all()}

    # Create/find groups
    for gkey, ginfo in groups.items():
        parent = group_cache.get(ginfo.get("parent")) if ginfo.get("parent") else None
        g, is_new = get_or_create_group(ginfo["name"], parent=parent)
        created_groups[gkey] = g
        if is_new:
            group_cache[g.name] = g

    objs = []
    for item in elements:
        g = created_groups.get(item.get("_group")) if item.get("_group") else None
        objs.append(WebElement(
            group=g,
            name=item["name"],
            locator_type=item["locator_type"],
            locator_value=item["locator_value"],
            page_url=item.get("page_url", ""),
            description=item.get("description", ""),
            is_test_point=item.get("is_test_point", False),
        ))
    WebElement.objects.bulk_create(objs)
    ok({"created": len(objs), "groups": len(created_groups)})


# ═══════════════════════════════════════════
# case commands
# ═══════════════════════════════════════════

def case_list(args):
    qs = WebTestCase.objects.all()
    if args.type and args.type != "web":
        err(f"当前仅支持 --type web")
    if args.search:
        qs = qs.filter(title__icontains=args.search)
    rows = []
    for c in qs.order_by("-updated_at"):
        steps = []
        try:
            steps = json.loads(c.steps_json or "[]")
        except json.JSONDecodeError:
            pass
        rows.append({
            "id": c.id,
            "title": c.title,
            "priority": c.priority,
            "enabled": c.enabled,
            "url": c.url,
            "step_count": len(steps),
            "directory_id": c.directory_id,
            "updated_at": str(c.updated_at)[:19] if c.updated_at else "",
        })
    ok({"count": len(rows), "cases": rows})


def case_create(args):
    steps_json = "[]"
    directory_id = getattr(args, "directory_id", None)
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            case_data = json.load(f)
        steps_json = json.dumps(case_data.get("steps", []), ensure_ascii=False)
        title = case_data.get("title", args.title or "")
        url = case_data.get("url", "")
        priority = case_data.get("priority", "P1")
        description = case_data.get("description", "")
        expected_result = case_data.get("expected_result", "")
        if case_data.get("directory_id") and not directory_id:
            directory_id = case_data["directory_id"]
    else:
        title = args.title or ""
        url = args.url or ""
        priority = args.priority or "P1"
        description = ""
        expected_result = ""
        if args.steps_json:
            steps_json = args.steps_json

    if not title:
        err("--title 不能为空")

    now = datetime.now()
    suffix = "".join(random.choices(string.digits, k=4))
    case_id = f"WEB-{now.strftime('%Y%m%d')}-{now.strftime('%H%M%S')}-{suffix}"

    c = WebTestCase.objects.create(
        id=case_id,
        title=title,
        case_type="web_automation",
        priority=priority,
        url=url,
        steps_json=steps_json,
        description=description,
        expected_result=expected_result,
        enabled=True,
        directory_id=directory_id,
    )
    ok({"id": c.id, "title": c.title, "action": "created", "updated_at": str(c.updated_at)[:19]})


def case_show(args):
    try:
        c = WebTestCase.objects.get(id=args.id)
    except WebTestCase.DoesNotExist:
        err(f"用例不存在: {args.id}")
    steps = []
    try:
        steps = json.loads(c.steps_json or "[]")
    except json.JSONDecodeError:
        pass
    ok({
        "id": c.id, "title": c.title, "priority": c.priority,
        "enabled": c.enabled, "url": c.url,
        "precondition": c.precondition, "description": c.description,
        "expected_result": c.expected_result,
        "steps": steps,
        "directory_id": c.directory_id,
        "created_at": str(c.created_at)[:19] if c.created_at else "",
        "updated_at": str(c.updated_at)[:19] if c.updated_at else "",
    })


def case_delete(args):
    try:
        c = WebTestCase.objects.get(id=args.id)
        title = c.title
        c.delete()
        ok({"id": args.id, "title": title, "action": "deleted"})
    except WebTestCase.DoesNotExist:
        err(f"用例不存在: {args.id}")


# ═══════════════════════════════════════════
# dir commands
# ═══════════════════════════════════════════

_TYPE_MAP = {"web": "web_automation", "ui": "ui_automation", "api": "api_testing", "storage": "storage"}


def dir_list(args):
    case_type = _TYPE_MAP.get(args.type, "web_automation")
    qs = CaseDirectory.objects.filter(case_type=case_type)
    if args.parent_id is not None:
        qs = qs.filter(parent_id=args.parent_id)
    else:
        qs = qs.filter(parent__isnull=True)
    rows = []
    for d in qs.order_by("sort_order", "name"):
        rows.append({
            "id": d.id, "name": d.name, "case_type": d.case_type,
            "parent_id": d.parent_id,
            "child_count": d.children.count(),
        })
    ok({"count": len(rows), "directories": rows})


def dir_create(args):
    case_type = _TYPE_MAP.get(args.type, "web_automation")
    d = CaseDirectory.objects.create(
        name=args.name,
        case_type=case_type,
        parent_id=args.parent_id,
    )
    ok({"id": d.id, "name": d.name, "case_type": d.case_type, "parent_id": d.parent_id, "action": "created"})


def dir_tree(args):
    """Print a tree view of all directories."""
    all_dirs = CaseDirectory.objects.all().order_by("case_type", "parent_id", "sort_order", "name")
    by_type = {}
    for d in all_dirs:
        by_type.setdefault(d.case_type, []).append(d)

    lines = []
    for ct, dirs in by_type.items():
        lines.append(f"\n[{ct}]")
        roots = [d for d in dirs if d.parent_id is None]
        children_by_parent = {}
        for d in dirs:
            if d.parent_id:
                children_by_parent.setdefault(d.parent_id, []).append(d)

        def _print_tree(node, indent=0):
            prefix = "  " * indent + ("├─ " if indent > 0 else "")
            lines.append(f"{prefix}{node.name} (id={node.id})")
            for child in children_by_parent.get(node.id, []):
                _print_tree(child, indent + 1)

        for root in roots:
            _print_tree(root)

    output = "\n".join(lines)
    ok({"tree": output})


# ═══════════════════════════════════════════
# run command
# ═══════════════════════════════════════════

def _build_testcase_def(row):
    """Build a TestCaseDef from a WebTestCase ORM row."""
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


def run_case(args):
    """Execute a web test case via the execution engine and return results."""
    case_id = args.case_id
    loop_count = getattr(args, "loop", 3)
    timeout = getattr(args, "timeout", 5)

    try:
        row = WebTestCase.objects.get(id=case_id, enabled=True)
    except WebTestCase.DoesNotExist:
        err(f"用例不存在或未启用: {case_id}")

    test_case = _build_testcase_def(row)
    ts = str(int(time.time()))[-6:]
    task_id = f"WEB-{ts}-{case_id}"[:50]  # TaskCard.task_id, also used as client_task_id

    # Create TaskCard so it shows up in the frontend task list
    # IMPORTANT: task_id MUST match client_task_id passed to _execute_unified_remote,
    # otherwise _execute_tests can't find the TaskCard to populate case_items.
    task_card = TaskCard.objects.create(
        task_id=task_id,
        name=row.title,
        creator="cli",
        task_type="web_automation",
        mode="immediate",
        device_serial="web",
        case_ids=[case_id],
        loop_count=loop_count,
        interval_seconds=timeout,
        status="queued",
        running=False,
        start_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )

    async def _exec():
        try:
            await _execute_unified_remote(
                task_id, [test_case], loop_count, timeout,
                client_task_id=task_id,
                task_type="web_automation",
                device_label="web",
            )
        except Exception:
            import traceback
            traceback.print_exc()

    asyncio.run(_exec())

    # Collect results — TestRunRecord.run_id == task_id (passed as run_id to engine)
    results = list(TestResult.objects.filter(run__run_id=task_id).values(
        "case_id", "case_type", "result", "duration_ms", "detail",
    ))
    run_record = TestRunRecord.objects.filter(run_id=task_id).values(
        "status", "summary", "started_at", "finished_at",
    ).first()

    passed = sum(1 for r in results if r["result"] == "pass")
    failed = sum(1 for r in results if r["result"] == "fail")

    # TaskCard.case_items / overall_pass etc. are already populated by _execute_tests
    # (it looks up TaskCard by client_task_id, which matches our task_id).
    # Refresh from DB, then fix up any cosmetic state-machine issues.
    task_card.refresh_from_db()

    # Build execution logs from TestResult details (WebSocket logs unavailable in CLI mode)
    now_str = datetime.now().strftime("%H:%M:%S")
    log_entries = [
        {"time": now_str, "text": f"任务开始: [{case_id}] {row.title}", "level": "info"},
    ]
    for i, r in enumerate(results):
        level = "success" if r["result"] == "pass" else "error"
        log_entries.append({
            "time": now_str,
            "text": f"  迭代 {i + 1}/{len(results)}: {r['result']} ({r['duration_ms']:.0f}ms) — {r['detail']}",
            "level": level,
        })
    log_entries.append({
        "time": now_str,
        "text": f"任务完成: {passed}/{len(results)} 通过" + (f", {failed} 失败" if failed else ""),
        "level": "success" if failed == 0 else "warn",
    })

    # Fix outcome if engine left it as interrupted (state-machine race in sync CLI mode)
    if task_card.outcome == "interrupted" and task_card.status == "done":
        task_card.outcome = "completed"

    # Build failed_steps from step_details for BUG section display
    orm_results = TestResult.objects.filter(run__run_id=task_id)
    failed_steps = []
    for tr in orm_results:
        for sd in (tr.step_details or []):
            if sd.get("result") == "fail":
                failed_steps.append({
                    "caseId": tr.case_id,
                    "caseTitle": row.title,
                    "iteration": sd.get("iteration", tr.iteration),
                    "stepIndex": sd.get("index", 0),
                    "stepType": sd.get("type", ""),
                    "description": sd.get("description", ""),
                    "result": sd.get("error", "步骤执行失败"),
                    "screenshot": sd.get("screenshot", ""),
                    "_date": str(tr.created_at)[:19] if tr.created_at else "",
                })

    task_card.logs = log_entries
    task_card.failed_steps = failed_steps
    task_card.save(update_fields=["outcome", "logs", "failed_steps"])

    ok({
        "task_id": task_id,
        "case_id": case_id,
        "title": row.title,
        "loop_count": loop_count,
        "status": run_record["status"] if run_record else "UNKNOWN",
        "summary": run_record["summary"] if run_record else {},
        "total": len(results),
        "passed": passed,
        "failed": failed,
        "results": [
            {
                "case_id": r["case_id"],
                "result": r["result"],
                "duration_ms": r["duration_ms"],
                "detail": (r["detail"] or "")[:200],
            }
            for r in results
        ],
    })


# ═══════════════════════════════════════════
# CLI parser
# ═══════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="CLI 工具 — 元素定位 + 用例管理 CRUD")
    sub = parser.add_subparsers(dest="domain", help="操作域: element | case")

    # ── element ──
    ep = sub.add_parser("element", help="Web 元素 CRUD")
    esp = ep.add_subparsers(dest="action")

    p = esp.add_parser("list", help="列出 Web 元素")
    p.add_argument("--page-url", help="按页面 URL 过滤")
    p.add_argument("--search", help="搜索 name/locator_value/description")

    p = esp.add_parser("create", help="创建 Web 元素")
    p.add_argument("--name", required=True, help="元素名称")
    p.add_argument("--type", required=True, dest="type",
                   choices=["css_selector", "xpath", "id", "class_name", "name", "tag_name",
                            "link_text", "partial_link_text", "text", "test_id", "role", "placeholder"],
                   help="定位器类型")
    p.add_argument("--value", required=True, dest="value", help="定位器值")
    p.add_argument("--page-url", required=True, dest="page_url", help="页面 URL")
    p.add_argument("--group", help="元素分组名称")
    p.add_argument("--description", help="元素描述")

    p = esp.add_parser("delete", help="删除 Web 元素")
    p.add_argument("id", type=int, help="元素 ID")

    p = esp.add_parser("batch", help="批量导入 Web 元素")
    p.add_argument("--file", required=True, dest="file", help="JSON 文件路径")

    # ── case ──
    cp = sub.add_parser("case", help="测试用例 CRUD")
    csp = cp.add_subparsers(dest="action")

    p = csp.add_parser("list", help="列出测试用例")
    p.add_argument("--type", choices=["web"], default="web", help="用例类型 (当前仅 web)")
    p.add_argument("--search", help="搜索标题")

    p = csp.add_parser("create", help="创建测试用例")
    p.add_argument("--type", choices=["web"], default="web", help="用例类型 (当前仅 web)")
    p.add_argument("--title", help="用例标题")
    p.add_argument("--url", help="目标 URL")
    p.add_argument("--priority", choices=["P0", "P1", "P2"], default="P1", help="优先级")
    p.add_argument("--steps-json", dest="steps_json", help="步骤 JSON 字符串 (仅简单场景)")
    p.add_argument("--file", help="从 JSON 文件读取 (含 title/steps/url 等)")
    p.add_argument("--directory-id", type=int, dest="directory_id", help="父目录 ID")

    p = csp.add_parser("show", help="查看用例详情")
    p.add_argument("id", help="用例 ID")

    p = csp.add_parser("delete", help="删除测试用例")
    p.add_argument("id", help="用例 ID")

    # ── dir ──
    dp = sub.add_parser("dir", help="目录 CRUD")
    dsp = dp.add_subparsers(dest="action")

    p = dsp.add_parser("list", help="列出目录树")
    p.add_argument("--type", choices=["web", "ui", "api", "storage"],
                   default="web", help="用例类型")
    p.add_argument("--parent-id", type=int, dest="parent_id", help="只列出指定父级下的子目录")

    p = dsp.add_parser("create", help="创建目录")
    p.add_argument("--name", required=True, help="目录名称")
    p.add_argument("--type", choices=["web", "ui", "api", "storage"],
                   default="web", help="用例类型")
    p.add_argument("--parent-id", type=int, dest="parent_id", help="父级目录 ID")

    p = dsp.add_parser("tree", help="显示完整目录树")

    # ── run ──
    rp = sub.add_parser("run", help="执行测试任务")
    rp.add_argument("--case-id", required=True, dest="case_id", help="要执行的用例 ID")
    rp.add_argument("--loop", type=int, default=1, help="循环次数 (默认 1)")
    rp.add_argument("--timeout", type=int, default=5, help="步骤间隔秒数 (默认 5)")

    args = parser.parse_args()
    if not args.domain:
        parser.print_help()
        sys.exit(1)

    # Dispatch
    dispatch = {
        ("element", "list"): element_list,
        ("element", "create"): element_create,
        ("element", "delete"): element_delete,
        ("element", "batch"): element_batch,
        ("case", "list"): case_list,
        ("case", "create"): case_create,
        ("case", "show"): case_show,
        ("case", "delete"): case_delete,
        ("dir", "list"): dir_list,
        ("dir", "create"): dir_create,
        ("dir", "tree"): dir_tree,
        ("run", None): run_case,
    }
    fn = dispatch.get((args.domain, getattr(args, "action", None)))
    if fn:
        fn(args)
    else:
        err(f"未知命令: {args.domain} {getattr(args, 'action', '')}")


if __name__ == "__main__":
    main()
