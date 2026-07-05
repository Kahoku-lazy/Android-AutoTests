"""ai-assistant API — Agent CRUD + Chat + Auth + Task management."""
import json, base64, os, uuid
from pathlib import Path
from datetime import datetime
from django.http import JsonResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.contrib.auth import authenticate
from .models import AIAgent, AITool, AIConversation, AIMessage, AITask, AIExecutionLog
from .api import encrypt_key, decrypt_key, mask_key
from shared.auth.jwt_auth import create_token_pair, verify_token, create_access_token, blacklist_token

AVATAR_DIR = settings.BASE_DIR / 'data' / 'avatars'


# ═══════════════════════════════════════════════
# Auth endpoints
# ═══════════════════════════════════════════════

@csrf_exempt
def login(request):
    """POST /api/ai/auth/login — authenticate and return JWT token pair."""
    data = json.loads(request.body)
    username = data.get('username', '')
    password = data.get('password', '')
    user = authenticate(username=username, password=password)
    if user is None:
        return JsonResponse({'ok': False, 'error': 'Invalid credentials'}, status=401)
    tokens = create_token_pair(str(user.id))
    return JsonResponse({
        'ok': True,
        **tokens,
        'user': {'id': user.id, 'username': user.username},
    })


@csrf_exempt
def register(request):
    """POST /api/ai/auth/register — create a new user."""
    from django.contrib.auth.models import User
    data = json.loads(request.body)
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    if not username or not password:
        return JsonResponse({'ok': False, 'error': 'username and password required'}, status=400)
    if User.objects.filter(username=username).exists():
        return JsonResponse({'ok': False, 'error': 'username already exists'}, status=409)
    user = User.objects.create_user(username=username, password=password)
    tokens = create_token_pair(str(user.id))
    return JsonResponse({
        'ok': True,
        **tokens,
        'user': {'id': user.id, 'username': user.username},
    })


@csrf_exempt
def refresh_token(request):
    """POST /api/ai/auth/refresh — refresh access token using refresh token."""
    data = json.loads(request.body)
    token = data.get('refresh_token', '')
    try:
        payload = verify_token(token)
        if payload.get('type') != 'refresh':
            return JsonResponse({'ok': False, 'error': 'Not a refresh token'}, status=401)
        new_access = create_access_token(payload['sub'])
        return JsonResponse({'ok': True, 'access_token': new_access, 'token_type': 'bearer'})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=401)


@csrf_exempt
def logout(request):
    """POST /api/ai/auth/logout — blacklist the current token."""
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if auth_header.startswith('Bearer '):
        blacklist_token(auth_header[7:])
    return JsonResponse({'ok': True})


def me(request):
    """GET /api/ai/auth/me — return current user info from JWT."""
    user_id = getattr(request, 'user_id', None)
    if not user_id:
        return JsonResponse({'ok': False, 'error': 'Not authenticated'}, status=401)
    from django.contrib.auth.models import User
    try:
        user = User.objects.get(id=user_id)
        return JsonResponse({'ok': True, 'user': {'id': user.id, 'username': user.username}})
    except User.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'User not found'}, status=404)



def list_agents(request):
    agents = []
    for a in AIAgent.objects.all().prefetch_related('tools'):
        # 从 prefetched 内存数据计数，避免 N+1 查询
        tool_count = sum(1 for t in a.tools.all() if t.enabled)
        agents.append({
            "id": a.id, "name": a.name, "avatar": a.avatar, "tags": a.tags,
            "description": a.description, "model_provider": a.model_provider,
            "model_name": a.model_name, "status": a.status,
            "tool_count": tool_count,
            "created_at": str(a.created_at),
        })
    return JsonResponse({"ok": True, "agents": agents})


def agent_detail(request, agent_id):
    try: a = AIAgent.objects.prefetch_related('tools').get(id=agent_id)
    except AIAgent.DoesNotExist: return JsonResponse({"ok": False, "error": "not found"}, status=404)
    tools = [{"id": t.id, "name": t.name, "tool_type": t.tool_type,
              "config_json": t.config_json, "enabled": t.enabled} for t in a.tools.all()]
    return JsonResponse({"ok": True, "agent": {
        "id": a.id, "name": a.name, "avatar": a.avatar, "tags": a.tags,
        "description": a.description, "model_provider": a.model_provider,
        "model_name": a.model_name,
        "api_key": mask_key(decrypt_key(a.api_key) if a.api_key else ''),
        "base_url": a.base_url,
        "system_prompt": a.system_prompt, "temperature": a.temperature,
        "max_tokens": a.max_tokens, "formatter": a.formatter,
        "max_iters": a.max_iters, "parallel_tool_calls": a.parallel_tool_calls,
        "print_hint_msg": a.print_hint_msg, "memory_mode": a.memory_mode,
        "long_term_memory_mode": a.long_term_memory_mode,
        "enable_meta_tool": a.enable_meta_tool,
        "enable_rewrite_query": a.enable_rewrite_query,
        "generate_kwargs": a.generate_kwargs,
        "compression_enabled": a.compression_enabled,
        "compression_threshold": a.compression_threshold,
        "compression_keep_recent": a.compression_keep_recent,
        "compression_prompt": a.compression_prompt,
        "compression_template": a.compression_template,
        "tts_enabled": a.tts_enabled, "status": a.status,
        "tools": tools,
        "is_connected": a.is_connected,
        "last_checked_at": str(a.last_checked_at) if a.last_checked_at else None,
        "available_models": json.loads(a.available_models) if a.available_models else [],
        "created_at": str(a.created_at),
    }})


