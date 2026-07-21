"""Platform tool listing endpoint — exposes the tool registry to the frontend."""
import json
import shutil
import subprocess
from pathlib import Path

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from ..decorators import require_auth
from ..models import AIAgent, AITool
from ..permissions import check_agent_owner


def list_available_platform_tools(request):
    """GET /api/ai/available-tools — return all available platform business tools.

    Returns tool names + descriptions so the frontend can render a
    checkbox-based tool selection UI per agent.
    """
    from agentscope_service.tools.factory import _TOOL_REGISTRY

    tools = [
        {
            "name": cls.name,
            "description": (cls.description or "").strip(),
        }
        for cls in _TOOL_REGISTRY
    ]
    return JsonResponse({"ok": True, "tools": tools})


def list_agent_tools(request, agent_id):
    """GET /api/ai/agents/{id}/tools — list all MCP and Skill tools for an agent."""
    if not check_agent_owner(request.user_id, agent_id):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    try:
        agent = AIAgent.objects.get(id=agent_id)
    except AIAgent.DoesNotExist:
        return JsonResponse({"ok": False, "error": "agent not found"}, status=404)

    tools_qs = AITool.objects.filter(agent=agent)
    mcp_list = []
    skill_list = []
    for t in tools_qs:
        item = {
            "id": t.id,
            "name": t.name,
            "tool_type": t.tool_type,
            "config_json": t.config_json,
            "enabled": t.enabled,
            "created_at": str(t.created_at),
        }
        try:
            item["config"] = json.loads(t.config_json)
        except (json.JSONDecodeError, TypeError):
            item["config"] = {}

        if t.tool_type == "skill":
            skill_list.append(item)
        else:
            mcp_list.append(item)

    return JsonResponse({"ok": True, "data": {"mcp": mcp_list, "skills": skill_list}})


@csrf_exempt
@require_auth
def toggle_tool(request, agent_id, tool_id):
    """POST /api/ai/agents/{id}/tools/{tool_id}/toggle — enable or disable a tool."""
    if not check_agent_owner(request.user_id, agent_id):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    try:
        tool = AITool.objects.get(id=tool_id, agent_id=agent_id)
    except AITool.DoesNotExist:
        return JsonResponse({"ok": False, "error": "tool not found"}, status=404)

    data = json.loads(request.body)
    tool.enabled = data.get("enabled", True)
    tool.save(update_fields=["enabled"])
    return JsonResponse({"ok": True, "enabled": tool.enabled})


@csrf_exempt
@require_auth
def delete_tool(request, agent_id, tool_id):
    """DELETE /api/ai/agents/{id}/tools/{tool_id} — delete MCP or Skill tool.

    Skill tools also have their file directories cleaned up.
    """
    if not check_agent_owner(request.user_id, agent_id):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    try:
        tool = AITool.objects.get(id=tool_id, agent_id=agent_id)
    except AITool.DoesNotExist:
        return JsonResponse({"ok": False, "error": "tool not found"}, status=404)

    if tool.tool_type == "skill":
        try:
            cfg = json.loads(tool.config_json)
            dir_path = cfg.get("dir_path", "")
            if dir_path:
                skill_dir = Path(dir_path)
                skills_root = Path("data/skills").resolve()
                if skill_dir.exists() and str(skill_dir.resolve()).startswith(str(skills_root)):
                    shutil.rmtree(skill_dir)
        except Exception:
            pass

    tool.delete()
    return JsonResponse({"ok": True})


@csrf_exempt
@require_auth
def save_mcp(request, agent_id):
    """POST /api/ai/agents/{id}/tools/mcp/save — add or update an MCP server.

    Body: {"name": "github", "config_json": "{\"transport\":\"stdio\",...}"}
    If name already exists → update; otherwise → create.
    """
    if not check_agent_owner(request.user_id, agent_id):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    try:
        agent = AIAgent.objects.get(id=agent_id)
    except AIAgent.DoesNotExist:
        return JsonResponse({"ok": False, "error": "agent not found"}, status=404)

    data = json.loads(request.body)
    name = (data.get("name") or "").strip()
    config_json_str = data.get("config_json", "{}")

    try:
        json.loads(config_json_str)
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({"ok": False, "error": "config_json 不是有效的 JSON"}, status=400)

    if not name:
        return JsonResponse({"ok": False, "error": "name 不能为空"}, status=400)

    existing = AITool.objects.filter(agent=agent, name=name, tool_type="mcp").first()
    if existing:
        existing.config_json = config_json_str
        existing.save(update_fields=["config_json"])
        return JsonResponse({"ok": True, "id": existing.id, "created": False})

    tool = AITool.objects.create(
        agent=agent,
        name=name,
        tool_type="mcp",
        config_json=config_json_str,
        enabled=True,
    )
    return JsonResponse({"ok": True, "id": tool.id, "created": True})


