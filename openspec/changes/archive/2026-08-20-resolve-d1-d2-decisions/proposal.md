## Why

L1a 详档登记的两处待评审决策悬而未决：D-1（`engines` import `algorithms.hierarchy` 纯解析是否违反总纲 §三 "engines ❌ algorithms.*" 的字面禁令）、D-2（`Node` 归属 models/，algorithms 允许 import `models.Node`，需回写总纲 §一 line 85 的依赖表述）。代码已按 D-2 落地（Node 在 models/ui_nodes.py）并按 D-1 复用（engines/android/airtest_u2.py import algorithms.hierarchy），文档与代码不一致，须裁决回写。

## What Changes

- **裁决 D-1（改规则）**：总纲 §三 防火墙 engines 行改为 "✅ 第三方引擎库 + models.* + algorithms.*（零 apps/django 依赖的纯函数包）"——纯解析复用优于内联；删除 "❌ algorithms.*（引擎不加工）"
- **裁决 D-2（回写表述）**：总纲 §一 line 93 依赖方向改为 "engines 依赖第三方库 + models + algorithms（纯函数）；algorithms 依赖第三方纯库 + models（仅类型定义）"
- L1a 详档 D-1/D-2 决策行标注"已裁决（2026-08-20）"
- 落地实测文档差距 #9 更新为已裁决

## 关联文档

- ARCH：`设计-目标架构-设备交互协议与引擎分层.md`（§一、§三）、`设计-L1a-算法层.md`（§八 决策登记）、`设计-现状架构-重构落地实测.md`（差距 #9）
- 纯文档裁决，无代码/行为变化：`skip_specs: true`

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无）

## Impact

- 仅 3 份文档正文；代码/前端/数据库零改动
