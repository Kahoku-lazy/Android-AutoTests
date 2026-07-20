---
name: code-read-step-types
description: How to read test step types from models/step_types.py StepType enum instead of .claude/rules/conventions.md
metadata:
  type: reference
---

# 测试步骤类型 — 从代码读取

**不要依赖 `.claude/rules/conventions.md` 的步骤列表**（手工维护，可能过时。当前规则写的是 14 种，实际代码有 17 种）。

## 如何获取

唯一的真相源：`models/step_types.py` → `class StepType(Enum)`。

直接 Read 该文件，查看所有步骤类型及其 docstring。

## 在对话中获取

```
Read models/step_types.py
```

StepType 枚举包含全部步骤类型：点击类 4 种、手势类 2 种、等待类 4 种、验证类 2 种、应用控制类 3 种、工具类 2 种，共 17 种。

执行分发映射在 `apps/test_runner/executor.py` → `StepExecutor.execute()` 的 handlers dict 中。

## 为什么

- 枚举是代码级真相源，步骤类型的增减必然反映在枚举中
- 规则文件需要手动同步，容易遗漏（如 `long_click` `swipe` `drag` `wait_any` 在代码中有但旧文档中无）