@csrf_exempt
@require_auth
def test_mcp(request, agent_id):
    """POST /api/ai/agents/{id}/tools/mcp/test — test MCP server connectivity.

    Body matches the JSON config: {"transport":"stdio","command":"npx","args":["-y","..."],"url":"",...}
    Returns {ok, connected, detail}.
    """
    if not check_agent_owner(request.user_id, agent_id):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)

    data = json.loads(request.body)
    transport = data.get("transport", "stdio")

    try:
        if transport == "stdio":
            cmd = [data.get("command", "")]
            args = data.get("args", [])
            if isinstance(args, str):
                args = args.split()
            cmd.extend(args)
            cmd = [c for c in cmd if c]
            if not cmd:
                return JsonResponse({"ok": True, "connected": False, "detail": "命令为空"})

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=15,
                cwd=data.get("cwd") or None,
            )
            detail = f"进程已启动 (stdout: {(result.stdout or '').strip()[:100] or '无输出'})"
            if result.stderr and "error" in result.stderr.lower():
                detail = f"stderr: {result.stderr.strip()[:200]}"
                return JsonResponse({"ok": True, "connected": False, "detail": detail})
            return JsonResponse({"ok": True, "connected": True, "detail": detail})

        else:
            url = data.get("url", "")
            if not url:
                return JsonResponse({"ok": True, "connected": False, "detail": "URL 为空"})
            try:
                import httpx
                resp = httpx.get(url, timeout=10, follow_redirects=True)
                if 200 <= resp.status_code < 500:
                    return JsonResponse({"ok": True, "connected": True,
                        "detail": f"HTTP {resp.status_code}"})
                return JsonResponse({"ok": True, "connected": False,
                    "detail": f"HTTP {resp.status_code}"})
            except ImportError:
                import urllib.request
                try:
                    r = urllib.request.urlopen(url, timeout=10)
                    return JsonResponse({"ok": True, "connected": True,
                        "detail": f"HTTP {r.getcode()}"})
                except Exception as e:
                    return JsonResponse({"ok": True, "connected": False,
                        "detail": f"连接失败: {e}"})

    except subprocess.TimeoutExpired:
        return JsonResponse({"ok": True, "connected": False, "detail": "命令超时 (15s)"})
    except FileNotFoundError:
        return JsonResponse({"ok": True, "connected": False, "detail": f"命令未找到: {cmd[0] if cmd else '未知'}"})
    except Exception as e:
        return JsonResponse({"ok": True, "connected": False, "detail": str(e)[:200]})


# ── Skill upload ──

SKILL_ALLOWED_EXTENSIONS = {
    '.py', '.sh', '.bash', '.js', '.ts', '.json', '.yaml', '.yml',
    '.md', '.markdown', '.txt', '.toml', '.cfg', '.ini', '.env',
}
MAX_SKILL_TOTAL_SIZE = 50 * 1024 * 1024  # 50MB


def _detect_skill_features(dir_path):
    """Scan a skill directory and return a features summary string."""
    ext_counts = {}
    cli_entries = 0
    total_files = 0
    for fpath in dir_path.rglob("*"):
        if fpath.is_file() and fpath.suffix.lower() in SKILL_ALLOWED_EXTENSIONS:
            total_files += 1
            ext = fpath.suffix.lower().lstrip('.')
            ext_counts[ext] = ext_counts.get(ext, 0) + 1
            try:
                first_line = fpath.read_text(encoding="utf-8", errors="replace")[:100]
                if first_line.startswith("#!") or 'if __name__' in first_line:
                    cli_entries += 1
            except Exception:
                pass

    parts = []
    if ext_counts:
        for ext in sorted(ext_counts.keys()):
            count = ext_counts[ext]
            parts.append(f"{ext.capitalize()}: {count}")
    if cli_entries:
        parts.append(f"{cli_entries} CLI tool{'s' if cli_entries > 1 else ''}")
    return ", ".join(parts) if parts else f"{total_files} files"


