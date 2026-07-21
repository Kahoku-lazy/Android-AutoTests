# MCP & Skill 独立管理 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 每个智能体独立管理 MCP JSON 配置和 Skill 文件夹上传，以卡片形式展示，支持连通性测试。

**Architecture:** 后端新增 6 个 Tool CRUD 端点（list/save_mcp/test_mcp/upload_skill/delete/toggle），前端 AgentDetail.vue Step 4 用卡片区替换旧表单。MCP 纯 JSON 编辑，Skill 通过 webkitdirectory 多文件上传。编辑模式即时 API 持久化，新建模式暂存表单。

**Tech Stack:** Django ORM + Vue 3 + Element Plus + webkitdirectory API

## Global Constraints

- API 响应统一 `{ok, data}` 或 `{ok, error}`
- JSON 字段 snake_case，前端变量 camelCase
- 所有写操作通过 `@csrf_exempt` + `@require_auth` 装饰器
- Tool 归属通过 `check_agent_owner` 验证
- Skill 文件防路径穿越（过滤 `..` `/` `\`），总大小限制 50MB
- 单文件行数上限：.py 400 行，.vue 500 行

---

### Task 1: 后端 — list_agent_tools + toggle_tool + delete_tool 端点

**Files:**
- Modify: `apps/ai_assistant/views/tool_views.py`

**Interfaces:**
- Produces: `list_agent_tools(request, agent_id) → JsonResponse`, `toggle_tool(request, agent_id, tool_id) → JsonResponse`, `delete_tool(request, agent_id, tool_id) → JsonResponse`

- [ ] **Step 1: 在 tool_views.py 末尾添加 list_agent_tools 视图**

```python
# 追加到 tool_views.py 末尾（保留已有 list_available_platform_tools）

import shutil
import subprocess
from pathlib import Path

from django.views.decorators.csrf import csrf_exempt

from ..decorators import require_auth
from ..models import AIAgent, AITool
from ..permissions import check_agent_owner


def list_agent_tools(request, agent_id):
    """GET /api/ai/agents/{id}/tools — 列出 Agent 的所有 MCP 和 Skill。"""
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
        if t.tool_type == "skill":
            try:
                cfg = json.loads(t.config_json)
                item["config"] = cfg
            except (json.JSONDecodeError, TypeError):
                item["config"] = {}
            skill_list.append(item)
        else:
            try:
                item["config"] = json.loads(t.config_json)
            except (json.JSONDecodeError, TypeError):
                item["config"] = {}
            mcp_list.append(item)

    return JsonResponse({"ok": True, "data": {"mcp": mcp_list, "skills": skill_list}})
```

- [ ] **Step 2: 添加 toggle_tool 视图**

```python
@csrf_exempt
@require_auth
def toggle_tool(request, agent_id, tool_id):
    """POST /api/ai/agents/{id}/tools/{tool_id}/toggle — 启用/禁用 Tool。"""
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
```

- [ ] **Step 3: 添加 delete_tool 视图（Skill 需清理文件）**

```python
@csrf_exempt
@require_auth
def delete_tool(request, agent_id, tool_id):
    """DELETE /api/ai/agents/{id}/tools/{tool_id} — 删除 MCP 或 Skill。"""
    if not check_agent_owner(request.user_id, agent_id):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    try:
        tool = AITool.objects.get(id=tool_id, agent_id=agent_id)
    except AITool.DoesNotExist:
        return JsonResponse({"ok": False, "error": "tool not found"}, status=404)

    # Skill 需清理文件目录
    if tool.tool_type == "skill":
        try:
            cfg = json.loads(tool.config_json)
            dir_path = cfg.get("dir_path", "")
            if dir_path:
                skill_dir = Path(dir_path)
                if skill_dir.exists() and str(skill_dir).startswith(str(Path("data/skills"))):
                    shutil.rmtree(skill_dir)
        except Exception:
            pass

    tool.delete()
    return JsonResponse({"ok": True})
