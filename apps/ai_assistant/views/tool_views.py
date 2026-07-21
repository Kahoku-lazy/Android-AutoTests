"""Platform tool listing endpoint — exposes the tool registry to the frontend."""
import json
import shutil
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
