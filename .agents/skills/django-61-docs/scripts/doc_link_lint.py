"""校验文档里引用的 Django 链接是否钉在指定版本（默认 6.1）。

为什么需要它：回答里写 `https://docs.djangoproject.com/en/stable/...` 或漏掉版本段，
半年后同一句话会指向另一个版本，等于不可复核。本脚本把这类"引用漂移"变成可自动判定的错误。

用法示例::

    python doc_link_lint.py .agents/skills/django-61-docs/SKILL.md
    python doc_link_lint.py dev_docs/ARCH_PRD/*.md
    python doc_link_lint.py --changed            # 只查 git 改动（含未跟踪）

判定：
- 错误(E)：链接没有版本段；版本段是 dev/stable/latest；GitHub 引用停在 main/master
- 警告(W)：版本段与 --target 不一致（写 6.0 做对照时属正常，所以默认不 fail）
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys

from pathlib import Path

DOC_URL = re.compile(r"https://docs\.djangoproject\.com/[^\s)\]\"'<>`]+")
GH_URL = re.compile(r"https://github\.com/django/django/(?:blob|tree)/([^\s)\]\"'<>`/]+)")
VERSION_SEGMENT = re.compile(r"^\d+\.\d+$")
FLOATING = {"dev", "stable", "latest"}


def iter_files(explicit: list[str], changed: bool) -> list[Path]:
    """返回待检文件：显式参数优先，否则取 git 改动。"""
    if explicit:
        return [Path(item) for item in explicit]
    if not changed:
        return []
    names: list[str] = []
    for command in (
        ["git", "diff", "--name-only", "HEAD"],
        ["git", "ls-files", "--others", "--exclude-standard"],
    ):
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        names.extend(result.stdout.splitlines())
    suffixes = {".md", ".mdx", ".txt", ".rst"}
    return [Path(n) for n in dict.fromkeys(names) if Path(n).suffix.lower() in suffixes]


def classify(url: str, target: str) -> tuple[str, str] | None:
    """判定一条 docs.djangoproject.com 链接是否合规。"""
    segments = [seg for seg in url.split("docs.djangoproject.com/", 1)[1].split("/") if seg]
    if not segments:
        return "E", "链接为空"
    if segments[0] in FLOATING:
        return "E", f"版本段是 {segments[0]}，会跟随上游漂移"
    if FLOATING & set(segments):
        return "E", "路径里出现 dev/stable/latest，不是固定版本"
    version = next((seg for seg in segments if VERSION_SEGMENT.match(seg)), None)
    if version is None:
        language = segments[0]
        guess = "/".join([language, target, *segments[1:]])
        return "E", f"缺少版本段；fix: https://docs.djangoproject.com/{guess}"
    if version != target:
        return "W", f"版本是 {version}，本次目标是 {target}（做对照时请显式说明）"
    return None


def classify_github(reference: str, target: str) -> tuple[str, str] | None:
    """判定一条 GitHub django/django 源码链接：不接受 main/master，版本不符只警告。"""
    if reference in {"main", "master"}:
        return "E", f"源码引用停在 {reference}，会漂移；fix: 用 tag {target}.x 或 stable/{target}.x"
    if reference.startswith("stable/"):
        pinned = reference.split("/", 1)[1]
        if not pinned.startswith(target):
            return "W", f"源码引用为 {reference}，与目标 {target} 不一致"
        return None
    if not reference.startswith(f"{target}."):
        return "W", f"源码引用为 {reference}，与目标 {target} 不一致"
    return None


def lint_file(path: Path, target: str) -> tuple[int, int]:
    """检查单个文件，返回 (错误数, 警告数)。"""
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as exc:
        print(f"{path}: 读不了（{exc}）", file=sys.stderr)
        return 1, 0

    errors = warnings = 0
    for number, line in enumerate(lines, start=1):
        findings: list[tuple[str, str, str]] = []
        for url in sorted(set(DOC_URL.findall(line))):
            verdict = classify(url, target)
            if verdict:
                findings.append((verdict[0], verdict[1], url))
        for reference in sorted(set(GH_URL.findall(line))):
            verdict = classify_github(reference, target)
            if verdict:
                findings.append((verdict[0], verdict[1], f"django/django@{reference}"))
        for level, reason, subject in findings:
            print(f"{path}:{number}: {level} {reason}\n    {subject}")
            if level == "E":
                errors += 1
            else:
                warnings += 1
    return errors, warnings


def main(argv: list[str] | None = None) -> int:
    """入口：按参数检查文件并给出汇总。"""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="校验 Django 文档链接的版本钉死")
    parser.add_argument("files", nargs="*", help="待检文件；缺省配合 --changed 使用")
    parser.add_argument("--changed", action="store_true", help="只查 git 改动（含未跟踪的新文件）")
    parser.add_argument("--target", default="6.1", help="目标版本，默认 6.1")
    parser.add_argument("--strict", action="store_true", help="把警告也当失败")
    args = parser.parse_args(argv)

    files = iter_files(args.files, args.changed)
    if not files:
        print("没有待检文件：给几个路径，或加 --changed", file=sys.stderr)
        return 2

    total_errors = total_warnings = 0
    for path in files:
        errors, warnings = lint_file(path, args.target)
        total_errors += errors
        total_warnings += warnings

    print(
        f"\n{total_errors} error(s), {total_warnings} warning(s) in {len(files)} file(s)；target={args.target}"
    )
    if total_errors or (args.strict and total_warnings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