@csrf_exempt
def create_agent(request):
    data = json.loads(request.body)
    a = AIAgent.objects.create(
        name=data.get("name", ""), avatar=data.get("avatar", "🤖"),
        tags=data.get("tags", ""), description=data.get("description", ""),
        model_provider=data.get("model_provider", "dashscope"),
        model_name=data.get("model_name", "qwen-max"),
        api_key=encrypt_key(data.get("api_key", "")), base_url=data.get("base_url", ""),
        system_prompt=data.get("system_prompt", ""),
        temperature=data.get("temperature", 0.7),
        max_tokens=data.get("max_tokens", 4096),
        formatter=data.get("formatter", "dashscope"),
        max_iters=data.get("max_iters", 10),
        parallel_tool_calls=data.get("parallel_tool_calls", False),
        print_hint_msg=data.get("print_hint_msg", False),
        memory_mode=data.get("memory_mode", "inmemory"),
        long_term_memory_mode=data.get("long_term_memory_mode", "both"),
        enable_meta_tool=data.get("enable_meta_tool", False),
        enable_rewrite_query=data.get("enable_rewrite_query", True),
        generate_kwargs=data.get("generate_kwargs", "{}"),
        compression_enabled=data.get("compression_enabled", False),
        compression_threshold=data.get("compression_threshold", 10000),
        compression_keep_recent=data.get("compression_keep_recent", 3),
        compression_prompt=data.get("compression_prompt", ""),
        compression_template=data.get("compression_template", ""),
        tts_enabled=data.get("tts_enabled", False),
        key_revealed=False)
    for t in data.get("tools", []):
        AITool.objects.create(agent=a, name=t.get("name", ""),
            tool_type=t.get("tool_type", "mcp"),
            config_json=t.get("config_json", "{}"), enabled=t.get("enabled", True))
    return JsonResponse({"ok": True, "id": a.id})


@csrf_exempt
def update_agent(request, agent_id):
    try: a = AIAgent.objects.get(id=agent_id)
    except AIAgent.DoesNotExist: return JsonResponse({"ok": False, "error": "not found"}, status=404)
    data = json.loads(request.body)
    # api_key 加密后存储；带掩码的值表示未修改，跳过
    key_changed = False
    if 'api_key' in data and data['api_key']:
        if '***' in data['api_key']:
            del data['api_key']  # 未修改，保留原值
        else:
            data['api_key'] = encrypt_key(data['api_key'])
            key_changed = True
    for f in ['name','avatar','tags','description','model_provider','model_name',
              'api_key','base_url','system_prompt','temperature','max_tokens',
              'formatter','max_iters','parallel_tool_calls','print_hint_msg',
              'memory_mode','long_term_memory_mode','enable_meta_tool',
              'enable_rewrite_query','generate_kwargs',
              'compression_enabled','compression_threshold','compression_keep_recent',
              'compression_prompt','compression_template','tts_enabled','status']:
        if f in data: setattr(a, f, data[f])
    if key_changed:
        a.key_revealed = False  # Key 已更新，允许重新查看一次
    a.save()
    if 'tools' in data:
        a.tools.all().delete()
        for t in data['tools']:
            AITool.objects.create(agent=a, name=t.get("name",""),
                tool_type=t.get("tool_type","mcp"),
                config_json=t.get("config_json","{}"), enabled=t.get("enabled",True))
    return JsonResponse({"ok": True})


@csrf_exempt
def reveal_api_key(request, agent_id):
    """POST /api/ai/agents/<id>/reveal-key — 一次性返回解密后的 API Key。
    仅在创建/更新后首次调用返回明文，之后永久返回脱敏值。
    """
    try:
        a = AIAgent.objects.get(id=agent_id)
    except AIAgent.DoesNotExist:
        return JsonResponse({"ok": False, "error": "not found"}, status=404)

    if not a.api_key:
        return JsonResponse({"ok": False, "error": "未配置 API Key"}, status=400)

    if a.key_revealed:
        # 已查看过，只返回脱敏值
        decrypted = decrypt_key(a.api_key)
        return JsonResponse({
            "ok": True,
            "api_key": mask_key(decrypted),
            "revealed": False,
            "hint": "API Key 仅支持一次性查看，已过期"
        })

    # 首次查看 — 返回解密后的完整 Key，同时标记已查看
    decrypted = decrypt_key(a.api_key)
    a.key_revealed = True
    a.save(update_fields=['key_revealed', 'updated_at'])

    return JsonResponse({
        "ok": True,
        "api_key": decrypted,
        "revealed": True,
        "hint": "请立即复制保存，此 Key 仅显示一次"
    })


@csrf_exempt
def delete_agent(request, agent_id):
    AIAgent.objects.filter(id=agent_id).delete()
    return JsonResponse({"ok": True})


@csrf_exempt
def delete_conversation(request, conv_id):
    """DELETE /api/ai/conversations/{id}/delete — delete a conversation and its messages."""
    try:
        c = AIConversation.objects.get(id=conv_id)
    except AIConversation.DoesNotExist:
        return JsonResponse({"ok": False, "error": "not found"}, status=404)
    c.delete()
    return JsonResponse({"ok": True})


