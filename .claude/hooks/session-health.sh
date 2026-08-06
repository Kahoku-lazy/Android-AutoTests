#!/bin/bash
# SessionStart hook -- 会话启动时探测各服务状态

echo "🏥 服务健康检查..."

# Django
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8766/api/ 2>/dev/null | grep -q "200"; then
  echo "   ✅ Django  :8766"
else
  echo "   ⚠️  Django  :8766 — 未响应"
fi

# Vite
if curl -s -o /dev/null -w "%{http_code}" http://localhost:5173 2>/dev/null | grep -q "200"; then
  echo "   ✅ Vite :5173"
else
  echo "   ⚠️  Vite :5173 — 未响应"
fi

# Redis
if redis-cli ping 2>/dev/null | grep -q "PONG"; then
  echo "   ✅ Redis :6379"
else
  echo "   ⚠️  Redis :6379 — 未响应（AI 对话将降级）"
fi

exit 0
