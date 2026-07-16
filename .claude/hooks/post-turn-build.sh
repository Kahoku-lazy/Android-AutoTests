#!/bin/bash
# Stop hook -- 每轮结束后跑编译检查（有改动时）

cd "$CLAUDE_PROJECT_DIR" || exit 0

# Check if any tracked files changed this turn
CHANGED=$(git diff --name-only 2>/dev/null | grep -v '\.claude/' | grep -v 'tests/' | grep -v 'logs/')
if [ -z "$CHANGED" ]; then
  exit 0
fi

echo "🔨 本轮机编译检查..."

FAILED=0

# Frontend changed?
if echo "$CHANGED" | grep -qE 'frontend/.*\.(vue|js|css)$'; then
  cd frontend 2>/dev/null || exit 0
  if npx vite build --mode development > /dev/null 2>&1; then
    echo "   ✅ frontend build"
  else
    echo "   ❌ frontend build FAILED — 请检查浏览器 Console" >&2
    FAILED=1
  fi
  cd "$CLAUDE_PROJECT_DIR"
fi

# Backend changed?
if echo "$CHANGED" | grep -qE '\.py$'; then
  if python manage.py check > /dev/null 2>&1; then
    echo "   ✅ manage.py check"
  else
    echo "   ❌ manage.py check FAILED" >&2
    python manage.py check 2>&1 >&2
    FAILED=1
  fi
fi

if [ $FAILED -eq 1 ]; then
  echo "⚠️  本轮改动编译未通过，请在下一轮修复" >&2
fi

exit 0