def list_conversations(request, agent_id):
    convs = AIConversation.objects.filter(agent_id=agent_id).order_by('-updated_at')
    return JsonResponse({"ok": True, "conversations": [
        {"id": c.id, "title": c.title, "status": c.status,
         "agent_scope_session_id": c.agent_scope_session_id or '',
         "created_at": str(c.created_at)} for c in convs]})


@csrf_exempt
def create_conversation(request, agent_id):
    data = json.loads(request.body)
    c = AIConversation.objects.create(agent_id=agent_id, title=data.get("title","新对话"))
    return JsonResponse({"ok": True, "id": c.id, "agent_scope_session_id": c.agent_scope_session_id or ''})


def list_messages(request, conv_id):
    msgs = AIMessage.objects.filter(conversation_id=conv_id)
    return JsonResponse({"ok": True, "messages": [
        {"id": m.id, "role": m.role, "content": m.content,
         "blocks": json.loads(m.blocks) if m.blocks else [],
         "reason": m.reason or 'normal',
         "tool_calls": m.tool_calls,
         "tokens": m.tokens,
         "input_tokens": m.input_tokens or 0,
         "model_name": m.model_name or '',
         "created_at": str(m.created_at)} for m in msgs]})


@csrf_exempt
def upload_avatar(request):
    """POST /api/ai/upload-avatar — Upload avatar image, return URL."""
    try:
        data = json.loads(request.body)
        img_b64 = data.get("image", "")
        if not img_b64:
            return JsonResponse({"ok": False, "error": "no image data"})
        # Decode base64 (strip data:image/... prefix if present)
        if ',' in img_b64:
            img_b64 = img_b64.split(',', 1)[1]
        img_bytes = base64.b64decode(img_b64)

        AVATAR_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        fname = f"avatar_{ts}.png"
        fpath = AVATAR_DIR / fname
        fpath.write_bytes(img_bytes)

        url = f"/api/ai/avatars/{fname}"
        return JsonResponse({"ok": True, "url": url})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)})


@csrf_exempt
def send_message(request, conv_id):
    """POST /api/ai/conversations/{id}/send — Send message + get agent response.

    Uses AgentScope to create a ReActAgent from DB config, runs it, and saves response.
    """
    try:
        conv = AIConversation.objects.select_related('agent').get(id=conv_id)
    except AIConversation.DoesNotExist:
        return JsonResponse({"ok": False, "error": "conversation not found"}, status=404)

    data = json.loads(request.body)
    user_text = data.get("message", "").strip()
    if not user_text:
        return JsonResponse({"ok": False, "error": "message required"})

    # Save user message
    AIMessage.objects.create(conversation=conv, role="user", content=user_text)

    # Build agent from config
    agent_cfg = conv.agent
    response_text = ""
    tokens = 0
    try:
        response_text, tokens = _run_agent(agent_cfg, user_text, conv)
        role = "assistant"
    except Exception as e:
        response_text = f"抱歉，智能体运行出错：{str(e)}"
        role = "assistant"

    # Save assistant message
    AIMessage.objects.create(conversation=conv, role=role, content=response_text, tokens=tokens)
    conv.title = user_text[:30] if conv.title == "新对话" else conv.title
    conv.save(update_fields=["title", "updated_at"])

    return JsonResponse({"ok": True, "message": {"role": role, "content": response_text, "tokens": tokens}})


def _run_agent(agent_cfg, user_text, conv) -> tuple:
    """Run AgentScope agent with the given config. Returns (response_text, tokens)."""
    provider = agent_cfg.model_provider
    model_name = agent_cfg.model_name
    api_key = decrypt_key(agent_cfg.api_key) if agent_cfg.api_key else ''
    base_url = agent_cfg.base_url
    system_prompt = agent_cfg.system_prompt
    temperature = agent_cfg.temperature

    if not api_key:
        return "请先配置 API Key", 0

    # Build messages with conversation history
    messages = [{"role": "system", "content": system_prompt or "你是一个有用的AI助手。"}]

    # Include recent conversation history (last 20 messages)
    history = AIMessage.objects.filter(conversation=conv).order_by('-created_at')[:20]
    for m in reversed(list(history)):
        if m.role in ('user', 'assistant'):
            messages.append({"role": m.role, "content": m.content})

    messages.append({"role": "user", "content": user_text})

    # Call LLM API based on provider
    try:
        import requests

        if provider == "dashscope":
            return _call_dashscope(messages, api_key, model_name, temperature)
        elif provider == "openai":
            return _call_openai(messages, api_key, model_name, base_url, temperature)
        else:
            return _call_openai(messages, api_key, model_name, base_url or "https://api.openai.com/v1", temperature)
    except Exception as e:
        return f"调用模型失败：{str(e)}", 0


def _call_dashscope(messages, api_key, model_name, temperature):
    """Call Alibaba DashScope (Qwen) API."""
    import requests
    resp = requests.post(
        "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": model_name, "messages": messages, "temperature": temperature},
        timeout=120,
    )
    if resp.status_code == 200:
        body = resp.json()
        choice = body["choices"][0]
        return choice["message"]["content"], body.get("usage", {}).get("total_tokens", 0)
    return f"API 错误 ({resp.status_code}): {resp.text[:200]}", 0


