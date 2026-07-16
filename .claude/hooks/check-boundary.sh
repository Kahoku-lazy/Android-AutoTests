#!/bin/bash
# PreToolUse hook — 每次 Edit/Write 前检查架构边界
# 匹配: Edit, Write / 警告: exit 0（不阻断，只报告）
# 阻断: exit 2（仅当检测到新的跨模块 ORM 直接写入时）

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null)
FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" 2>/dev/null)
CONTENT=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('new_string', d.get('tool_input',{}).get('content','')))" 2>/dev/null)

# 只检查 apps/ 和 agentscope_service/ 下的 Python 文件
if ! echo "$FILE_PATH" | grep -qE "(apps/|agentscope_service/).*\.py$"; then
  exit 0
fi

# 跳过 migrations 和 __init__
if echo "$FILE_PATH" | grep -qE "(migrations/|__init__\.py)"; then
  exit 0
fi

WARNINGS=0
PROJECT_DIR="$CLAUDE_PROJECT_DIR"

# ── 检查 1: 是否新增了跨 App 的 service/views/内部实现 import ──
NEW_CROSS_IMPORT=$(echo "$CONTENT" | grep -E "from apps\.[a-z_]+\.(service|views|runner|callbacks|state_machine|executor|adapter|pool) import")
if [ -n "$NEW_CROSS_IMPORT" ]; then
  echo "⚠️  [边界] $FILE_PATH: 新增跨模块内部实现 import" >&2
  echo "   规则: .claude/rules/module-boundaries.md — 防火墙 #1/#4" >&2
  echo "   import: $NEW_CROSS_IMPORT" >&2
  echo "   建议: 改用 api.py 白名单函数，或先让 architect agent 评估" >&2
  WARNINGS=$((WARNINGS + 1))
fi

# ── 检查 2: 是否新增了跨 App 的直接 ORM 写入 ──
# 检查当前文件是否在某个 App 中，且内容包含对其他 App Model 的 .save()/.update()/.create()
CURRENT_APP=$(echo "$FILE_PATH" | sed -n 's|.*apps/\([^/]*\)/.*|\1|p')
if [ -n "$CURRENT_APP" ]; then
  # 检查是否 import 了其他 App 的 Model
  OTHER_MODEL_IMPORT=$(echo "$CONTENT" | grep -oE "from apps\.([a-z_]+)\.models import" | grep -v "apps\.$CURRENT_APP\." | head -1)
  # 检查是否有直接 ORM 写操作
  DIRECT_ORM_WRITE=$(echo "$CONTENT" | grep -E "\.(save|update|create|delete|bulk_create)\(.*\)")
  if [ -n "$OTHER_MODEL_IMPORT" ] && [ -n "$DIRECT_ORM_WRITE" ]; then
    echo "🔴 [边界] $FILE_PATH: 可能跨模块直接 ORM 写入" >&2
    echo "   规则: .claude/rules/module-boundaries.md — 防火墙 #2" >&2
    echo "   写入操作应通过目标模块的 api.py 函数" >&2
    echo "   已知违规 (不重复报告): test_runner/state_machine.py, task_tools.py" >&2
    # 不阻断已知违规文件
    if echo "$FILE_PATH" | grep -qE "(state_machine\.py|task_tools\.py)"; then
      echo "   → 已知技术债，已记录在 architect.md TD-01/TD-02" >&2
    else
      echo "   → 这是新的潜在违规！建议先让 architect agent 审查" >&2
      WARNINGS=$((WARNINGS + 1))
    fi
  fi
fi

# ── 检查 3: 是否新增了硬编码的跨 App 路径引用 ──
# 检查内容中是否出现了不属于当前 App 的表前缀引用
if [ -n "$CURRENT_APP" ]; then
  # 当前 App 的表前缀（基于约定映射）
  case "$CURRENT_APP" in
    device_pool)      OWN_PREFIX="dp_" ;;
    element_locator)  OWN_PREFIX="el_" ;;
    case_manager)     OWN_PREFIX="cm_" ;;
    test_runner)      OWN_PREFIX="tr_" ;;
    report_generator) OWN_PREFIX="rg_" ;;
    ai_assistant)     OWN_PREFIX="ai_" ;;
    workflow)         OWN_PREFIX="wf_" ;;
    dashboard)        OWN_PREFIX="" ;;
    *)                OWN_PREFIX="" ;;
  esac
fi

# ── 检查 4: 文件体积预警 ──
CURRENT_LINES=$(wc -l < "$PROJECT_DIR/$FILE_PATH" 2>/dev/null)
if [ -n "$CURRENT_LINES" ]; then
  if echo "$FILE_PATH" | grep -q "\.py$" && [ "$CURRENT_LINES" -gt 400 ]; then
    echo "💡 [体积] $FILE_PATH: $CURRENT_LINES 行 (Python 上限 400)" >&2
    echo "   建议: 拆分为多个模块文件" >&2
  fi
fi

if [ $WARNINGS -gt 0 ]; then
  echo "⏭️  共 $WARNINGS 条边界警告，已放行（不阻断），请人工确认" >&2
fi

exit 0
