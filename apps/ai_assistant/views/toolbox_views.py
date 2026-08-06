"""AI Toolbox — shared skills, tools, and extensions reusable across agents."""

import json
import os

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from ..decorators import require_auth
from ..models import AISharedTool, AITool

# Shared skill uploads land in data/shared_skills/{tool_id}/
_SHARED_SKILLS_DIR = os.path.join("data", "shared_skills")
_SHARED_SKILL_MAX_MB = 50
_SKILL_EXTENSIONS = {
    ".py",
    ".sh",
    ".bash",
    ".js",
    ".ts",
    ".json",
    ".yaml",
    ".yml",
    ".md",
    ".markdown",
    ".txt",
    ".toml",
    ".cfg",
    ".ini",
    ".env",
}


def _detect_skill_features(file_names: list[str]) -> str:
    """Return a human-readable summary of file types in a skill folder."""
    exts: dict[str, int] = {}
    has_cli = False
    for name in file_names:
        _, ext = os.path.splitext(name)
        if ext:
            ext = ext.lower()
            exts[ext] = exts.get(ext, 0) + 1
        if ext in (".sh", ".bash", ".py") or name in ("run", "start", "main"):
            has_cli = True
    parts = []
    for ext in sorted(exts):
        label = ext.lstrip(".").upper()
        parts.append(f"{label}: {exts[ext]}")
    if has_cli:
        parts.insert(0, "1 CLI tool")
    return ", ".join(parts) if parts else "Unknown"


def list_shared_tools(request):
    """GET /api/ai/toolbox — List all shared toolbox items."""
    items = AISharedTool.objects.filter(enabled=True).order_by("-updated_at")
    return JsonResponse(
        {
            "status": True,
            "items": [
                {
                    "id": item.id,
                    "name": item.name,
                    "item_type": item.item_type,
                    "description": item.description,
                    "config_json": item.config_json,
                    "created_at": str(item.created_at),
                }
                for item in items
            ],
        }
    )


@csrf_exempt
@require_auth
def create_shared_tool(request):
    """POST /api/ai/toolbox/create — Add a shared MCP tool or extension."""
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"status": False, "message": "无效的 JSON"}, status=400)

    name = (body.get("name") or "").strip()
    if not name:
        return JsonResponse({"status": False, "message": "name is required"}, status=400)

    item_type = (body.get("item_type") or "").strip()
    if item_type not in ("mcp", "extension"):
        return JsonResponse(
            {"status": False, "message": "item_type must be 'mcp' or 'extension'"}, status=400
        )

    config_json = body.get("config_json", "{}")
    if isinstance(config_json, dict):
        config_json = json.dumps(config_json)

    item = AISharedTool.objects.create(
        name=name,
        item_type=item_type,
        description=body.get("description", ""),
        config_json=config_json,
    )
    return JsonResponse({"status": True, "id": item.id})


@csrf_exempt
@require_auth
def update_shared_tool(request, item_id):
    """POST /api/ai/toolbox/{id}/update — Update a shared toolbox item."""
    try:
        item = AISharedTool.objects.get(id=item_id)
    except AISharedTool.DoesNotExist:
        return JsonResponse({"status": False, "message": "not found"}, status=404)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"status": False, "message": "无效的 JSON"}, status=400)

    if "name" in body:
        item.name = body["name"].strip()
    if "description" in body:
        item.description = body["description"]
    if "config_json" in body:
        cfg = body["config_json"]
        item.config_json = json.dumps(cfg) if isinstance(cfg, dict) else cfg

    item.save(update_fields=[f for f in ("name", "description", "config_json") if f in body])
    return JsonResponse({"status": True})


@csrf_exempt
@require_auth
def delete_shared_tool(request, item_id):
    """POST /api/ai/toolbox/{id}/delete — Delete a shared toolbox item."""
    try:
        item = AISharedTool.objects.get(id=item_id)
    except AISharedTool.DoesNotExist:
        return JsonResponse({"status": False, "message": "not found"}, status=404)

    # If it's a skill type, also remove the uploaded files
    if item.item_type == "skill":
        import shutil

        skill_dir = os.path.join(_SHARED_SKILLS_DIR, str(item.id))
        if os.path.isdir(skill_dir):
            shutil.rmtree(skill_dir, ignore_errors=True)

    item.delete()
    return JsonResponse({"status": True})