def _call_openai(messages, api_key, model_name, base_url, temperature):
    """Call OpenAI-compatible API."""
    import requests
    url = f"{base_url.rstrip('/')}/chat/completions"
    resp = requests.post(
        url,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": model_name, "messages": messages, "temperature": temperature},
        timeout=120,
    )
    if resp.status_code == 200:
        body = resp.json()
        choice = body["choices"][0]
        return choice["message"]["content"], body.get("usage", {}).get("total_tokens", 0)
    return f"API 错误 ({resp.status_code}): {resp.text[:200]}", 0


@csrf_exempt
def save_message(request, conv_id):
    """POST /api/ai/conversations/{id}/save-message — persist assistant message after SSE stream.

    Accepts the full ContentBlock structure so that thinking/tool_calls/hints are preserved
    across sessions (跨 Turn 上下文完整性).
    """
    data = json.loads(request.body)
    role = data.get('role', 'assistant')
    content = data.get('content', '')
    tokens = data.get('tokens', 0)
    blocks = data.get('blocks', [])
    reason = data.get('reason', 'normal')
    input_tokens = data.get('input_tokens', 0)
    model_name = data.get('model_name', '')
    msg = AIMessage.objects.create(
        conversation_id=conv_id,
        role=role,
        content=content,
        tokens=tokens,
        blocks=json.dumps(blocks) if isinstance(blocks, list) else (blocks or '[]'),
        reason=reason,
        input_tokens=input_tokens,
        model_name=model_name,
    )
    return JsonResponse({"ok": True, "id": msg.id})


@csrf_exempt
def send_confirm_result(request, conv_id):
    """POST /api/ai/conversations/{id}/confirm-result — send user confirmation back to AgentScope.

    Called when the LLM emits REQUIRE_USER_CONFIRM, the user makes a decision,
    and we relay that decision so the ReAct loop can resume.

    Body: {
        "reply_id": "xxx",          # AgentScope reply_id from the confirm event
        "confirm_results": [
            {"tool_call_id": "tc1", "approved": true},
            {"tool_call_id": "tc2", "approved": false, "reason": "设备已被占用"},
        ]
    }
    """
    try:
        conv = AIConversation.objects.get(id=conv_id)
    except AIConversation.DoesNotExist:
        return JsonResponse({"ok": False, "error": "conversation not found"}, status=404)

    if not conv.agent_scope_session_id:
        return JsonResponse({"ok": False, "error": "no AgentScope session"}, status=400)

    data = json.loads(request.body)
    reply_id = data.get('reply_id', '')
    confirm_results = data.get('confirm_results', [])

    token = _get_agentscope_token(request)

    # Forward to AgentScope SSE stream: sends a USER_CONFIRM_RESULT event
    # via the same /sessions/{session_id}/stream endpoint (but as a POST with confirm data)
    resp, err = _call_agentscope(
        f"/sessions/{conv.agent_scope_session_id}/confirm",
        'POST',
        {
            "reply_id": reply_id,
            "confirm_results": confirm_results,
        },
        token,
        timeout=10,
    )

    if err:
        return JsonResponse({"ok": False, "error": f"confirm result send failed: {err}"}, status=503)

    # Even if AgentScope doesn't have a dedicated confirm endpoint yet,
    # log the decision locally for audit
    try:
        AIExecutionLog.objects.create(
            agent=conv.agent,
            level='info',
            message=f"User confirm: {json.dumps(confirm_results, ensure_ascii=False)}",
            metadata=json.dumps({"reply_id": reply_id, "conv_id": conv_id}),
        )
    except Exception:
        pass  # non-critical

    return JsonResponse({"ok": True})


@csrf_exempt
def stream_chat(request, conv_id):
    """POST /api/ai/conversations/{id}/stream — SSE streaming chat via AgentScope.

    Returns an SSE stream of agent events. Stub — implemented in Phase 6.
    """
    return JsonResponse({"ok": False, "error": "streaming not yet available — use /send for now"}, status=501)


def serve_avatar(request, filename):
    """GET /api/ai/avatars/{filename} — Serve uploaded avatar images."""
    fpath = AVATAR_DIR / filename
    if fpath.exists():
        return FileResponse(open(str(fpath), 'rb'), content_type='image/png')
    return JsonResponse({"ok": False, "error": "not found"}, status=404)


# ── Task history ──────────────────────────────────────────────────────────────

def list_conv_tasks(request, conv_id):
    """GET /api/ai/conversations/{id}/tasks — list AI-created tasks for a conversation."""
    # Verify conversation exists
    try:
        conv = AIConversation.objects.get(id=conv_id)
    except AIConversation.DoesNotExist:
        return JsonResponse({"ok": False, "error": "conversation not found"}, status=404)

    # Get AI-created tasks (prefixed with ai-task-)
    try:
        from apps.test_runner.models import TestRunRecord
        tasks = TestRunRecord.objects.filter(
            run_id__startswith="ai-task-"
        ).order_by("-started_at")[:50]

        return JsonResponse({"ok": True, "tasks": [
            {
                "run_id": t.run_id,
                "status": t.status,
                "device_serial": t.device_serial,
                "device_model": "",
                "cases": t.selected_cases or [],
                "loop_count": t.loop_count or 1,
                "started_at": str(t.started_at) if t.started_at else None,
                "completed_at": str(t.completed_at) if getattr(t, 'completed_at', None) else None,
                "summary": t.summary or "",
            }
            for t in tasks
        ]})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)


