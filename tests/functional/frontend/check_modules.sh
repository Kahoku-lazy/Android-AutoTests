#!/bin/bash
# Frontend module loading check — all 7 modules + login page
# Usage: bash scripts/run_frontend_check.sh

VITE_BASE="http://localhost:5173/src"
MODULES=(
  "modules/dashboard/index.vue"
  "modules/device-pool/index.vue"
  "modules/element-locator/index.vue"
  "modules/element-manager/index.vue"
  "modules/case-manager/index.vue"
  "modules/test-runner/index.vue"
  "modules/report-generator/index.vue"
  "modules/ai-assistant/index.vue"
  "views/LoginView.vue"
)

TOTAL=0
PASSED=0
FAILED=0
declare -a FAILURES

echo ""
echo "==================================================="
echo "  Frontend Module Loading Check"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "==================================================="

for module in "${MODULES[@]}"; do
  TOTAL=$((TOTAL + 1))
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$VITE_BASE/$module" 2>/dev/null)
  if [ "$HTTP_CODE" = "200" ]; then
    echo "  [PASS] $module"
    PASSED=$((PASSED + 1))
  else
    echo "  [FAIL] $module (HTTP $HTTP_CODE)"
    FAILED=$((FAILED + 1))
    FAILURES+=("$module")
  fi
done

echo ""
echo "  Total: $TOTAL | Passed: $PASSED | Failed: $FAILED"

if [ $FAILED -gt 0 ]; then
  echo ""
  echo "  Failed Modules:"
  for f in "${FAILURES[@]}"; do
    echo "    - $f"
  done
  echo ""
  echo "  Action: Frontend has compile errors. Run: cd frontend && npx vite build"
fi

echo "==================================================="
echo ""
[ $FAILED -eq 0 ] && exit 0 || exit 1