```

- [ ] **Step 4: 验证端点可访问**

```bash
curl -s http://localhost:8765/api/ai/agents/1/tools | python -m json.tool
# 期望: {"ok":true,"data":{"mcp":[],"skills":[]}} 或 403
```

---

### Task 2: 后端 — save_mcp 端点

**Files:**
- Modify: `apps/ai_assistant/views/tool_views.py` (追加)

**Interfaces:**
- Consumes: `AITool.objects` from models.py
- Produces: `save_mcp(request, agent_id) → JsonResponse`

- [ ] **Step 1: 添加 save_mcp 视图（新建或更新 MCP）**

```python
@csrf_exempt
@require_auth
def save_mcp(request, agent_id):
    """POST /api/ai/agents/{id}/tools/mcp/save — 添加或更新 MCP 服务器。

    Body: {"name": "github", "config_json": "{\"transport\":\"stdio\",...}"}
    若 name 已存在 → 更新；不存在 → 新建。
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

    # 校验 JSON 格式
    try:
        parsed = json.loads(config_json_str)
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({"ok": False, "error": "config_json 不是有效的 JSON"}, status=400)

    if not name:
        return JsonResponse({"ok": False, "error": "name 不能为空"}, status=400)

    # 查找是否已存在同名 MCP
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
```

- [ ] **Step 2: 用 curl 测试 save_mcp 端点**

```bash
curl -s -X POST http://localhost:8765/api/ai/agents/1/tools/mcp/save \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"name":"test-mcp","config_json":"{\"transport\":\"stdio\",\"command\":\"echo\",\"args\":[\"hello\"]}"}'
# 期望: {"ok":true,"id":...,"created":true}
```

---

### Task 3: 后端 — test_mcp 端点

**Files:**
- Modify: `apps/ai_assistant/views/tool_views.py` (追加)

**Interfaces:**
- Consumes: subprocess / httpx
- Produces: `test_mcp(request, agent_id) → JsonResponse`

- [ ] **Step 1: 添加 test_mcp 视图**

```python
@csrf_exempt
@require_auth
def test_mcp(request, agent_id):
    """POST /api/ai/agents/{id}/tools/mcp/test — 测试 MCP 连通性。

    Body: {"transport":"stdio","command":"npx","args":["-y","@mcp/server"],"url":""}
    返回 connected: true/false + detail 说明。
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
                env={**__import__("os").environ, **{k: v for k, v in (data.get("env") or {}).items()}},
            )
            # stdio MCP 通过 stdin/stdout 通信，这里只测试命令是否可执行
            # 成功标准：进程正常启动（不抛异常），忽略退出码（MCP 会等待 stdin）
            detail = f"进程已启动 (stdout: {(result.stdout or '').strip()[:100] or '无输出'})"
            if result.stderr and "error" in result.stderr.lower():
                detail = f"stderr: {result.stderr.strip()[:200]}"
                return JsonResponse({"ok": True, "connected": False, "detail": detail})
            return JsonResponse({"ok": True, "connected": True, "detail": detail})

        else:  # sse / streamable_http
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
```

- [ ] **Step 2: 测试 test_mcp 端点**

```bash
curl -s -X POST http://localhost:8765/api/ai/agents/1/tools/mcp/test \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"transport":"stdio","command":"echo","args":["hello"]}'
# 期望: {"ok":true,"connected":true,"detail":"进程已启动..."}
```

---

### Task 4: 后端 — upload_skill 端点

**Files:**
- Modify: `apps/ai_assistant/views/tool_views.py` (追加)

**Interfaces:**
- Consumes: `request.FILES` (multipart), `AIAgent.objects`, `AITool.objects`
- Produces: `upload_skill(request, agent_id) → JsonResponse`

- [ ] **Step 1: 添加功能自动检测辅助函数和 upload_skill 视图**

```python
SKILL_ALLOWED_EXTENSIONS = {
    '.py', '.sh', '.bash', '.js', '.ts', '.json', '.yaml', '.yml',
    '.md', '.markdown', '.txt', '.toml', '.cfg', '.ini', '.env',
}
MAX_SKILL_TOTAL_SIZE = 50 * 1024 * 1024  # 50MB