def get_conv_task(request, conv_id, run_id):
    """GET /api/ai/conversations/{id}/tasks/{run_id} — get details of a specific task."""
    try:
        from apps.test_runner.models import TestRunRecord
        task = TestRunRecord.objects.filter(run_id=run_id).first()
        if not task:
            return JsonResponse({"ok": False, "error": "task not found"}, status=404)

        return JsonResponse({"ok": True, "task": {
            "run_id": task.run_id,
            "status": task.status,
            "device_serial": task.device_serial,
            "cases": task.selected_cases or [],
            "loop_count": task.loop_count or 1,
            "started_at": str(task.started_at) if task.started_at else None,
            "completed_at": str(task.completed_at) if getattr(task, 'completed_at', None) else None,
            "summary": task.summary or "",
        }})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)



# ═══════════════════════════════════════════════
#  File upload & parsing for AI chat
# ═══════════════════════════════════════════════

UPLOAD_DIR = settings.BASE_DIR / 'data' / 'uploads'
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {'txt', 'log', 'md', 'markdown', 'json', 'xml', 'csv', 'py', 'js', 'html', 'css', 'yaml', 'yml', 'docx', 'xlsx', 'pdf'}
MAX_UPLOAD_SIZE = 20 * 1024 * 1024  # 20MB


def _parse_docx(filepath: str) -> str:
    try:
        from docx import Document
        doc = Document(filepath)
        return '\n'.join(p.text for p in doc.paragraphs if p.text.strip())
    except Exception as e:
        return f"[DOCX parse error: {e}]"


def _parse_xlsx(filepath: str) -> str:
    try:
        import openpyxl
        wb = openpyxl.load_workbook(filepath, data_only=True)
        parts = []
        for name in wb.sheetnames:
            ws = wb[name]
            parts.append(f'--- Sheet: {name} ---')
            for row in ws.iter_rows(values_only=True):
                parts.append('\t'.join(str(c) if c is not None else '' for c in row))
        return '\n'.join(parts)
    except Exception as e:
        return f"[XLSX parse error: {e}]"


def _parse_pdf(filepath: str) -> str:
    try:
        import fitz  # pymupdf
        doc = fitz.open(filepath)
        parts = []
        for page in doc:
            text = page.get_text()
            if text.strip():
                parts.append(f'--- Page {page.number + 1} ---\n{text}')
        return '\n'.join(parts) if parts else "[PDF has no extractable text]"
    except Exception as e:
        return f"[PDF parse error: {e}]"


def _parse_markdown(filepath: str) -> str:
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"[MD parse error: {e}]"


@csrf_exempt
def upload_and_parse_file(request):
    """POST /api/ai/upload-file — upload a file and return parsed text content."""
    if request.method != 'POST':
        return JsonResponse({"ok": False, "error": "POST required"}, status=405)

    uploaded = request.FILES.get('file')
    if not uploaded:
        return JsonResponse({"ok": False, "error": "No file uploaded"}, status=400)

    # Check extension
    ext = uploaded.name.rsplit('.', 1)[-1].lower() if '.' in uploaded.name else ''
    if ext not in ALLOWED_EXTENSIONS:
        return JsonResponse({"ok": False, "error": f"Unsupported file type: .{ext}. Supported: {', '.join(sorted(ALLOWED_EXTENSIONS))}"}, status=400)

    if uploaded.size > MAX_UPLOAD_SIZE:
        return JsonResponse({"ok": False, "error": f"File too large ({uploaded.size} bytes). Max: {MAX_UPLOAD_SIZE} bytes"}, status=400)

    # Save to disk
    import uuid
    saved_name = f"{uuid.uuid4().hex}_{uploaded.name}"
    filepath = UPLOAD_DIR / saved_name
    with open(filepath, 'wb') as f:
        for chunk in uploaded.chunks():
            f.write(chunk)

    # Parse based on extension
    text_extensions = {'txt', 'log', 'json', 'xml', 'csv', 'py', 'js', 'html', 'css', 'yaml', 'yml'}
    content = ""
    parse_error = None

    try:
        if ext in text_extensions:
            content = open(filepath, 'r', encoding='utf-8', errors='replace').read()
        elif ext in ('md', 'markdown'):
            content = _parse_markdown(str(filepath))
        elif ext == 'docx':
            content = _parse_docx(str(filepath))
        elif ext == 'xlsx':
            content = _parse_xlsx(str(filepath))
        elif ext == 'pdf':
            content = _parse_pdf(str(filepath))
    except Exception as e:
        parse_error = str(e)
        content = f"[Parse error: {e}]"

    # Truncate very long content for AI context
    if len(content) > 50000:
        content = content[:50000] + f"\n\n[... truncated {len(content) - 50000} chars]"

    return JsonResponse({
        "ok": True,
        "data": {
            "filename": uploaded.name,
            "size": uploaded.size,
            "type": ext,
            "content": content,
            "preview": content[:300] + ("..." if len(content) > 300 else ""),
            "error": parse_error,
        },
    })


