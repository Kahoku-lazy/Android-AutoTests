"""E2E SSE test v4 — samples all event types."""

import json
import threading
import time

from collections import Counter

import requests

BASE, AS_URL = "http://localhost:8765", "http://localhost:8000"
MSG = "Harness Engineering 是什么你清楚吗"


def ok(d):
    return d.get("ok", False) if isinstance(d, dict) else False


# ── 1. Login ──
resp = requests.post(
    f"{BASE}/api/ai/auth/login", json={"username": "admin", "password": "admin123"}, timeout=10
)
assert resp.status_code == 200 and ok(resp.json()), f"Login: {resp.text[:200]}"
token = resp.json()["access_token"]
user_id = resp.json().get("user_id", "1")
print(f"[OK] Login user_id={user_id}")
h_django = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
h_as = {"Authorization": f"Bearer {token}", "X-User-ID": str(user_id)}

# ── 2. Agent ──
resp = requests.get(f"{BASE}/api/ai/agents", headers=h_django, timeout=10)
agents = resp.json().get("agents", [])
agent = next(
    (a for a in agents if a and "测试" in str(a.get("name", ""))), agents[0] if agents else None
)
assert agent, f"No agent"
print(f"[OK] Agent id={agent['id']}")

# ── 3. Conversation ──
resp = requests.post(
    f"{BASE}/api/ai/agents/{agent['id']}/conversations/create",
    headers=h_django,
    json={"title": "E2E Test"},
    timeout=10,
)
conv_id = resp.json().get("id") or resp.json().get("data", {}).get("id")
print(f"[OK] Conv id={conv_id}")

# ── 4. Session ──
resp = requests.post(
    f"{BASE}/api/ai/conversations/{conv_id}/create-scope-session", headers=h_django, timeout=30
)
sess = resp.json()
assert ok(sess), f"Session: {sess}"
session_id = sess.get("session_id")
agent_scope_id = sess.get("agent_scope_id")
print(f"[OK] Session id={session_id}")

# ── 5. Save user message ──
requests.post(
    f"{BASE}/api/ai/conversations/{conv_id}/save-message",
    headers=h_django,
    json={"role": "user", "content": MSG},
    timeout=10,
)
print(f"[OK] Msg saved")

# ── 6. SSE stream ──
event_types = Counter()
sample_events = []
errors = []
text = ""
stream_error = None
start = time.time()
done_ev = threading.Event()


def listen():
    global event_types, sample_events, errors, text, stream_error
    sse_url = f"{AS_URL}/sessions/{session_id}/stream?agent_id={agent_scope_id}"
    try:
        sse_resp = requests.get(sse_url, headers=h_as, stream=True, timeout=300)
        if sse_resp.status_code != 200:
            stream_error = f"SSE {sse_resp.status_code}: {sse_resp.text[:200]}"
            done_ev.set()
            return

        evtype = None
        for line in sse_resp.iter_lines(decode_unicode=True):
            if line is None:
                continue
            if line.startswith("event: "):
                evtype = line[7:].strip()
                event_types[evtype] += 1
            elif line.startswith("data: "):
                data_str = line[6:]
                try:
                    d = json.loads(data_str) if data_str not in ("", "[DONE]") else data_str
                except Exception:
                    d = data_str

                if len(sample_events) < 30:
                    sample_events.append({"event": evtype, "data": str(d)[:120]})

                if evtype == "error" or (isinstance(d, dict) and d.get("type") == "error"):
                    errors.append(str(d)[:300])
                elif evtype in ("textGenerated", "textDelta"):
                    t = d.get("text", "") if isinstance(d, dict) else str(d)
                    text += t
                elif d == "[DONE]" or evtype in ("messageEnd", "runFinished"):
                    done_ev.set()
                    return
    except requests.exceptions.ChunkedEncodingError:
        done_ev.set()
    except Exception as e:
        stream_error = f"{type(e).__name__}: {e}"
        done_ev.set()


# Start SSE, wait, then chat
t = threading.Thread(target=listen, daemon=True)
t.start()
time.sleep(1)
chat_body = {
    "agent_id": agent_scope_id,
    "session_id": session_id,
    "input": {"name": str(user_id), "role": "user", "content": [{"type": "text", "text": MSG}]},
}
resp = requests.post(f"{AS_URL}/chat/", json=chat_body, headers=h_as, timeout=10)
print(f"[OK] Chat status={resp.status_code}")

done_ev.wait(timeout=120)
elapsed = time.time() - start

# ── 7. Report ──
print(f"\n{'=' * 50}")
print(f"  Duration: {elapsed:.0f}s | Events: {sum(event_types.values())}")
print(f"  Text: {len(text)} chars | Errors: {len(errors)}")
print(f"\n  Event types: {dict(event_types.most_common(15))}")

if sample_events:
    print(f"\n  Sample events (first 20):")
    for i, e in enumerate(sample_events[:20]):
        print(f"  [{e['event']}] {e['data'][:120]}")

if errors:
    print(f"\n  Errors ({len(errors)}):")
    for e in errors[:5]:
        print(f"  {e[:200]}")

if stream_error:
    print(f"\n  Stream error: {stream_error}")
print(f"{'=' * 50}")
