"""Locator project list / tree — system-locked android|web|api."""

from __future__ import annotations

from typing import Any

from .models import (
    SYSTEM_PROJECTS,
    ApiEndpoint,
    LocatorProject,
    Page,
    WebElement,
)

__all__ = [
    "ConflictError",
    "ensure_system_projects",
    "get_project",
    "get_project_by_code",
    "get_project_tree",
    "list_projects",
    "serialize_project",
]


class ConflictError(Exception):
    """Business conflict (illegal move, duplicate name, etc.)."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def ensure_system_projects() -> list[LocatorProject]:
    """Ensure the three locked projects exist; return them in stable order."""
    projects: list[LocatorProject] = []
    for code, name in SYSTEM_PROJECTS:
        obj, created = LocatorProject.objects.get_or_create(
            code=code,
            defaults={"name": name, "description": ""},
        )
        if not created and obj.name != name:
            obj.name = name
            obj.save(update_fields=["name", "updated_at"])
        projects.append(obj)
    return projects


def serialize_project(obj: LocatorProject) -> dict[str, Any]:
    if obj.code == "android":
        file_count = Page.objects.filter(is_folder=False).count()
    elif obj.code == "web":
        file_count = WebElement.objects.count()
    else:
        file_count = ApiEndpoint.objects.count()
    return {
        "id": obj.id,
        "code": obj.code,
        "name": obj.name,
        "description": obj.description,
        "file_count": file_count,
        "created_at": obj.created_at.isoformat() if obj.created_at else "",
        "updated_at": obj.updated_at.isoformat() if obj.updated_at else "",
        "locked": True,
    }


def list_projects() -> list[dict[str, Any]]:
    return [serialize_project(p) for p in ensure_system_projects()]


def get_project_by_code(*, code: str) -> LocatorProject | None:
    ensure_system_projects()
    return LocatorProject.objects.filter(code=code).first()


def get_project(*, project_id: int) -> LocatorProject | None:
    ensure_system_projects()
    return LocatorProject.objects.filter(id=project_id).first()


def _serialize_file_node(*, kind: str, file_id: int, name: str, sort_order: int = 0) -> dict[str, Any]:
    return {
        "type": "file",
        "kind": kind,
        "id": file_id,
        "name": name,
        "sort_order": sort_order,
    }


def _build_dir_node(directory, children_map, files_by_dir) -> dict[str, Any]:
    child_dirs = children_map.get(directory.id, [])
    return {
        "type": "directory",
        "id": directory.id,
        "name": directory.name,
        "sort_order": directory.sort_order,
        "children": [
            *[_build_dir_node(c, children_map, files_by_dir) for c in child_dirs],
            *[f for f in files_by_dir.get(directory.id, [])],
        ],
    }


def get_project_tree(*, code: str) -> dict[str, Any]:
    project = get_project_by_code(code=code)
    if project is None:
        raise LookupError("项目不存在")

    directories = list(project.directories.all().order_by("sort_order", "id"))
    children_map: dict[int | None, list] = {}
    for d in directories:
        children_map.setdefault(d.parent_id, []).append(d)

    files_by_dir: dict[int | None, list] = {}
    if project.code == "android":
        pages = Page.objects.filter(is_folder=False).order_by("id")
        # Prefer directory FK; unmigrated pages fall back to root
        for page in pages:
            dir_id = page.directory_id
            files_by_dir.setdefault(dir_id, []).append(
                _serialize_file_node(
                    kind="page",
                    file_id=page.id,
                    name=page.label or f"页面 #{page.id}",
                )
            )
    elif project.code == "web":
        for el in WebElement.objects.all().order_by("id"):
            files_by_dir.setdefault(el.directory_id, []).append(
                _serialize_file_node(kind="web_element", file_id=el.id, name=el.name or f"元素 #{el.id}")
            )
    else:
        for ep in ApiEndpoint.objects.all().order_by("id"):
            files_by_dir.setdefault(ep.directory_id, []).append(
                _serialize_file_node(
                    kind="api_endpoint",
                    file_id=ep.id,
                    name=ep.name or f"{ep.method} #{ep.id}",
                )
            )

    # Only include root files that belong to this project's directories or null
    dir_ids = {d.id for d in directories}
    root_files = [
        f
        for f in files_by_dir.get(None, [])
        if True
    ]
    # Files hanging on directories of other projects should not appear — directory FK is project-scoped
    scoped_files_by_dir: dict[int | None, list] = {None: root_files}
    for dir_id, items in files_by_dir.items():
        if dir_id is None:
            continue
        if dir_id in dir_ids:
            scoped_files_by_dir[dir_id] = items

    root_dirs = children_map.get(None, [])
    return {
        "project": serialize_project(project),
        "tree": [
            *[_build_dir_node(d, children_map, scoped_files_by_dir) for d in root_dirs],
            *scoped_files_by_dir.get(None, []),
        ],
    }
