---
name: code-read-api-endpoints
description: How to discover API endpoints from urls.py instead of .claude/rules/api-conventions.md
metadata:
  type: reference
---

# API 端点 — 从代码读取

**不要依赖 `.claude/rules/api-conventions.md` 中的端点清单**（那是手工维护的）。

## 如何获取

每个 Django App 的 URL 路由定义在自己的 `urls.py` 中：

```bash
# 一行命令列出全部路由
python manage.py show_urls 2>/dev/null || \
  grep -rn "path(\|re_path(" apps/*/urls.py
```

## 在对话中获取

直接 Read 以下文件获取准确的端点定义：

```bash
# 列出所有 urls.py
find apps -name "urls.py"

# 示例
cat apps/device_pool/urls.py       # /api/devices/*
cat apps/element_locator/urls.py    # /api/elements/*
cat apps/case_manager/urls.py       # /api/cases/*
cat apps/test_runner/urls.py        # /api/runner/*
cat apps/report_generator/urls.py   # /api/reports/*
cat apps/ai_assistant/urls.py       # /api/ai/*
```

WebSocket 路由在 `gateway/routing.py` 中。

## 为什么

- `urls.py` 是 URL 路由的代码级真相源
- 规则文件中的端点清单可能遗漏或过时
- 路由文件也包含视图函数名，可直接追溯代码
