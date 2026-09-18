## Context

「落地不齐」拆开来看是两件事，实测把它们的比例摆清楚了（2026-09-15，`modules/**/*.{vue,css,ts}`，与 `tokens.css` 全文比对）：

| 维度 | 实测 |
|------|------|
| 未登记色值 | 68 个 / 117 次（CSS 侧 63 次 · .ts/script 侧 38 次，含 inline 模板样式） |
| 跨模块复用（≥2 模块） | **仅 2 个**（`#faf5ee` 是 `--doodle-bg` 的 fallback 漂移、`#5b4aa8` 是紫色文字 fallback） |
| 单模块专用 | **55 个** |
| `:root` 内模块私有变量 | 37（`--ai-*` 35 + `--case-*` 2） |
| `@deprecated` 别名 | 94 次 / 6 模块 |
| `--doodle-*` | 6 次使用（`--doodle-radius` / `--doodle-shadow` 零使用） |

结论：**令牌体系不缺层次，缺登记处**。所以本变更的主体不是「再发明一批全局令牌」，而是「给每个模块一个合法的登记位置，并把不该在全局的东西移出全局」。

## Goals / Non-Goals

**Goals:**

- 让「模块用到的每个色值都有登记处」成为可静态验收的事实：CSS 侧未登记字面量归零
- 让模块私有色板家族不再出现在 `:root`（消除 L0 §④.3 与实现的三处冲突）
- 退役重复令牌（`--doodle-*` 与 `@deprecated` 别名），消除「同名不同值」的陷阱
- 把图表 / canvas 色集中到各模块的图表色表，使「画布例外」可控可审

**Non-Goals:**

- **不改任何色值**（除三处与现役令牌同值可直接替换者：`--app-ink-muted`→`--app-text-muted` 等）；`--app-ink`(`#2d2d2d`)→`--ink`(`#1e1e24`) 属**已登记的视觉微调**，随本变更登记浏览器复核项
- 不动圆角 / 间距 / 字号（那不是色值登记问题；146 处单值圆角仍为独立观察项）
- 不抽共享色板组件、不新增全局令牌层次（实测跨模块复用只有 2 个值，新增层次缺依据）
- 不改布局、组件结构、API 与协议

## Decisions

**D1 · 模块家族令牌迁入作用域，而不是改规范文字承认它们全局**

备选是修改 L0 §④.3 允许全局家族令牌。否决依据来自实测：`--ai-*` 的消费点全部落在 `.ai-workbench` 作用域内的 4 个 AI 页面（`AgentDetail` / `index` / `SkillViewerPage` / `TaskDetailPage` 的页面根都带该类），作用域化零风险；唯一外部消费者 `device-pool/NetworkConnectDialog.vue` 是跨模块借用，本就该修。**并已验证作用域化不会打断弹层**：EP 2.7 `el-dialog` 渲染为 `Teleport({ to: appendTo, disabled: appendTo !== "body" ? false : !appendToBody })`，`appendToBody` 默认 `false` → Teleport 禁用 → 弹层原地渲染在组件树内，作用域变量可达；仓库内 `append-to-body` 命中 0。

**D2 · 模块专用色值的登记位置取「消费组件自身根类」**

模块私有值 55 个、单模块专用。若统一挂在页面根类（如 `.ai-workbench`）上，一旦某元素将来被 Teleport 到 body（`append-to-body`）就会丢变量。故口径定为：**声明在同时承载消费者的那个组件的根类上**，跟随元素移动，不依赖祖先链。分类色板（如 `case-manager` 的 7 色测试类型标签）已在上一变更按此模式落到 `.sheet-tag` 自身。

**D3 · 图表 / canvas 色保留字面量但必须集中**

同既有 ECharts 例外（`frontend/AGENTS.md` AppCard 节）：画布配色是独立主题。本变更只要求它们**集中在一处**（`report-generator/constants.ts` 的 `CHART_COLORS`、workflow 节点色表），不再散落在组件与模板里。

**D4 · 别名退役分「同值替换」与「近值替换」两类**

`--app-ink-muted`→`--app-text-secondary`（同 `#999`；初稿误写为 `--app-text-muted`，后者实为 `#bbb`）、`--app-accent-blue`→`--c-workflow`（同 `#89CFF0`）、`--app-green`→`--c-workflow`、`--app-blue`→`--c-element`（后两者本已是 `var(--c-*)` 别名）属**零视觉变化**；`--app-ink`→`--ink`（`#2d2d2d`→`#1e1e24`）与 `--app-accent-purple`→`--app-status-purple`（`#b39ef3`→`#C9B6F2`）属**已登记微调**，一并登记浏览器复核。

**D5 · 用并行子代理做逐模块登记，主审统一收口**

8 个模块的文件互不重叠，登记规则可以完全确定（「同值用令牌、否则就近具名声明、不改色值」），适合并行；共享层（`tokens.css` / 文档 / 规范）由主审先做完，避免子代理各造词汇。收口以**全仓静态扫描 + typecheck** 为准，不采信子代理自述。

## Risks / Trade-offs

- [改 `:root` 影响全局，若某消费点不在作用域内会静默退化（颜色丢失/回落到 fallback）] → 已用「消费点全部在作用域内」+「EP Teleport 禁用」两条实测排除；收口再跑一次 `--ai-`/`--case-` 消费点与作用域覆盖对照
- [`--app-ink`→`--ink` 让描边由 `#2d2d2d` 变 `#1e1e24`（略深）] → 登记为浏览器复核项；这是「一个墨色」的收敛方向，但无法在本环境渲染确认
- [子代理可能顺手改色值或过度抽象] → 任务书显式禁止改色值、禁止新增全局令牌，并要求附 before/after 计数；主审用全仓扫描复核
- [模块局部声明会比全局集中更「重复」] → 接受：重复命名优于隐式全局与 Teleport 失效；规则 8 本就要求等第二个真实消费方才抽象

## Migration Plan

- 无数据迁移；回滚为 revert 本变更
- 顺序：共享令牌层（含 EP Teleport 证据已记）→ 各模块登记（并行）→ 全仓复核 → 速查与规格 → 归档

## 模块防火墙自检

- 跨 App import：不涉及（只改 `frontend/src` 与文档）
- 禁止跨 App import service / runner / consumer / state_machine：不涉及
- 所有 INSERT / UPDATE / DELETE 收敛到各 App 的 api.py：不涉及，无后端与写操作
- 前端不直连数据库；仪表盘不做写操作：不涉及，不改 `api.ts` / HTTP / store
- 新增跨模块依赖：无（改动方向是**消除**跨模块令牌借用）
