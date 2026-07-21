# Task 1: list_agent_tools + toggle_tool + delete_tool 端点

> 文件: `apps/ai_assistant/views/tool_views.py`

## 要求

在现有 `tool_views.py` 文件末尾追加 3 个视图函数（保留已有 `list_available_platform_tools`）。

### 1. list_agent_tools(request, agent_id)
- GET 端点，返回 Agent 的所有 MCP 和 Skill，分为两组
- 验证 `check_agent_owner(request.user_id, agent_id)` → 否则 403
- Agent 不存在 → 404
- 返回格式: `{"ok": true, "data": {"mcp": [...], "skills": [...]}}`
- 每个 item: `{id, name, tool_type, config_json, enabled, created_at}`
- config_json 额外解析到 `config` 字段（方便前端），解析失败给 `{}`

### 2. toggle_tool(request, agent_id, tool_id)
- POST，启用/禁用工具
- 需要 `@csrf_exempt` + `@require_auth`
- 验证 agent owner + tool 存在（agent_id 匹配）
- Body: `{"enabled": true/false}`
- 返回: `{"ok": true, "enabled": <new_value>}`

### 3. delete_tool(request, agent_id, tool_id)
- DELETE，删除工具
- 需要 `@csrf_exempt` + `@require_auth`
- Skill 类型：清理 `data/skills/` 下对应目录（从 config_json.dir_path 读取）
  - 安全检查：dir_path 必须以 `data/skills` 开头
- 返回: `{"ok": true}`

## 需要添加的 imports

```python
import json
import shutil
from pathlib import Path
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from ..decorators import require_auth
from ..models import AIAgent, AITool
from ..permissions import check_agent_owner
```

(如果文件已有这些 import，跳过重复的)

## 全局约束
- API 响应统一 `{ok, data}` 或 `{ok, error}`
- JSON 字段 snake_case
- 所有写操作通过 `@csrf_exempt` + `@require_auth`
- Tool 归属通过 `check_agent_owner` 验证

## 上下文
- 项目是 Django REST API，AgentScope 驱动的 AI 测试平台
- AITool 模型: `agent(FK→AIAgent), name, tool_type(mcp|skill|platform), config_json, enabled, created_at`
- 已有 tool_views.py 包含 `list_available_platform_tools`（参考代码风格）
- check_agent_owner 在 `apps/ai_assistant/permissions.py`