@csrf_exempt
@require_auth
def upload_skill(request, agent_id):
    """POST /api/ai/agents/{id}/tools/skill/upload — upload a skill folder.

    multipart/form-data:
      - files: multiple files (webkitdirectory upload)
      - name: skill folder name

    Saves to data/skills/{agent_id}/{name}/, auto-detects features,
    writes _manifest.json, creates/updates AITool record.
    """
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "POST required"}, status=405)

    if not check_agent_owner(request.user_id, agent_id):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)

    try:
        agent = AIAgent.objects.get(id=agent_id)
    except AIAgent.DoesNotExist:
        return JsonResponse({"ok": False, "error": "agent not found"}, status=404)

    skill_name = (request.POST.get("name") or "").strip()
    uploaded_files = request.FILES.getlist("files")

    if not skill_name:
        return JsonResponse({"ok": False, "error": "skill name 不能为空"}, status=400)
    if not uploaded_files:
        return JsonResponse({"ok": False, "error": "未上传任何文件"}, status=400)

    if any(c in skill_name for c in ("..", "/", "\\")):
        return JsonResponse({"ok": False, "error": "skill name 包含非法字符"}, status=400)

    total_size = sum(f.size for f in uploaded_files)
    if total_size > MAX_SKILL_TOTAL_SIZE:
        return JsonResponse({
            "ok": False,
            "error": f"文件总大小 {total_size} 超过限制 {MAX_SKILL_TOTAL_SIZE}",
        }, status=400)

    skill_dir = Path(f"data/skills/{agent_id}/{skill_name}")
    skill_dir.mkdir(parents=True, exist_ok=True)

    file_count = 0
    try:
        for uploaded_file in uploaded_files:
            rel_path = uploaded_file.name.replace("\\", "/")
            if ".." in rel_path or rel_path.startswith("/"):
                continue
            safe_name = Path(rel_path).name
            if not safe_name or safe_name.startswith("."):
                continue
            ext = safe_name.suffix.lower()
            if ext not in SKILL_ALLOWED_EXTENSIONS:
                continue
            dest = skill_dir / safe_name
            with open(dest, "wb") as f:
                for chunk in uploaded_file.chunks():
                    f.write(chunk)
            file_count += 1
    except Exception as e:
        shutil.rmtree(skill_dir, ignore_errors=True)
        return JsonResponse({"ok": False, "error": f"文件写入失败: {e}"}, status=500)

    if file_count == 0:
        shutil.rmtree(skill_dir, ignore_errors=True)
        return JsonResponse({"ok": False, "error": "没有有效的 Skill 文件"}, status=400)

    features = _detect_skill_features(skill_dir)

    from datetime import datetime
    manifest = {
        "name": skill_name,
        "file_count": file_count,
        "size_bytes": total_size,
        "features": features,
        "agent_id": agent_id,
        "created_at": str(datetime.now()),
    }
    (skill_dir / "_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    config_json = json.dumps({
        "dir_path": str(skill_dir.resolve()),
        "original_name": skill_name,
        "file_count": file_count,
        "size_bytes": total_size,
        "features": features,
        "uploaded_at": str(datetime.now()),
    }, ensure_ascii=False)

    existing = AITool.objects.filter(agent=agent, name=skill_name, tool_type="skill").first()
    if existing:
        existing.config_json = config_json
        existing.enabled = True
        existing.save()
        tool = existing
    else:
        tool = AITool.objects.create(
            agent=agent,
            name=skill_name,
            tool_type="skill",
            config_json=config_json,
            enabled=True,
        )

    return JsonResponse({
        "ok": True,
        "data": {
            "id": tool.id,
            "name": tool.name,
            "tool_type": "skill",
            "config_json": config_json,
            "config": json.loads(config_json),
            "enabled": tool.enabled,
            "created_at": str(tool.created_at),
        },
    })
