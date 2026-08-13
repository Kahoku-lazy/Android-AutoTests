"""Test SSE streaming at raw TCP level — verify async fix produces true streaming."""

import json
import socket
import sys
import time

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwianRpIjoiMDRhZDk0OGYtNGEwMS00NjE1LTliM2EtODNkNmI1NTZhOTFjIiwiaWF0IjoxNzg2MzQ0MjAwLCJleHAiOjE3ODYzNDc4MDAsInR5cGUiOiJhY2Nlc3MifQ.p-NHo-UTj4HUsL1QSp0qgBGe3DLE-hW316MMWwr-fxA"

host, port, path = "127.0.0.1", 8766, "/api/ai/conversations/61/chat/stream"
body = json.dumps({"message": "say hi in 3 words"})

req = (
    f"POST {path} HTTP/1.1\r\n"
    f"Host: {host}:{port}\r\n"
    f"Content-Type: application/json\r\n"
    f"Authorization: Bearer {TOKEN}\r\n"
    f"Content-Length: {len(body)}\r\n"
    f"Connection: close\r\n"
    f"\r\n"
    f"{body}"
)


try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(60)
    sock.connect((host, port))
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    bytes_sent = sock.sendall(req.encode())
except Exception as e:
    sys.exit(1)

response = b""
chunks = []
start = time.time()
recv_count = 0
while True:
    try:
        chunk = sock.recv(65536)
        recv_count += 1
        if not chunk:
            break
        now = time.time()
        chunks.append(
            {
                "time": round(now - start, 3),
                "len": len(chunk),
            }
        )
        response += chunk
    except socket.timeout:
        break
    except Exception as e:
        break

sock.close()

if not response:
    sys.exit(1)

text = response.decode("utf-8", errors="replace")
header_end = text.find("\r\n\r\n")
headers = text[:header_end] if header_end > 0 else "(no headers found)"
body_text = text[header_end + 4 :] if header_end > 0 else text


# Count SSE events
events = body_text.strip().split("\n\n")
delta_count = 0
for evt in events:
    for line in evt.split("\n"):
        if line.startswith("data: ") and "_DELTA" in line:
            delta_count += 1


if len(chunks) > 2:
    pass
elif len(chunks) == 2:
    pass
else:
    pass

first_time = chunks[0]["time"] if chunks else 0
for c in chunks:
    gap = c["time"] - first_time
