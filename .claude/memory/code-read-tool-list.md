---
name: code-read-tool-list
description: How to read AgentScope Tool inventory from factory.py instead of .claude/rules/agentscope-tools.md
metadata:
  type: reference
---

# AgentScope Tool 清单 — 从代码读取

**不要依赖 `.claude/rules/agentscope-tools.md` 中的 Tool 清单**（手工维护，随 Tool 新增/删除会过时）。

## 如何获取

唯一的真相源：`agentscope_service/tools/factory.py`。

```bash
# 列出所有注册的 Tool
python -c "
from agentscope_service.tools.factory import build_business_tools
tools = [t() for t in build_business_tools()]
for t in tools:
    print(f'{t.name}: {t.description[:60]}')
"
```

## 在对话中获取

直接 Read `agentscope_service/tools/factory.py`，查看 `_ALL_BUSINESS_TOOLS` 列表。

每个 Tool 类的 `name`、`description`、`input_schema` 在对应的 `*_tools.py` 文件中。

## 为什么

- `factory.py` 的注册列表是代码级真相源
- Tool 的增删必然反映在 factory 注册中
- 规则文件需要手动同步，容易遗漏
