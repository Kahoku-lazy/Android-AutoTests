---
name: port-defaults-doc-demo
description: 文档门户和工作流 Demo 的启动端口和约束
metadata: 
  node_type: memory
  type: project
  originSessionId: 20404476-773d-49d5-b645-8aafe1b0106f
---

## 端口约定

| 服务 | 端口 | 启动命令 |
|------|:--:|------|
| 文档门户 (`dev_docs/index.html`) | **9999** | `cd dev_docs && python3 -m http.server 9999 --bind 0.0.0.0` |
| 工作流 Demo (`tests/workflow-demo/index.html`) | **9998** | `cd tests/workflow-demo && python3 -m http.server 9998 --bind 0.0.0.0` |

## 关键约束

1. **Demo 禁止 `file://` 打开** — SVG 的 `filter="url(#ns)"` 和 `marker-end="url(#arrow)"` 在 `file://` 协议下无法解析 ID 引用，节点阴影和连线箭头会丢失
2. **禁止从项目根目录启动 HTTP 服务** — 根目录有其他项目，端口和路径会冲突
3. **必须从各自目录启动** — 文档从 `dev_docs/` 启动，Demo 从 `tests/workflow-demo/` 启动
4. **端口不可互换** — 9998 给 Demo，9999 给文档，不要混用

**Why:** 端口约定避免每次讨论启动时重新排查冲突；file:// 约束已在 2026-07-14 排查确认。

**How to apply:** 每次需要启动文档或 Demo 时，直接使用上表中的命令和端口，不要再从项目根目录启动或尝试 file:// 打开。
