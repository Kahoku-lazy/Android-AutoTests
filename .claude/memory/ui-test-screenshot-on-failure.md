---
name: ui-test-screenshot-on-failure
description: UI 自动化测试失败必须截图嵌入 HTML 报告，所有修复必须留痕
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 921bc6d5-c227-471c-a6f0-467192f54b52
---

UI 自动化测试过程中出错或断言失败时，必须：

1. **自动截图** — `capture_screenshot(page, case_id)` → base64 data URI
2. **嵌入 HTML 报告** — 失败用例行显示 📸 缩略图，点击全屏放大
3. **记录修复痕迹** — `log_fix(case_id, problem, solution, auto_fixed)` → `fix_log` 列表
4. **即使自动修复也要留痕** — `auto_fixed=True` 标记，让用户知道发生了什么

**Why:** 用户需要看到测试失败时的页面状态，以及每次修复的过程。即使 AI 自动修好了，也要让用户知道曾经出过问题、怎么修的。

**How to apply:**
- `helpers.py` 必须导出 `capture_screenshot(page, case_id)` 和 `log_fix()` 和 `fix_log`
- `run_tests.py` 的 runner 在 UI 层 `except` 块中自动调用截图
- HTML 报告的「用例详情」表格中失败行嵌入 `<img src="data:image/png;base64,...">`
- HTML 报告新增「🔧 修复日志」section，展示 `fix_log` 表格

**关联**：[[agent-must-be-used]] [[task-completion-summary]] [[test-plan-workflow]]
