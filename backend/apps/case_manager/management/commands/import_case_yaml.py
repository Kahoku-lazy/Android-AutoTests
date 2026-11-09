"""按目录同步 YAML 用例到平台用例库。

用法：
    python manage.py import_case_yaml --dir <目录> [--project <项目名>]
        [--owner <用户名或编号>] [--dry-run] [--prune]

每份 YAML 映射为项目下的一张用例表，表名取文件在目录内的相对路径；
重复同步按标题覆盖，`--prune` 才删除 YAML 中已消失的行。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError

from backend.apps.case_manager.api_yaml import import_yaml_text, parse_yaml_text
from backend.apps.case_manager.models import CaseProject

DEFAULT_PROJECT = "YAML 用例库"
"""未指定 `--project` 时使用的项目名。"""

FILE_NAME_FALLBACK = "用例表"
"""相对路径算不出表名时的兜底名。"""


def _table_name(root: Path, path: Path) -> str:
    """把文件相对路径转成用例表名：分隔符换成 ` / `，去掉扩展名。"""
    try:
        relative = path.relative_to(root)
    except ValueError:
        relative = Path(path.name)
    stem = relative.with_suffix("")
    parts = [part for part in stem.parts if part not in {"", "."}]
    name = " / ".join(parts).strip()
    return name or FILE_NAME_FALLBACK


def _yaml_files(root: Path) -> list[Path]:
    """递归列出目录下的 YAML 文件，按路径排序保证同步顺序稳定。"""
    return sorted(
        [
            path
            for path in root.rglob("*")
            if path.is_file() and path.suffix.lower() in {".yaml", ".yml"}
        ]
    )


def _read_text(path: Path) -> str:
    """按 UTF-8 读正文，兼容带 BOM 的文件。

    Raises:
        UnicodeDecodeError: 文件不是 UTF-8 编码。
    """
    return path.read_text(encoding="utf-8-sig")


def _resolve_owner(value: str):
    """按用户名或编号取项目归属用户，缺省用第一个超级用户。

    Raises:
        CommandError: 没有可用用户，或指定用户不存在。
    """
    user_model = get_user_model()
    text = (value or "").strip()
    if not text:
        owner = user_model.objects.filter(is_superuser=True).order_by("id").first()
        if owner is None:
            raise CommandError("没有可用的归属用户，请用 --owner 指定")
        return owner
    if text.isdigit():
        owner = user_model.objects.filter(id=int(text)).first()
    else:
        owner = user_model.objects.filter(username=text).first()
    if owner is None:
        raise CommandError(f"用户不存在：{text}")
    return owner


def _get_or_create_project(*, owner, name: str) -> CaseProject:
    """按「归属用户 + 项目名」取用例项目，不存在时创建。"""
    try:
        project, _created = CaseProject.objects.get_or_create(
            created_by=str(owner.id),
            name=name,
            defaults={"description": "由本地 YAML 目录同步"},
        )
    except IntegrityError:
        project = CaseProject.objects.get(created_by=str(owner.id), name=name)
    return project


class Command(BaseCommand):
    """按目录同步 YAML 用例：每份 YAML 一张表，按标题幂等覆盖。"""

    help = "把目录下的 YAML 用例同步到平台用例库（每份 YAML 一张表，重复同步幂等）"

    def add_arguments(self, parser) -> None:
        """声明命令行参数。"""
        parser.add_argument("--dir", required=True, help="YAML 所在目录")
        parser.add_argument(
            "--project", default=DEFAULT_PROJECT, help=f"目标项目名（默认 {DEFAULT_PROJECT}）"
        )
        parser.add_argument(
            "--owner", default="", help="归属用户（用户名或编号，默认第一个超级用户）"
        )
        parser.add_argument("--dry-run", action="store_true", help="只解析不写库")
        parser.add_argument("--prune", action="store_true", help="删除 YAML 中已不存在的旧用例行")

    def handle(self, *args: Any, **options: Any) -> None:
        """遍历目录并逐份导入，最后打印汇总。

        Raises:
            CommandError: 目录不存在、没有 YAML，或归属用户不可用。
        """
        root = Path(str(options["dir"])).expanduser()
        if not root.is_dir():
            raise CommandError(f"目录不存在：{root}")
        paths = _yaml_files(root)
        if not paths:
            raise CommandError(f"目录下没有 YAML 文件：{root}")

        dry_run = bool(options["dry_run"])
        prune = bool(options["prune"])
        owner = _resolve_owner(str(options["owner"]))
        project = (
            None if dry_run else _get_or_create_project(owner=owner, name=str(options["project"]))
        )
        if project is None:
            self.stdout.write(
                f"项目：{options['project']}（试运行不建库）  归属：{owner.get_username()}"
            )
        else:
            self.stdout.write(
                f"项目：{project.name}（#{project.id}）  归属：{owner.get_username()}"
            )
        self.stdout.write(
            f"目录：{root}  文件：{len(paths)}  模式：{'试运行' if dry_run else '写入'}"
        )

        totals = {"files": 0, "cases": 0, "created": 0, "updated": 0, "removed": 0}
        skipped: list[tuple[str, str]] = []
        for path in paths:
            name = _table_name(root, path)
            try:
                text = _read_text(path)
            except UnicodeDecodeError:
                skipped.append((name, "不是 UTF-8 编码"))
                continue
            if dry_run:
                rows, reason = parse_yaml_text(text)
                if reason:
                    skipped.append((name, reason))
                    continue
                totals["files"] += 1
                totals["cases"] += len(rows)
                self.stdout.write(f"  [试运行] {name}：{len(rows)} 条")
                continue
            try:
                result = import_yaml_text(
                    project_id=project.id,
                    user_id=str(owner.id),
                    text=text,
                    file_name=name,
                    prune=prune,
                )
            except (ValueError, LookupError) as exc:
                skipped.append((name, str(exc)))
                continue
            totals["files"] += 1
            totals["cases"] += result["total"]
            totals["created"] += result["created"]
            totals["updated"] += result["updated"]
            totals["removed"] += result["removed"]
            self.stdout.write(
                f"  {name}：共 {result['total']} 条，新建 {result['created']}，"
                f"更新 {result['updated']}，删除 {result['removed']}"
            )

        self.stdout.write(
            f"汇总：文件 {totals['files']}，用例 {totals['cases']}，新建 {totals['created']}，"
            f"更新 {totals['updated']}，删除 {totals['removed']}，跳过 {len(skipped)}"
        )
        for name, reason in skipped:
            self.stdout.write(f"  跳过 {name}：{reason}")
