#!/bin/bash
# SessionStart hook — 检查架构文档是否落后于代码
# 对比 项目架构.md 的 auto 区域与代码实际状态
# 退出 0 → 一致, 退出 1 → 有 drift (不阻断 session，仅提示)

PROJECT_DIR="$CLAUDE_PROJECT_DIR"
CHECK_SCRIPT="$PROJECT_DIR/tools/gen_arch_stats.py"

if [ ! -f "$CHECK_SCRIPT" ]; then
  exit 0
fi

RESULT=$(python3 "$CHECK_SCRIPT" --check-md 2>&1)
EXIT_CODE=$?

if [ $EXIT_CODE -eq 1 ]; then
  echo "📋 [文档] $RESULT" >&2
  echo "   建议: 调用 architect agent → 自动同步文档" >&2
elif [ $EXIT_CODE -eq 0 ]; then
  # 一致，静默通过
  :
fi

exit 0