# ═══════════════════════════════════════════════
#  Feature 1: Conversation rename
# ═══════════════════════════════════════════════

@csrf_exempt
def rename_conversation(request, conv_id):
    """PATCH /api/ai/conversations/{id}/rename — rename a conversation."""
    try:
        c = AIConversation.objects.get(id=conv_id)
    except AIConversation.DoesNotExist:
        return JsonResponse({"ok": False, "error": "conversation not found"}, status=404)
    try:
        data = json.loads(request.body.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({"ok": False, "error": "invalid request encoding, use UTF-8"}, status=400)
    title = data.get("title", "").strip()
    if not title:
        return JsonResponse({"ok": False, "error": "title is required"}, status=400)
    c.title = title
    c.save()
    return JsonResponse({"ok": True, "title": c.title})


# ═══════════════════════════════════════════════
#  Feature 2+3: Agent test connection & model list
# ═══════════════════════════════════════════════

# OpenAI-compatible model list endpoints
_MODEL_LIST_PATHS = ["/models", "/v1/models"]


def _call_model_api(agent, path, method="GET", body=None):
    """Call the model provider's API with the agent's credentials."""
    import requests
    api_key = decrypt_key(agent.api_key) if agent.api_key else ""
    base = (agent.base_url or "").rstrip("/")
    if not base:
        # Infer base URL from provider
        if agent.model_provider == "dashscope":
            base = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        elif agent.model_provider == "openai":
            base = "https://api.openai.com/v1"
        elif agent.model_provider == "anthropic":
            base = "https://api.anthropic.com/v1"
        elif agent.model_provider == "deepseek":
            base = "https://api.deepseek.com/v1"
        else:
            return None, "No base_url configured"
    url = f"{base}{path}"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    try:
        if method == "GET":
            resp = requests.get(url, headers=headers, timeout=15)
        else:
            resp = requests.post(url, headers=headers, json=body or {}, timeout=15)
        return resp, None
    except requests.RequestException as e:
        return None, str(e)


@csrf_exempt
def test_agent_connection(request, agent_id):
    """POST /api/ai/agents/{id}/test — test API connectivity and fetch models."""
    try:
        a = AIAgent.objects.get(id=agent_id)
    except AIAgent.DoesNotExist:
        return JsonResponse({"ok": False, "error": "not found"}, status=404)

    # Try to list models as the connectivity test
    available_models = []
    connected = False
    last_error = ""

    for path in _MODEL_LIST_PATHS:
        resp, err = _call_model_api(a, path)
        if err:
            last_error = err
            continue
        if resp is not None and 200 <= resp.status_code < 300:
            connected = True
            data = resp.json()
            # Parse model list from response
            if "data" in data:
                available_models = [m.get("id", "") for m in data["data"] if m.get("id")]
            elif "models" in data:
                available_models = [m.get("id", "") for m in data["models"] if m.get("id")]
            if available_models:
                # Sort: put the agent's current model at top
                cur = a.model_name
                available_models.sort(key=lambda x: (x != cur, x))
            break
        else:
            last_error = f"HTTP {resp.status_code}"

    if not connected and not last_error:
        # Try a simple chat completion as fallback connectivity check
        chat_body = {
            "model": a.model_name,
            "messages": [{"role": "user", "content": "hi"}],
            "max_tokens": 5,
        }
        resp, err = _call_model_api(a, "/chat/completions", "POST", chat_body)
        if err:
            last_error = err
        elif resp and 200 <= resp.status_code < 300:
            connected = True
        elif resp:
            last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"

    # Update agent health fields
    a.is_connected = connected
    a.last_checked_at = datetime.now()
    if available_models:
        a.available_models = json.dumps(available_models)
    a.save()

    return JsonResponse({
        "ok": True,
        "connected": connected,
        "available_models": available_models,
        "error": last_error if not connected else "",
    })


@csrf_exempt
def list_available_models(request, agent_id=None):
    """GET /api/ai/agents/{id}/models — get cached available models for an agent.
       POST /api/ai/models/detect — detect models from API config (no agent_id needed).
    """
    if request.method == "POST":
        # Direct detection from provided config
        data = json.loads(request.body)
        provider = data.get("model_provider", "")
        api_key = data.get("api_key", "")
        base_url = data.get("base_url", "")
        # Build a temporary agent-like object
        import requests
        if not base_url:
            if provider == "dashscope":
                base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
            elif provider == "openai":
                base_url = "https://api.openai.com/v1"
            elif provider == "anthropic":
                base_url = "https://api.anthropic.com/v1"
            elif provider == "deepseek":
                base_url = "https://api.deepseek.com/v1"
        models = []
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        for path in _MODEL_LIST_PATHS:
            try:
                resp = requests.get(f"{base_url.rstrip('/')}{path}", headers=headers, timeout=15)
                if 200 <= resp.status_code < 300:
                    data_json = resp.json()
                    if "data" in data_json:
                        models = [m.get("id", "") for m in data_json["data"] if m.get("id")]
                    elif "models" in data_json:
                        models = [m.get("id", "") for m in data_json["models"] if m.get("id")]
                    if models:
                        break
            except Exception:
                continue
        return JsonResponse({"ok": True, "models": models})

    # GET: return cached models for an agent
    if agent_id:
        try:
            a = AIAgent.objects.get(id=agent_id)
            models = json.loads(a.available_models) if a.available_models else []
            return JsonResponse({"ok": True, "models": models, "is_connected": a.is_connected,
                                "last_checked": str(a.last_checked_at) if a.last_checked_at else None})
        except AIAgent.DoesNotExist:
            return JsonResponse({"ok": False, "error": "not found"}, status=404)
    return JsonResponse({"ok": False, "error": "agent_id required"}, status=400)


# ═══════════════════════════════════════════════
#  Feature 4: Agent health check (called by frontend timer)
# ═══════════════════════════════════════════════

def health_check_all_agents(request):
    """GET /api/ai/agents/health — check connectivity of all active agents."""
    results = []
    for a in AIAgent.objects.filter(status="active"):
        # Quick connectivity test
        connected = a.is_connected
        if a.api_key:
            # Re-test if last check was > 30 min ago
            from datetime import timedelta
            needs_check = (
                not a.last_checked_at
                or (datetime.now() - a.last_checked_at.replace(tzinfo=None)) > timedelta(minutes=30)
            )
            if needs_check:
                # Use the chat completion endpoint as a lightweight check
                chat_body = {
                    "model": a.model_name,
                    "messages": [{"role": "user", "content": "ping"}],
                    "max_tokens": 2,
                }
                resp, err = _call_model_api(a, "/chat/completions", "POST", chat_body)
                connected = not err and resp is not None and 200 <= resp.status_code < 300
                a.is_connected = connected
                a.last_checked_at = datetime.now()
                a.save()

        results.append({
            "id": a.id,
            "name": a.name,
            "is_connected": connected,
            "last_checked": str(a.last_checked_at) if a.last_checked_at else None,
        })
    return JsonResponse({"ok": True, "agents": results})


# ═══════════════════════════════════════════════
#  Feature 5: AgentScope SSE session management
# ═══════════════════════════════════════════════

AGENTSCOPE_BASE = "http://127.0.0.1:8000"


def _get_agentscope_token(request):
    """Reuse the current user's JWT token for AgentScope calls."""
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header[7:]
    return ''


def _call_agentscope(path, method, body, token, timeout=10):
    """Make an HTTP request to the AgentScope service."""
    import requests
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}',
    }
    url = f'{AGENTSCOPE_BASE}{path}'
    try:
        if method == 'GET':
            resp = requests.get(url, headers=headers, timeout=timeout)
        elif method == 'POST':
            resp = requests.post(url, headers=headers, json=body, timeout=timeout)
        elif method == 'DELETE':
            resp = requests.delete(url, headers=headers, timeout=timeout)
        else:
            return None, 'unsupported method'
        return resp, None
    except requests.ConnectionError:
        return None, 'AgentScope service unavailable'
    except requests.Timeout:
        return None, 'AgentScope service timeout'
    except Exception as e:
        return None, str(e)


