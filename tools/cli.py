"""
CLI 工具 — 元素定位 + 用例管理 CRUD
用法:
  python tools/cli.py element list    [--page-url /login] [--search 关键词]
  python tools/cli.py element create  --name xxx --type css_selector --value "xxx" --page-url /login [--group 分组名]
  python tools/cli.py element delete  <element_id>
  python tools/cli.py element batch   --file elements.json

  python tools/cli.py case list       [--type web] [--search 关键词]
  python tools/cli.py case create     --type web --title xxx [--file case.json]
  python tools/cli.py case show       <case_id>
  python tools/cli.py case delete     <case_id>

输出: JSON {ok, data/error}
"""

import argparse
import json
import os
import random
import string
import sys

from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()

from apps.case_manager.models import CaseDirectory, CaseProject, TestDefinition  # noqa: E402
from apps.element_locator.models import WebElement, WebGroup  # noqa: E402

# ═══════════════════════════════════════════
# helpers
# ═══════════════════════════════════════════


def ok(data=None):
    print(json.dumps({"status": True, "data": data}, ensure_ascii=False, indent=2))


def err(msg):
    print(json.dumps({"status": False, "message": msg}, ensure_ascii=False, indent=2))
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
            Q(name__icontains=args.search)
            | Q(locator_value__icontains=args.search)
            | Q(description__icontains=args.search)
        )
    rows = []
    for el in qs.select_related("group").order_by("page_url", "group__name", "name"):
        rows.append(
            {
                "id": el.id,
                "name": el.name,
                "locator_type": el.locator_type,
                "locator_value": el.locator_value,
                "page_url": el.page_url,
                "group": el.group.name if el.group else None,
                "description": el.description,
                "is_test_point": el.is_test_point,
            }
        )
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
        objs.append(
            WebElement(
                group=g,
                name=item["name"],
                locator_type=item["locator_type"],
                locator_value=item["locator_value"],
                page_url=item.get("page_url", ""),
                description=item.get("description", ""),
                is_test_point=item.get("is_test_point", False),
            )
        )
    WebElement.objects.bulk_create(objs)
    ok({"created": len(objs), "groups": len(created_groups)})


# ═══════════════════════════════════════════
# case / dir commands (document cases)
# ═══════════════════════════════════════════


def case_list(args):
    qs = TestDefinition.objects.all()
    if getattr(args, "search", None):
        qs = qs.filter(title__icontains=args.search)
    rows = [
        {
            "id": c.id,
            "title": c.title,
            "test_type": c.test_type,
            "business_type": c.business_type,
            "project_id": c.project_id,
            "directory_id": c.directory_id,
            "updated_at": str(c.updated_at)[:19] if c.updated_at else "",
        }
        for c in qs.order_by("-updated_at")
    ]
    ok({"count": len(rows), "cases": rows})


def case_create(args):
    err("请使用平台「用例管理」创建文档用例（CLI 新建已停用）")


def case_show(args):
    try:
        c = TestDefinition.objects.get(id=args.id)
    except TestDefinition.DoesNotExist:
        err(f"用例不存在: {args.id}")
        return
    ok(
        {
            "id": c.id,
            "title": c.title,
            "test_type": c.test_type,
            "business_type": c.business_type,
            "module": c.module,
            "precondition": c.precondition,
            "steps": c.steps,
            "expected_result": c.expected_result,
            "project_id": c.project_id,
            "directory_id": c.directory_id,
        }
    )


def case_delete(args):
    try:
        c = TestDefinition.objects.get(id=args.id)
        title = c.title
        c.delete()
        ok({"id": args.id, "title": title, "action": "deleted"})
    except TestDefinition.DoesNotExist:
        err(f"用例不存在: {args.id}")


def dir_list(args):
    qs = CaseDirectory.objects.all()
    if getattr(args, "parent_id", None) is not None:
        qs = qs.filter(parent_id=args.parent_id)
    else:
        qs = qs.filter(parent__isnull=True)
    rows = [
        {
            "id": d.id,
            "name": d.name,
            "project_id": d.project_id,
            "parent_id": d.parent_id,
            "child_count": d.children.count(),
        }
        for d in qs.order_by("sort_order", "name")
    ]
    ok({"count": len(rows), "directories": rows})


def dir_create(args):
    err("请使用平台「用例管理」创建目录（CLI 新建已停用）")


def dir_tree(args):
    projects = CaseProject.objects.all().order_by("id")
    lines = []
    for proj in projects:
        lines.append(f"[project {proj.id}] {proj.name}")
        dirs = list(
            CaseDirectory.objects.filter(project=proj).order_by("parent_id", "sort_order", "name")
        )
        by_parent: dict = {}
        for d in dirs:
            by_parent.setdefault(d.parent_id, []).append(d)

        def walk(parent_id, indent):
            for d in by_parent.get(parent_id, []):
                lines.append(f"{indent}- {d.name} (#{d.id})")
                walk(d.id, indent + "  ")

        walk(None, "  ")
    ok({"tree": "\n".join(lines)})


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
    p.add_argument(
        "--type",
        required=True,
        dest="type",
        choices=[
            "css_selector",
            "xpath",
            "id",
            "class_name",
            "name",
            "tag_name",
            "link_text",
            "partial_link_text",
            "text",
            "test_id",
            "role",
            "placeholder",
        ],
        help="定位器类型",
    )
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
    p.add_argument(
        "--type", choices=["web", "ui", "api", "storage"], default="web", help="用例类型"
    )
    p.add_argument("--parent-id", type=int, dest="parent_id", help="只列出指定父级下的子目录")

    p = dsp.add_parser("create", help="创建目录")
    p.add_argument("--name", required=True, help="目录名称")
    p.add_argument(
        "--type", choices=["web", "ui", "api", "storage"], default="web", help="用例类型"
    )
    p.add_argument("--parent-id", type=int, dest="parent_id", help="父级目录 ID")

    p = dsp.add_parser("tree", help="显示完整目录树")

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
    }
    fn = dispatch.get((args.domain, getattr(args, "action", None)))
    if fn:
        fn(args)
    else:
        err(f"未知命令: {args.domain} {getattr(args, 'action', '')}")


if __name__ == "__main__":
    main()