@csrf_exempt
@require_auth
def upload_shared_skill(request):
    """POST /api/ai/toolbox/upload-skill — Upload a shared skill folder."""
    files = request.FILES.getlist("files")
    skill_name = (request.POST.get("name") or "").strip()
    if not files:
        return JsonResponse({"status": False, "message": "no files uploaded"}, status=400)
    if not skill_name:
        return JsonResponse({"status": False, "message": "name is required"}, status=400)

    # Validate files
    total_size = 0
    file_names = []
    for f in files:
        if ".." in f.name or f.name.startswith("/"):
            return JsonResponse({"status": False, "message": f"非法文件名: {f.name}"}, status=400)
        _, ext = os.path.splitext(f.name)
        if ext.lower() not in _SKILL_EXTENSIONS:
            return JsonResponse(
                {"status": False, "message": f"不支持的文件类型: {ext or '无后缀'}"}, status=400
            )
        total_size += f.size
        file_names.append(f.name)

    size_mb = total_size / (1024 * 1024)
    if size_mb > _SHARED_SKILL_MAX_MB:
        return JsonResponse(
            {
                "status": False,
                "message": f"总大小 {size_mb:.1f}MB 超过 {_SHARED_SKILL_MAX_MB}MB 限制",
            },
            status=400,
        )

    # Create DB record first (so we have an ID for the directory)
    features = _detect_skill_features(file_names)
    item = AISharedTool.objects.create(
        name=skill_name,
        item_type="skill",
        description=f"{len(files)} 个文件 — {features}",
        config_json=json.dumps(
            {
                "file_count": len(files),
                "size_bytes": total_size,
                "features": features,
            }
        ),
    )

    # Save files to data/shared_skills/{id}/
    skill_dir = os.path.join(_SHARED_SKILLS_DIR, str(item.id))
    os.makedirs(skill_dir, exist_ok=True)
    for f in files:
        dest = os.path.join(skill_dir, f.name)
        # Ensure subdirectories exist
        os.makedirs(os.path.dirname(dest) or skill_dir, exist_ok=True)
        with open(dest, "wb") as dst:
            for chunk in f.chunks():
                dst.write(chunk)

    return JsonResponse({"status": True, "id": item.id})


@csrf_exempt
@require_auth
def import_from_toolbox(request, agent_id):
    """POST /api/ai/agents/{id}/tools/import-from-toolbox — Import a shared
    toolbox item into an agent, creating a per-agent AITool copy."""
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"status": False, "message": "无效的 JSON"}, status=400)

    toolbox_item_id = body.get("toolbox_item_id")
    if not toolbox_item_id:
        return JsonResponse({"status": False, "message": "toolbox_item_id is required"}, status=400)

    try:
        shared = AISharedTool.objects.get(id=toolbox_item_id, enabled=True)
    except AISharedTool.DoesNotExist:
        return JsonResponse({"status": False, "message": "toolbox item not found"}, status=404)

    # Check for duplicate import by name
    exists = AITool.objects.filter(
        agent_id=agent_id,
        name=shared.name,
        tool_type=shared.item_type,
    ).exists()
    if exists:
        return JsonResponse(
            {"status": False, "message": f"'{shared.name}' 已存在于当前智能体"}, status=409
        )

    # For skill type, copy files to agent's skill directory
    config = shared.config_json
    if shared.item_type == "skill":
        import shutil

        src_dir = os.path.join(_SHARED_SKILLS_DIR, str(shared.id))
        dst_dir = os.path.join("data", "skills", str(agent_id), shared.name)
        if os.path.isdir(src_dir) and not os.path.isdir(dst_dir):
            shutil.copytree(src_dir, dst_dir)
            cfg = json.loads(config) if isinstance(config, str) else config
            cfg["dir_path"] = dst_dir
            config = json.dumps(cfg)

    tool = AITool.objects.create(
        agent_id=agent_id,
        name=shared.name,
        tool_type=shared.item_type,
        config_json=config,
        enabled=True,
    )
    return JsonResponse({"status": True, "id": tool.id})