@csrf_exempt
def register_agent_in_agentscope(request, agent_id):
    """POST /api/ai/agents/{id}/register-scope — Register (or update) a Django agent with AgentScope.

    Creates credential + agent in AgentScope so that SSE streaming sessions can be created.
    """
    try:
        agent_cfg = AIAgent.objects.get(id=agent_id)
    except AIAgent.DoesNotExist:
        return JsonResponse({"ok": False, "error": "agent not found"}, status=404)

    api_key = decrypt_key(agent_cfg.api_key) if agent_cfg.api_key else ''
    if not api_key:
        return JsonResponse({"ok": False, "error": "API key required for AgentScope registration"}, status=400)

    token = _get_agentscope_token(request)

    # Map Django provider to AgentScope credential type
    # All OpenAI-compatible providers (openai, anthropic, deepseek, custom) use 'openai_credential' + base_url
    provider_type_map = {
        'dashscope': 'dashscope_credential',
        'anthropic': 'openai_credential',  # use openai_credential with anthropic base_url
        'openai': 'openai_credential',
        'deepseek': 'openai_credential',   # DeepSeek is OpenAI-compatible
        'gemini': 'openai_credential',
        'custom': 'openai_credential',
    }
    provider_type = provider_type_map.get(agent_cfg.model_provider, 'openai_credential')

    base_url = agent_cfg.base_url
    if not base_url:
        if agent_cfg.model_provider == 'dashscope':
            base_url = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
        elif agent_cfg.model_provider == 'deepseek':
            base_url = 'https://api.deepseek.com/v1'
        elif agent_cfg.model_provider == 'openai':
            base_url = 'https://api.openai.com/v1'
        elif agent_cfg.model_provider == 'anthropic':
            base_url = 'https://api.anthropic.com/v1'
        else:
            base_url = 'https://api.deepseek.com/v1'

    credential_body = {
        "data": {
            "type": provider_type,
            "api_key": api_key,
            "base_url": base_url,
        },
    }
    # Also store the agent_id as metadata so we can find it later
    credential_body["data"]["agent_django_id"] = str(agent_id)

    resp, err = _call_agentscope('/credential/', 'POST', credential_body, token)
    if err:
        return JsonResponse({"ok": False, "error": f"credential creation failed: {err}"}, status=503)
    if resp.status_code not in (200, 201):
        return JsonResponse({"ok": False, "error": f"credential creation failed: HTTP {resp.status_code} — {resp.text[:200]}"}, status=503)

    credential_id = resp.json().get('credential_id', '')

    # Step 2: Create agent (AgentScope assigns its own agent_id — save it for later use)
    agent_body = {
        "name": agent_cfg.name,
        "system_prompt": agent_cfg.system_prompt or "你是一个有用的AI测试助手。",
        "react_config": {
            "max_iters": agent_cfg.max_iters or 10,
            "parallel_tool_calls": agent_cfg.parallel_tool_calls,
        },
    }
    resp, err = _call_agentscope('/agent/', 'POST', agent_body, token)
    if err:
        return JsonResponse({"ok": False, "error": f"agent creation failed: {err}"}, status=503)
    if resp.status_code not in (200, 201):
        return JsonResponse({"ok": False, "error": f"agent creation failed: HTTP {resp.status_code} — {resp.text[:200]}"}, status=503)

    agent_scope_id = resp.json().get('agent_id', '')
    if not agent_scope_id:
        return JsonResponse({"ok": False, "error": "AgentScope did not return agent_id"}, status=503)

    # Persist the AgentScope agent_id so we can reuse it on subsequent calls
    agent_cfg.agent_scope_id = agent_scope_id
    agent_cfg.save(update_fields=['agent_scope_id', 'updated_at'])

    return JsonResponse({
        "ok": True,
        "agent_scope_id": agent_scope_id,
        "credential_id": credential_id,
    })


