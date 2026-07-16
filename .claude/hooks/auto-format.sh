#!/bin/bash
# PostToolUse hook -- 代码改动后自动格式化
# 匹配: Edit, Write
# 后台运行，不阻断

INPUT=$(cat)
FILE=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" 2>/dev/null)

if [ -z "$FILE" ]; then
  exit 0
fi

FULL_PATH="$CLAUDE_PROJECT_DIR/$FILE"

# Python files → ruff
if echo "$FILE" | grep -qE '\.py$'; then
  python -m ruff format "$FULL_PATH" 2>/dev/null && echo "   📐 ruff formatted: $FILE"
fi

# Vue/JS/CSS files → prettier
if echo "$FILE" | grep -qE '\.(vue|js|css)$'; then
  cd "$CLAUDE_PROJECT_DIR/frontend" 2>/dev/null || exit 0
  npx prettier --write "$FULL_PATH" 2>/dev/null && echo "   📐 prettier formatted: $FILE"
fi

exit 0
