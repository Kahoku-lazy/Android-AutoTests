#!/bin/bash
# PreToolUse hook -- 写文件前检测硬编码凭据
# 匹配: Edit, Write / 阻断: exit 2

INPUT=$(cat)
CONTENT=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('new_string', d.get('tool_input',{}).get('content','')))" 2>/dev/null)
FILE=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" 2>/dev/null)

for pattern in \
  "admin123" \
  "autotests2026" \
  "api_key\s*=\s*'[A-Za-z0-9]" \
  "SECRET_KEY\s*=\s*'[^']+"; do
  if echo "$CONTENT" | grep -qE "$pattern"; then
    echo "🚫 Blocked: 检测到硬编码凭据 in $FILE" >&2
    echo "   规则: .claude/rules/security.md" >&2
    exit 2
  fi
done
exit 0