@csrf_exempt
def create_scope_session(request, conv_id):
    """POST /api/ai/conversations/{id}/create-scope-session — Create an AgentScope SSE session for this conversation.

    Returns the session_id needed for SSE streaming. The session persists — only created once per conversation.
    """
    try:
        conv = AIConversation.objects.select_related('agent').get(id=conv_id)
    except AIConversation.DoesNotExist:
        return JsonResponse({"ok": False, "error": "conversation not found"}, status=404)

    # If session already exists, return it
    if conv.agent_scope_session_id:
        return JsonResponse({
            "ok": True,
            "session_id": conv.agent_scope_session_id,
            "agent_scope_id": conv.agent.agent_scope_id,
        })

    # Ensure the agent is registered in AgentScope (returns its real agent_id)
    api_key = decrypt_key(conv.agent.api_key) if conv.agent.api_key else ''
    if not api_key:
        return JsonResponse({"ok": False, "error": "Agent has no API key — cannot create session"}, status=400)

    # Register agent only if not already registered
    if not conv.agent.agent_scope_id:
        reg_resp_data = register_agent_in_agentscope(request, conv.agent.id)
        reg_body = json.loads(reg_resp_data.content)
        if not reg_body.get('ok'):
            return JsonResponse({"ok": False, "error": f"Agent registration failed: {reg_body.get('error', 'unknown')}"}, status=503)

    agent_scope_id = conv.agent.agent_scope_id

    # Create a new credential for this session (AgentScope sessions are tied to a credential)
    provider_type_map = {
        'dashscope': 'dashscope_credential',
        'anthropic': 'openai_credential',
        'openai': 'openai_credential',
        'deepseek': 'openai_credential',
        'gemini': 'openai_credential',
        'custom': 'openai_credential',
    }
    provider_type = provider_type_map.get(conv.agent.model_provider, 'openai_credential')

    base_url = conv.agent.base_url
    if not base_url:
        if conv.agent.model_provider == 'dashscope':
            base_url = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
        elif conv.agent.model_provider == 'deepseek':
            base_url = 'https://api.deepseek.com/v1'
        elif conv.agent.model_provider == 'openai':
            base_url = 'https://api.openai.com/v1'
        elif conv.agent.model_provider == 'anthropic':
            base_url = 'https://api.anthropic.com/v1'
        else:
            base_url = 'https://api.deepseek.com/v1'

    token = _get_agentscope_token(request)
    credential_resp, err = _call_agentscope('/credential/', 'POST', {
        "data": {
            "type": provider_type,
            "api_key": api_key,
            "base_url": base_url,
            "agent_django_id": str(conv.agent.id),
        },
    }, token)
    if err or credential_resp.status_code not in (200, 201):
        return JsonResponse({"ok": False, "error": f"credential creation failed: {err or credential_resp.text[:200]}"}, status=503)
    credential_id = credential_resp.json().get('credential_id', '')

    session_body = {
        "agent_id": agent_scope_id,
        "chat_model_config": {
            "type": provider_type,
            "credential_id": credential_id,
            "model": conv.agent.model_name,
            "parameters": {
                "temperature": conv.agent.temperature or 0.7,
                "max_tokens": conv.agent.max_tokens or 4096,
            },
        },
    }
    resp, err = _call_agentscope('/sessions/', 'POST', session_body, token)
    if err:
        return JsonResponse({"ok": False, "error": f"session creation failed: {err}"}, status=503)
    if resp.status_code not in (200, 201):
        return JsonResponse({"ok": False, "error": f"session creation failed: HTTP {resp.status_code} — {resp.text[:200]}"}, status=503)

    session_id = resp.json().get('session_id', '')

    # Persist the session_id on the conversation
    conv.agent_scope_session_id = session_id
    conv.save(update_fields=['agent_scope_session_id', 'updated_at'])

    return JsonResponse({
        "ok": True,
        "session_id": session_id,
        "agent_scope_id": agent_scope_id,
    })
