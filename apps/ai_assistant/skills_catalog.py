"""engines/ai/skills 目录扫描（只读文件系统 + 读库启停）。

写库仍走 api.py。运行时按「磁盘有 SKILL.md 且库中未停用」决定加载哪些目录。
"""

from __future__ import annotations

import json
import logging
import os
import re

import frontmatter

from django.conf import settings

from apps.ai_assistant.models import AISharedTool

logger = logging.getLogger("ai_assistant")

SHARED_SKILLS_DIR = os.path.join(str(settings.BASE_DIR), "engines", "ai", "skills")


def _parse_skill_md(path: str) -> tuple[str, str]:
    """读 SKILL.md frontmatter，返回 (name, description)；失败则用空串。"""
    try:
        parsed = frontmatter.load(path)
    except Exception:
        logger.exception("SKILL.md 解析失败: %s", path)
        return "", ""
    name = str(parsed.get("name") or "").strip()
    desc = str(parsed.get("description") or "").strip()
    return name, desc


def scan_skill_folders() -> list[dict]:
    """扫描 engines/ai/skills 下含 SKILL.md 的一级目录。"""
    results: list[dict] = []
    if not os.path.isdir(SHARED_SKILLS_DIR):
        return results
    for entry in sorted(os.listdir(SHARED_SKILLS_DIR)):
        if ".." in entry or "/" in entry or "\\" in entry:
            continue
        folder = os.path.join(SHARED_SKILLS_DIR, entry)
        skill_md = os.path.join(folder, "SKILL.md")
        if not os.path.isdir(folder) or not os.path.isfile(skill_md):
            continue
        _name, description = _parse_skill_md(skill_md)
        file_count = 0
        size_bytes = 0
        for root, _dirs, files in os.walk(folder):
            for fname in files:
                fpath = os.path.join(root, fname)
                file_count += 1
                try:
                    size_bytes += os.path.getsize(fpath)
                except OSError:
                    pass
        results.append(
            {
                "folder": entry,
                "description": description,
                "file_count": file_count,
                "size_bytes": size_bytes,
            }
        )
    return results


def skill_origin(item: AISharedTool) -> str:
    """uploaded = 工具箱上传；local = 仓库/磁盘已有。"""
    try:
        cfg = json.loads(item.config_json or "{}")
    except json.JSONDecodeError:
        cfg = {}
    origin = cfg.get("origin")
    if origin in ("local", "uploaded"):
        return origin
    if cfg.get("file_count"):
        return "uploaded"
    return "local"


def list_enabled_skill_dirs() -> list[str]:
    """总闸打开后交给引擎的 skill 目录（磁盘存在且未在库中停用）。"""
    disabled = set(
        AISharedTool.objects.filter(item_type="skill", enabled=False).values_list("name", flat=True)
    )
    dirs: list[str] = []
    for folder in scan_skill_folders():
        name = folder["folder"]
        if name in disabled:
            continue
        dirs.append(os.path.join(SHARED_SKILLS_DIR, name))
    return dirs


class SkillFsError(ValueError):
    """Skill 目录/文件不可读（名称非法、不存在或越界）。"""


_SKILL_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_SKIP_DIR_NAMES = {".git", "__pycache__", "node_modules", ".ruff_cache"}
_SKIP_FILE_NAMES = {".env", ".DS_Store"}
_TEXT_EXTS = {
    ".md",
    ".markdown",
    ".py",
    ".sh",
    ".bash",
    ".js",
    ".ts",
    ".json",
    ".yaml",
    ".yml",
    ".txt",
    ".toml",
    ".cfg",
    ".ini",
    ".html",
    ".css",
    ".xml",
}
_MAX_PREVIEW_BYTES = 512 * 1024


def _is_within(root: str, target: str) -> bool:
    """target 必须落在 root 目录内。"""
    try:
        root_r = os.path.realpath(root)
        target_r = os.path.realpath(target)
        return os.path.commonpath([root_r, target_r]) == root_r
    except ValueError:
        return False


def resolve_skill_root(name: str) -> str:
    """校验 skill 文件夹名并返回绝对路径。"""
    if not _SKILL_NAME_RE.match(name or ""):
        raise SkillFsError("invalid name")
    root = os.path.join(SHARED_SKILLS_DIR, name)
    if not os.path.isdir(root) or not _is_within(SHARED_SKILLS_DIR, root):
        raise SkillFsError("not found")
    return os.path.realpath(root)


def resolve_skill_file(name: str, rel: str) -> str:
    """校验相对路径并返回绝对文件路径。"""
    root = resolve_skill_root(name)
    rel_norm = (rel or "").replace("\\", "/").strip().lstrip("/")
    if not rel_norm or ".." in rel_norm.split("/"):
        raise SkillFsError("invalid path")
    target = os.path.join(root, *rel_norm.split("/"))
    if not os.path.isfile(target) or not _is_within(root, target):
        raise SkillFsError("not found")
    return os.path.realpath(target)


def build_skill_tree(name: str) -> list[dict]:
    """返回 skill 目录树（不含敏感/缓存目录）。"""
    root = resolve_skill_root(name)
    return _walk_tree(root, root)


def _walk_tree(root: str, current: str) -> list[dict]:
    nodes: list[dict] = []
    try:
        entries = sorted(os.listdir(current), key=str.lower)
    except OSError:
        return nodes
    for entry in entries:
        if entry in _SKIP_DIR_NAMES or entry in _SKIP_FILE_NAMES:
            continue
        full = os.path.join(current, entry)
        rel = os.path.relpath(full, root).replace("\\", "/")
        if os.path.isdir(full):
            nodes.append(
                {
                    "name": entry,
                    "path": rel,
                    "is_dir": True,
                    "children": _walk_tree(root, full),
                }
            )
        elif os.path.isfile(full):
            nodes.append({"name": entry, "path": rel, "is_dir": False, "children": []})
    return nodes


def read_skill_file(name: str, rel: str) -> dict:
    """读 skill 内文本文件；非文本或过大不返回正文。"""
    full = resolve_skill_file(name, rel)
    basename = os.path.basename(full)
    if basename in _SKIP_FILE_NAMES:
        raise SkillFsError("not found")
    ext = os.path.splitext(basename)[1].lower()
    rel_norm = os.path.relpath(full, resolve_skill_root(name)).replace("\\", "/")
    if ext not in _TEXT_EXTS:
        return {"path": rel_norm, "name": basename, "kind": "unsupported", "content": ""}
    try:
        size = os.path.getsize(full)
    except OSError as exc:
        logger.exception("读取 skill 文件失败")
        raise SkillFsError("not found") from exc
    if size > _MAX_PREVIEW_BYTES:
        return {"path": rel_norm, "name": basename, "kind": "too_large", "content": ""}
    try:
        with open(full, encoding="utf-8", errors="replace") as handle:
            content = handle.read()
    except OSError as exc:
        logger.exception("读取 skill 文件失败")
        raise SkillFsError("not found") from exc
    kind = "markdown" if ext in {".md", ".markdown"} else "text"
    return {"path": rel_norm, "name": basename, "kind": kind, "content": content}
