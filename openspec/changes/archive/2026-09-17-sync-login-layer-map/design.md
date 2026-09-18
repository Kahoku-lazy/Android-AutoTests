## Context

现状约束：
- 生成器需要 dev server（5173）与一次真实失败登录（8766）才能跑完整流程，**不适合当作每次提交的快速检查**
- bundle 位于 `temps/`（`AGENTS.md` 规定临时产物放这里），但 `AGENTS.md` 同时规定「设计方案与报告」放 `dev_docs/DEV_TEST/` —— 该产物的归属本身有冲突，本变更不擅自搬迁
- `REGIONS` 里的 `src: 'LoginView.vue:44'` 等行号是手写的，任何行号漂移都无法自动发现

## Goals / Non-Goals

**Goals**：让「源码改了 → HTML 过期」这件事**可被一条秒级命令发现**，并把触发条件写进 agent 会读到的地方。

**Non-Goals**：不追求自动同步（不自动重跑生成器）；不接入 CI/钩子；不解决行号漂移；不改产物位置。

## Decisions

**D1：指纹内嵌进 HTML，而不是单独的 sidecar JSON。**

| 方案 | 结论 | 理由 |
|---|---|---|
| 内嵌 `<script type="application/json" id="layer-map-provenance">`（**采用**） | ✅ | 单一真相源：HTML 与「它是基于哪版源码生成的」不可分离，拷贝/改名/搬目录后依然成立；无 sidecar 与 HTML 互不同步的第二类故障 |
| 同目录 `source-fingerprint.json` | ❌ | 两个文件可能被分别移动/单独提交而失配，反而制造新的不一致面 |

**D2：指纹覆盖「登录模块源码 9 个 + 生成器自身 2 个」。**

登录模块源码决定测量结果（DOM 与样式）；生成器 `login-layer-map.cjs` 与模板 `login-layer-map.template.html` 决定**呈现与标注清单**（改 `REGIONS` 的说明文字也会让 HTML 过期）。故二者都必须入指纹，否则「改了标注却没重跑」这类漂移会漏检。

**D3：`--check` 不开浏览器。**

检查只需读文件算哈希，故实现为独立分支在 `require('playwright')` 之前返回——保证在没有 dev server、没有浏览器的环境下也能跑，这是它能被当作门禁的前提。

**D4：只报「哪些文件变了」，不尝试自动修。**

不自动重跑（重跑需要 dev server 与后端，且截图会变）；只 exit 1 并点名文件，把决策交给改动者。

## Risks / Trade-offs

- [自指哈希：生成器哈希自己] → 无副作用：哈希的是磁盘上当前内容，生成期间不会变；编辑生成器后必须重跑才会重新内嵌新哈希，这正是期望行为
- [`--check` 通过 ≠ HTML 内容正确] → 已登记：它只能发现「受管文件变了」，管不了 `REGIONS` 里手写行号的漂移，也管不了渲染结果是否真的符合预期；后者仍靠人工看图
- [受管文件清单需要维护] → 若将来登录页新增样式/组件文件，需同步加进 `SOURCE_FILES`；清单写在生成器顶部并附注释说明判据
- [产物在 `temps/` 与被要求长期维护相矛盾] → 本变更不动位置，登记为 Open Question 交用户决定

## Migration Plan

无。首次重跑生成器即写入指纹；旧版无指纹的 HTML 会被 `--check` 判为「缺少指纹，请重跑」并以 exit 1 提示。回滚 = 还原生成器与两份文档。

## Open Questions

1. bundle 是否应迁到 `dev_docs/DEV_TEST/`（`AGENTS.md` 规定报告类文档的位置）以匹配「长期维护」的定位？
2. `--check` 是否接入 `frontend/package.json` scripts 或 pre-commit 钩子（现钩子只跑 Python ruff）？接入需要先定「前端改动时是否强制阻断提交」。