def _detect_skill_features(dir_path: Path) -> str:
    """扫描 Skill 目录，返回功能描述字符串。"""
    ext_counts = {}
    cli_entries = 0
    total_files = 0
    for fpath in dir_path.rglob("*"):
        if fpath.is_file() and fpath.suffix.lower() in SKILL_ALLOWED_EXTENSIONS:
            total_files += 1
            ext = fpath.suffix.lower().lstrip('.')
            ext_counts[ext] = ext_counts.get(ext, 0) + 1
            # 检测 CLI 入口：shebang 或 Python __main__
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
    """POST /api/ai/agents/{id}/tools/skill/upload — 上传 Skill 文件夹。

    Content-Type: multipart/form-data
    字段:
      - files: 多个文件（webkitdirectory 上传）
      - name: skill 名称（文件夹名）

    后端:
      1. 存入 data/skills/{agent_id}/{name}/
      2. 自动检测 features
      3. 写入 _manifest.json
      4. 创建 AITool 记录
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

    # 防路径穿越：skill_name 不能含危险字符
    if any(c in skill_name for c in ("..", "/", "\\")):
        return JsonResponse({"ok": False, "error": "skill name 包含非法字符"}, status=400)

    # 检查总大小
    total_size = sum(f.size for f in uploaded_files)
    if total_size > MAX_SKILL_TOTAL_SIZE:
        return JsonResponse({
            "ok": False,
            "error": f"文件总大小 {total_size} 超过限制 {MAX_SKILL_TOTAL_SIZE}",
        }, status=400)

    # 创建目录
    skill_dir = Path(f"data/skills/{agent_id}/{skill_name}")
    skill_dir.mkdir(parents=True, exist_ok=True)

    file_count = 0
    try:
        for uploaded_file in uploaded_files:
            # 过滤危险路径
            rel_path = uploaded_file.name.replace("\\", "/")
            if ".." in rel_path or rel_path.startswith("/"):
                continue
            # 只存储文件名（展平目录结构）
            safe_name = Path(rel_path).name
            if not safe_name or safe_name.startswith("."):
                continue
            ext = Path(safe_name).suffix.lower()
            if ext not in SKILL_ALLOWED_EXTENSIONS:
                continue
            dest = skill_dir / safe_name
            with open(dest, "wb") as f:
                for chunk in uploaded_file.chunks():
                    f.write(chunk)
            file_count += 1
    except Exception as e:
        # 清理失败的目录
        shutil.rmtree(skill_dir, ignore_errors=True)
        return JsonResponse({"ok": False, "error": f"文件写入失败: {e}"}, status=500)

    if file_count == 0:
        shutil.rmtree(skill_dir, ignore_errors=True)
        return JsonResponse({"ok": False, "error": "没有有效的 Skill 文件"}, status=400)

    # 自动检测功能
    features = _detect_skill_features(skill_dir)

    # 写入 manifest
    manifest = {
        "name": skill_name,
        "file_count": file_count,
        "size_bytes": total_size,
        "features": features,
        "agent_id": agent_id,
        "created_at": str(__import__("datetime").datetime.now()),
    }
    manifest_path = skill_dir / "_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # 创建/更新 AITool 记录
    existing = AITool.objects.filter(agent=agent, name=skill_name, tool_type="skill").first()
    config_json = json.dumps({
        "dir_path": str(skill_dir.resolve()),
        "original_name": skill_name,
        "file_count": file_count,
        "size_bytes": total_size,
        "features": features,
        "uploaded_at": str(__import__("datetime").datetime.now()),
    }, ensure_ascii=False)
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
```

- [ ] **Step 2: 验证 data/skills 目录可创建**

```bash
mkdir -p data/skills && ls -la data/skills
```

---

### Task 5: 后端 — URL 路由注册 + views/__init__.py 导出

**Files:**
- Modify: `apps/ai_assistant/urls.py` (追加 6 行)
- Modify: `apps/ai_assistant/views/__init__.py` (追加 export)

- [ ] **Step 1: 在 urls.py 中注册新路由**

在 `urls.py` 现有的 `path('available-tools', ...)` 行后追加：

```python
    # MCP & Skill management (per-agent)
    path('agents/<int:agent_id>/tools', list_agent_tools, name='agent_tools_list'),
    path('agents/<int:agent_id>/tools/mcp/save', save_mcp, name='agent_mcp_save'),
    path('agents/<int:agent_id>/tools/mcp/test', test_mcp, name='agent_mcp_test'),
    path('agents/<int:agent_id>/tools/skill/upload', upload_skill, name='agent_skill_upload'),
    path('agents/<int:agent_id>/tools/<int:tool_id>/toggle', toggle_tool, name='agent_tool_toggle'),
    path('agents/<int:agent_id>/tools/<int:tool_id>/delete', delete_tool, name='agent_tool_delete'),
```

- [ ] **Step 2: 在 views/__init__.py 中添加导出**

在 `from .tool_views import list_available_platform_tools` 行改为：

```python
from .tool_views import (
    list_available_platform_tools,
    list_agent_tools,
    save_mcp,
    test_mcp,
    upload_skill,
    toggle_tool,
    delete_tool,
)
```

并在 `__all__` 列表中添加相应的导出名称。

- [ ] **Step 3: 确认路由可解析**

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8765/api/ai/agents/1/tools
# 期望: 403 (无 token) 或 200
```

---

### Task 6: 前端 — api.js 新增函数

**Files:**
- Modify: `frontend/src/modules/ai-assistant/api.js` (追加)

- [ ] **Step 1: 在 api.js 末尾追加 MCP/Skill API 函数**

```javascript
// ── MCP & Skill management ──

/** Fetch an agent's MCP servers and skills. */
export async function fetchAgentTools(agentId) {
  const { data } = await djangoClient.get(`/ai/agents/${agentId}/tools`)
  return data
}

/** Save (create or update) an MCP server config. */
export async function saveMcp(agentId, name, configJson) {
  const { data } = await djangoClient.post(`/ai/agents/${agentId}/tools/mcp/save`, {
    name,
    config_json: configJson,
  })
  return data
}

/** Test MCP server connectivity. Returns {ok, connected, detail}. */
export async function testMcp(agentId, configJson) {
  const { data } = await djangoClient.post(`/ai/agents/${agentId}/tools/mcp/test`,
    typeof configJson === 'string' ? JSON.parse(configJson) : configJson
  )
  return data
}

/** Upload a skill folder. files: File[], name: string */
export async function uploadSkill(agentId, files, name) {
  const formData = new FormData()
  formData.append('name', name)
  for (const file of files) {
    formData.append('files', file)
  }
  const { data } = await djangoClient.post(`/ai/agents/${agentId}/tools/skill/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

/** Toggle a tool enabled/disabled. */
export async function toggleTool(agentId, toolId, enabled) {
  const { data } = await djangoClient.post(`/ai/agents/${agentId}/tools/${toolId}/toggle`, { enabled })
  return data
}

/** Delete an MCP or Skill tool. */
export async function deleteTool(agentId, toolId) {
  const { data } = await djangoClient.delete(`/ai/agents/${agentId}/tools/${toolId}/delete`)
  return data
}
```

- [ ] **Step 2: 确认 djangoClient 支持 delete 方法**

检查 `frontend/src/shared/api-client.js` 中 `djangoClient` 是否有 `.delete()` 方法。若没有，用 `.post()` 代替（Django 视图用 `@csrf_exempt`，方法可以是 POST）。

---

### Task 7: 前端 — AgentDetail.vue 重构 MCP 卡片区

**Files:**
- Modify: `frontend/src/modules/ai-assistant/AgentDetail.vue`

**Scope:** 替换 Step 4 中「MCP 服务器」表单区域（原 `addTool/removeTool` 模式）为卡片 + Modal JSON 编辑模式。

- [ ] **Step 1: 在 script setup 顶部追加 import**

在现有 `import { fetchDefaultPrompt, fetchPlatformTools, fetchAvailableSkills, fetchKnowledgeDocuments } from './api.js'` 行替换为：

```javascript
import { fetchDefaultPrompt, fetchPlatformTools, fetchAvailableSkills, fetchKnowledgeDocuments, fetchAgentTools, saveMcp, testMcp, uploadSkill, toggleTool, deleteTool } from './api.js'
```

- [ ] **Step 2: 添加 MCP 相关的响应式状态**

在 `const loadingDocs = ref(false)` 后追加：

```javascript
// MCP management (edit mode uses API directly)
const mcpTools = ref([])      // loaded from API in edit mode
const mcpDialogVisible = ref(false)
const mcpDialogMode = ref('add')  // 'add' | 'edit'
const mcpEditingIndex = ref(-1)
const mcpForm = ref({ name: '', config_json: '{\n  "transport": "stdio",\n  "command": "",\n  "args": []\n}' })
const mcpJsonError = ref('')
const mcpTestingId = ref(null)
const mcpTestResults = ref({})  // { name: { connected: bool, detail: str } }

// Skill management
const skills = ref([])         // loaded from API in edit mode
const skillUploading = ref(false)
const skillUploadProgress = ref(0)
```

- [ ] **Step 3: 添加加载和操作函数**

在 `loadKnowledgeDocs()` 函数后追加：

```javascript
// ── MCP functions ──
async function loadAgentTools() {
  if (isNew.value) return
  try {
    const data = await fetchAgentTools(agentId)
    if (data.ok) {
      mcpTools.value = data.data?.mcp || []
      skills.value = data.data?.skills || []
    }
  } catch (_) {}
}

function openMcpDialog(mode = 'add', index = -1) {
  mcpDialogMode.value = mode
  mcpEditingIndex.value = index
  mcpJsonError.value = ''
  if (mode === 'edit' && index >= 0) {
    const t = mcpTools.value[index]
    mcpForm.value = {
      name: t.name,
      config_json: typeof t.config_json === 'string' ? t.config_json : JSON.stringify(t.config || {}, null, 2),
    }
  } else {
    mcpForm.value = { name: '', config_json: '{\n  "transport": "stdio",\n  "command": "",\n  "args": []\n}' }
  }
  mcpDialogVisible.value = true
}

async function saveMcpTool() {
  if (!mcpForm.value.name.trim()) { ElMessage.warning('请输入 MCP 名称'); return }
  try {
    JSON.parse(mcpForm.value.config_json)
  } catch {
    mcpJsonError.value = 'JSON 格式无效'
    return
  }
  mcpJsonError.value = ''

  if (isNew.value) {
    // Create mode: stash in form.tools (bundled with agent creation)
    if (mcpDialogMode.value === 'add') {
      form.value.tools.push({
        name: mcpForm.value.name.trim(),
        tool_type: 'mcp',
        enabled: true,
        config_json: mcpForm.value.config_json,
      })
    } else if (mcpEditingIndex.value >= 0) {
      form.value.tools[mcpEditingIndex.value] = {
        ...form.value.tools[mcpEditingIndex.value],
        name: mcpForm.value.name.trim(),
        config_json: mcpForm.value.config_json,
      }
    }
  } else {
    // Edit mode: immediate API persistence
    const data = await saveMcp(agentId, mcpForm.value.name.trim(), mcpForm.value.config_json)
    if (data.ok) {
      await loadAgentTools()
    } else {
      ElMessage.error(data.error || '保存失败')
      return
    }
  }
  mcpDialogVisible.value = false
}

function removeMcpLocal(index) {
  form.value.tools.splice(index, 1)
}

async function removeMcpApi(index) {
  const tool = mcpTools.value[index]
  if (!tool) return
  try { await ElMessageBox.confirm(`确定删除 MCP「${tool.name}」？`, '确认删除', { type: 'warning' }) } catch { return }
  const data = await deleteTool(agentId, tool.id)
  if (data.ok) {
    mcpTools.value.splice(index, 1)
    ElMessage.success('已删除')
  } else {
    ElMessage.error(data.error || '删除失败')
  }
}

async function testMcpConnection(index) {
  const tool = isNew.value ? form.value.tools[index] : mcpTools.value[index]
  if (!tool) return
  let configStr = tool.config_json || '{}'
  // In create mode, tool is the form object (already parsed)
  if (isNew.value && typeof configStr !== 'string') {
    configStr = JSON.stringify(configStr)
  }
  const name = tool.name || ''
  mcpTestingId.value = name
  try {
    const data = await testMcp(agentId, configStr)
    mcpTestResults.value[name] = { connected: data.connected, detail: data.detail }
    if (data.connected) {
      ElMessage.success(`MCP「${name}」连通成功`)
    } else {
      ElMessage.warning(`MCP「${name}」连通失败: ${data.detail}`)
    }
  } catch {
    mcpTestResults.value[name] = { connected: false, detail: '请求失败' }
    ElMessage.error('连通性测试请求失败')
  }
  mcpTestingId.value = null
}

async function toggleMcpEnabled(index) {
  if (isNew.value) {
    form.value.tools[index].enabled = !form.value.tools[index].enabled
    return
  }
  const tool = mcpTools.value[index]
  const newEnabled = !tool.enabled
  const data = await toggleTool(agentId, tool.id, newEnabled)
  if (data.ok) {
    mcpTools.value[index].enabled = newEnabled
  }
}
```

- [ ] **Step 4: 在 onMounted 中调用 loadAgentTools**

在 `onMounted` 中 `loadKnowledgeDocs()` 调用后追加：

```javascript
  await loadAgentTools()
```

- [ ] **Step 5: 更新 save() 函数中的 tools 处理逻辑**

将 `save()` 函数中：
```javascript
  const platformToolRecords = [...selectedPlatformTools.value].map(name => ({
    name, tool_type: 'platform', enabled: true, config_json: '{}',
  }))
  const allTools = [...form.value.tools.map(t => ({...})), ...platformToolRecords]
```
改为（新建模式保留 tools，编辑模式不发送 tools — 因为已通过 API 管理）：

```javascript
  // In create mode, include MCP tools in payload. In edit mode, tools are managed via API.
  let allTools = []
  if (isNew.value) {
    const platformToolRecords = [...selectedPlatformTools.value].map(name => ({
      name,
      tool_type: 'platform',
      enabled: true,
      config_json: '{}',
    }))
    allTools = [...form.value.tools.map(t => ({
      name: t.name || '',
      tool_type: t.tool_type || 'mcp',
      enabled: t.enabled !== false,
      config_json: t.config_json || '{}',
    })), ...platformToolRecords]
  }
  // In edit mode, omit tools from payload — they're already managed via dedicated API
  const payload = { ...form.value, tools: allTools }
```

- [ ] **Step 6: 替换模板中 MCP 服务器区域**

将原有 `<el-divider>MCP 服务器</el-divider>` 到对应 `</el-divider>` 之间的内容（约第537-595行）替换为：

```html
        <el-divider>MCP 服务器 ({{ isNew ? form.tools.filter(t => t.tool_type === 'mcp').length : mcpTools.length }})</el-divider>
        <button class="add-tool-btn" @click="openMcpDialog('add')">
          <IconPlus :size="16" />
          <span>添加 MCP 服务器</span>
        </button>

        <!-- Edit mode: MCP cards loaded from API -->
        <template v-if="!isNew">
          <div v-for="(t, i) in mcpTools" :key="t.id" class="mcp-card">
            <div class="mcp-card-head">
              <span class="mcp-card-name">📡 {{ t.name }}</span>
              <span class="mcp-card-transport">{{ t.config?.transport || 'stdio' }}</span>
              <span v-if="mcpTestResults[t.name]" class="mcp-card-status"
                    :class="mcpTestResults[t.name].connected ? 'connected' : 'failed'">
                {{ mcpTestResults[t.name].connected ? '✅ 已连通' : '❌ 未连通' }}
              </span>
              <el-switch v-model="t.enabled" size="small" @change="toggleMcpEnabled(i)" />
            </div>
            <div class="mcp-card-body">
              <code>{{ t.config?.command || t.config?.url || '(空命令)' }}</code>
            </div>
            <div class="mcp-card-actions">
              <el-button size="small" :loading="mcpTestingId === t.name"
                         @click="testMcpConnection(i)">🔍 测试连通</el-button>
              <el-button size="small" @click="openMcpDialog('edit', i)">编辑</el-button>
              <el-button size="small" type="danger" plain @click="removeMcpApi(i)">删除</el-button>
            </div>
          </div>
        </template>

        <!-- Create mode: MCP cards stashed in form.tools -->
        <template v-if="isNew">
          <div v-for="(t, i) in form.tools.filter(t => t.tool_type === 'mcp')" :key="i" class="mcp-card">
            <div class="mcp-card-head">
              <span class="mcp-card-name">📡 {{ t.name || '(未命名)' }}</span>
              <span v-if="mcpTestResults[t.name]" class="mcp-card-status"
                    :class="mcpTestResults[t.name].connected ? 'connected' : 'failed'">
                {{ mcpTestResults[t.name].connected ? '✅ 已连通' : '❌ 未连通' }}
              </span>
              <el-switch v-model="t.enabled" size="small" />
            </div>
            <div class="mcp-card-body">
              <code>{{ (typeof t.config_json === 'string' ? JSON.parse(t.config_json) : t.config_json)?.command || '(空命令)' }}</code>
            </div>
            <div class="mcp-card-actions">
              <el-button size="small" :loading="mcpTestingId === t.name"
                         @click="testMcpConnection(i)">🔍 测试连通</el-button>
              <el-button size="small" @click="openMcpDialog('edit', i)">编辑</el-button>
              <el-button size="small" type="danger" plain @click="removeMcpLocal(i)">删除</el-button>
            </div>
          </div>
        </template>

        <div v-if="(isNew ? form.tools.filter(t => t.tool_type === 'mcp').length : mcpTools.length) === 0"
             class="tool-empty">暂未添加 MCP 服务器，点击上方按钮添加</div>

        <!-- MCP JSON editor dialog -->
        <el-dialog v-model="mcpDialogVisible"
                   :title="mcpDialogMode === 'add' ? '添加 MCP 服务器' : '编辑 MCP 服务器'"
                   width="560px" destroy-on-close>
          <el-form label-width="80px">
            <el-form-item label="名称" required>
              <el-input v-model="mcpForm.name" placeholder="如: github" />
            </el-form-item>
            <el-form-item label="JSON 配置" required>
              <el-input v-model="mcpForm.config_json" type="textarea" :rows="12"
                        placeholder='{"transport":"stdio","command":"npx",...}'
                        style="font-family: var(--font-mono, monospace); font-size: 13px;" />
              <div v-if="mcpJsonError" style="color:#e85f5f;font-size:12px;margin-top:4px">{{ mcpJsonError }}</div>
            </el-form-item>
          </el-form>
          <template #footer>
            <el-button @click="mcpDialogVisible = false">取消</el-button>
            <el-button type="primary" @click="saveMcpTool">保存</el-button>
          </template>
        </el-dialog>
```

- [ ] **Step 7: 移除不再需要的旧函数**

从 `<script setup>` 中删除以下函数（它们被新逻辑替代）：
- `parseToolFromApi`
- `addTool`
- `removeTool`
- `addKV`
- `removeKV`
- `toConfigJSON`
- `syncToolConfig`

保留 `onProviderChange` 等非 MCP 相关函数不变。

---

### Task 8: 前端 — AgentDetail.vue Skill 卡片区

**Files:**
- Modify: `frontend/src/modules/ai-assistant/AgentDetail.vue` (追加模板和函数)

- [ ] **Step 1: 添加 Skill 相关函数**

在 `toggleMcpEnabled()` 函数后追加：

```javascript
// ── Skill functions ──
const skillFolderInput = ref(null)

function triggerSkillUpload() {
  skillFolderInput.value?.click()
}

async function handleSkillFolderChange(e) {
  const files = e.target.files
  if (!files || !files.length) return

  // Extract folder name from first file's webkitRelativePath
  const firstPath = files[0].webkitRelativePath || files[0].name
  const folderName = firstPath.split('/')[0] || 'skill'

  skillUploading.value = true
  skillUploadProgress.value = 0

  try {
    const data = await uploadSkill(agentId, [...files], folderName)
    if (data.ok) {
      skills.value.push(data.data)
      ElMessage.success(`Skill「${folderName}」上传成功 (${data.data.config?.file_count || 0} 个文件)`)
    } else {
      ElMessage.error(data.error || '上传失败')
    }
  } catch (err) {
    ElMessage.error('上传失败: ' + (err.message || '未知错误'))
  }
  skillUploading.value = false
  skillUploadProgress.value = 0
  // Reset input so same folder can be re-uploaded
  e.target.value = ''
}

async function removeSkill(index) {
  const skill = skills.value[index]
  if (!skill) return
  try { await ElMessageBox.confirm(`确定删除 Skill「${skill.name}」？相关文件将被清除。`, '确认删除', { type: 'warning' }) } catch { return }
  const data = await deleteTool(agentId, skill.id)
  if (data.ok) {
    skills.value.splice(index, 1)
    ElMessage.success('Skill 已删除')
  } else {
    ElMessage.error(data.error || '删除失败')
  }
}

function formatSkillSize(bytes) {
  if (!bytes) return '0 B'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}
```

- [ ] **Step 2: 在模板中 MCP 区域后添加 Skill 卡片区**

在 MCP JSON editor dialog 的 `</el-dialog>` 之后、`</div>`（step-panel 结束标签）之前插入：

```html

        <el-divider>Skills ({{ skills.length }})</el-divider>

        <template v-if="!isNew">
          <button class="add-tool-btn add-skill-btn" @click="triggerSkillUpload" :disabled="skillUploading">
            <IconPlus :size="16" />
            <span>{{ skillUploading ? '上传中...' : '上传 Skill 文件夹' }}</span>
          </button>
          <input ref="skillFolderInput" type="file" webkitdirectory multiple
                 style="display:none" @change="handleSkillFolderChange" />

          <div v-if="skillUploading" style="padding:12px 0">
            <el-progress :percentage="skillUploadProgress" :indeterminate="true" />
          </div>

          <div v-for="(s, i) in skills" :key="s.id" class="skill-card">
            <div class="skill-card-head">
              <span class="skill-card-name">📦 {{ s.name }}</span>
              <span class="skill-card-count">{{ s.config?.file_count || 0 }} 个文件</span>
            </div>
            <div class="skill-card-body">
              <div class="skill-card-features">{{ s.config?.features || '无功能描述' }}</div>
              <div class="skill-card-meta">
                <span>{{ formatSkillSize(s.config?.size_bytes) }}</span>
                <span>·</span>
                <span>{{ s.config?.uploaded_at || s.created_at }}</span>
              </div>
            </div>
            <div class="skill-card-actions">
              <el-button size="small" type="danger" plain @click="removeSkill(i)">删除</el-button>
            </div>
          </div>

          <div v-if="!skills.length && !skillUploading" class="tool-empty">
            暂未上传 Skill，点击上方按钮选择文件夹上传
          </div>
        </template>

        <div v-else class="tool-empty">
          💡 Skills 管理在创建智能体后可用。请先保存智能体，再进入编辑模式上传 Skill。
        </div>
```

- [ ] **Step 3: 追加 MCP 和 Skill 卡片样式**

在 `<style scoped>` 末尾（`</style>` 之前）追加：

```css
/* ── MCP card ── */
.mcp-card {
  background: #faf9f4;
  border: 1.5px solid #e8e2d6;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  transition: border-color 0.2s ease;
}
.mcp-card:hover { border-color: #19c8b9; }

.mcp-card-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.mcp-card-name {
  font-size: 15px;
  font-weight: 700;
  color: #4a3a28;
}

.mcp-card-transport {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 6px;
  background: #e6f9f6;
  color: #158a80;
  font-weight: 600;
}

.mcp-card-status {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 6px;
  font-weight: 600;
}
.mcp-card-status.connected { background: #e8f5e0; color: #4a8233; }
.mcp-card-status.failed { background: #fde8e8; color: #c0392b; }

.mcp-card-body code {
  display: block;
  font-size: 13px;
  color: #6b5c44;
  background: #fff;
  padding: 6px 10px;
  border-radius: 6px;
  border: 1px solid #f0ebe0;
  margin-bottom: 10px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mcp-card-actions {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

/* ── Skill card ── */
.add-skill-btn {
  border-color: #b39ef3;
  color: #7c6ab2;
}
.add-skill-btn:hover {
  border-color: #b39ef3;
  background: #f5f2ff;
  color: #5c4a9e;
}

.skill-card {
  background: #faf9fb;
  border: 1.5px solid #e6e0f0;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  transition: border-color 0.2s ease;
}
.skill-card:hover { border-color: #b39ef3; }

.skill-card-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.skill-card-name {
  font-size: 15px;
  font-weight: 700;
  color: #4a3a28;
}

.skill-card-count {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 6px;
  background: #f5f2ff;
  color: #5c4a9e;
  font-weight: 600;
}

.skill-card-body {
  margin-bottom: 10px;
}

.skill-card-features {
  font-size: 13px;
  color: #6b5c44;
  line-height: 1.5;
}

.skill-card-meta {
  display: flex;
  gap: 6px;
  font-size: 11px;
  color: #a0936e;
  margin-top: 4px;
  align-items: center;
}

.skill-card-actions {
  display: flex;
  gap: 6px;
}

/* Remove old tool-card hover style (replaced by .mcp-card) */
.tool-card { display: none; }
.tool-card-head { display: none; }
```

- [ ] **Step 4: 处理 create_agent/update_agent 的 tools 兼容**

确保 `create_agent` 视图中对 `tool_type: 'mcp'` 的工具直接使用 `config_json`（已是 JSON 字符串），不需要额外转换。当前代码已支持此模式，无需修改。

- [ ] **Step 5: 前端构建验证**

```bash
cd frontend && npx vite build --mode development 2>&1 | tail -10
# 期望: 无编译错误
```

---

### Task 9: 端到端验证

- [ ] **Step 1: 验证 MCP JSON 保存和列表**

```bash
# 1. 保存 MCP
curl -s -X POST http://localhost:8765/api/ai/agents/<id>/tools/mcp/save \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"name":"github","config_json":"{\"transport\":\"stdio\",\"command\":\"npx\",\"args\":[\"-y\",\"@mcp/server-github\"]}"}'

# 2. 列表
curl -s http://localhost:8765/api/ai/agents/<id>/tools | python -m json.tool
# 期望: data.mcp 中包含 github

# 3. 测试连通
curl -s -X POST http://localhost:8765/api/ai/agents/<id>/tools/mcp/test \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"transport":"stdio","command":"echo","args":["test"]}'
# 期望: {"ok":true,"connected":true,...}
```

- [ ] **Step 2: 验证 Skill 上传**

```bash
# 创建测试文件
mkdir -p /tmp/test-skill
echo '#!/bin/bash\necho "hello"' > /tmp/test-skill/run.sh
echo '{"name":"test"}' > /tmp/test-skill/config.json

# 上传（用 curl multipart）
curl -s -X POST http://localhost:8765/api/ai/agents/<id>/tools/skill/upload \
  -H "Authorization: Bearer <token>" \
  -F "name=test-skill" \
  -F "files=@/tmp/test-skill/run.sh" \
  -F "files=@/tmp/test-skill/config.json"
# 期望: {"ok":true,"data":{"name":"test-skill","tool_type":"skill",...}}

# 验证文件已保存
ls -la data/skills/<id>/test-skill/
cat data/skills/<id>/test-skill/_manifest.json
```

- [ ] **Step 3: 验证删除 Skill 清理文件**

```bash
curl -s -X DELETE http://localhost:8765/api/ai/agents/<id>/tools/<tool_id>/delete \
  -H "Authorization: Bearer <token>"
# 期望: {"ok":true}

# 确认目录已删除
ls data/skills/<id>/test-skill/ 2>&1
# 期望: No such file or directory
```

- [ ] **Step 4: 验证 Agent A 不能访问 Agent B 的工具**

```bash
curl -s http://localhost:8765/api/ai/agents/<id_b>/tools \
  -H "Authorization: Bearer <token_for_user_who_owns_a>"
# 期望: {"ok":false,"error":"Forbidden"} 403
```
