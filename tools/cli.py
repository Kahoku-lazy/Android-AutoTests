"""
CLI 工具 — 用例管理 CRUD
用法:
  python tools/cli.py case list       [--type web] [--search 关键词]
  python tools/cli.py case create     --type web --title xxx [--file case.json]
  python tools/cli.py case show       <case_id>
  python tools/cli.py case delete     <case_id>

  python tools/cli.py dir list        [--type web] [--parent-id N]
  python tools/cli.py dir create      --name xxx [--type web] [--parent-id N]
  python tools/cli.py dir tree

输出: JSON {ok, data/error}

注：原 element 域（Web 元素 CRUD）随元素定位的 Web/API 两域整体下线而移除
（变更 remove-element-locator-web-api）。
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()

from apps.case_manager.models import CaseDirectory, CaseProject, TestDefinition  # noqa: E402

# ═══════════════════════════════════════════
# helpers
# ═══════════════════════════════════════════


def ok(data=None):
    print(json.dumps({"status": True, "data": data}, ensure_ascii=False, indent=2))


def err(msg):
    print(json.dumps({"status": False, "message": msg}, ensure_ascii=False, indent=2))
    sys.exit(1)


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
    parser = argparse.ArgumentParser(description="CLI 工具 — 用例管理 CRUD")
    sub = parser.add_subparsers(dest="domain", help="操作域: case | dir")

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
