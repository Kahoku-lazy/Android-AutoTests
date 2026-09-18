## Context

D-1 现状：`engines/android/airtest_u2.py::dump_hierarchy` import `algorithms.hierarchy.parse_hierarchy_xml`（XML 解析复用）；总纲 §三 字面写 "engines ❌ algorithms.*"。D-2 现状：`Node` 已在 `models/ui_nodes.py`，engines/algorithms 均已按此消费。

## Goals / Non-Goals

**Goals:**

- 文档与代码一致；两条规则可引用、可执行

**Non-Goals:**

- 不动代码；不改其他防火墙条目

## Decisions

- **D-1 裁决：允许**——`algorithms.*` 是零 `apps.*`/`django.*` 依赖的纯函数包，与第三方库同层；引擎内联 XML 解析反而制造第二份真相源。约束收紧为："engines 只可 import algorithms 的**纯函数**（无状态、无 I/O 副作用）"，禁止依赖 algorithms 中的有状态模块（当前不存在）
- **D-2 裁决：确认**——`Node` 归属 models/（L1b），algorithms/engines 均允许 `from models import Node`；总纲 §一依赖表述按此修正

## 模块防火墙自检

- 纯文档变更；通过

## Risks / Trade-offs

- [放宽后 engines→algorithms 滥用] → 规则写明"仅纯函数"；当前 algorithms 三模块均为纯函数，无有状态模块可供滥用
