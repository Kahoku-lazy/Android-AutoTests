## Context

- 设计语言口径：`.agents/skills/doodle-craft/references/tokens.md` 要求阴影扁平（无模糊）；`tokens.css` 已登记三档扁平硬偏移影 —— `--shadow-sm: 2px 2px 0 rgba(0,0,0,0.04)` / `--shadow-md: 2px 3px 0 rgba(0,0,0,0.05)` / `--shadow-lg: 3px 4px 0 rgba(0,0,0,0.06)`，并有 `--comp-dialog-shadow: 4px 4px 0 0 var(--color-indigo-13)` 等组件档。
- 本次实测（含把裸 `0` 计入长度的解析器，避免漏检 `0 2px 8px` 这类写法）：全仓模糊半径大于 0 的阴影共 **8 处**，分布与形态如下：

| # | 位置 | 现值 | 模糊 | 形态 |
|---|---|---|---|---|
| 1 | `ai-assistant/components/AgentBasicInfo.vue:62` | `--avatar-shadow: 0 2px 8px rgba(61, 52, 40, 0.08)` | 8px | 柔和投影（且为模块唯一裸 rgba） |
| 2 | `ai-assistant/components/AgentFormFooter.vue:30` | `box-shadow: 0 4px 14px var(--nav-save-glow)` | 14px | hover 光晕 |
| 3 | `device-inspector/components/ScreenshotView.css:25` | `box-shadow: 0 1px 1px var(--screenshot-pin-shadow-color)` | 1px | 图钉微影 |
| 4 | `device-inspector/components/ScreenshotView.css:67` | `box-shadow: 0 4px 24px var(--screenshot-img-shadow-color)` | 24px | 屏幕柔和投影 |
| 5 | `device-inspector/components/PageElementsPanel.vue:251` | `box-shadow: 0 8px 32px var(--pep-enlarge-shadow-color)` | 32px | 放大预览浮层影 |
| 6 | `device-inspector/components/StructureAnalysisPanel.vue:339` | `box-shadow: 0 8px 32px var(--sap-enlarge-shadow-color)` | 32px | 放大预览浮层影 |
| 7 | `workflow/components/vueflow/PageFlowNode.vue:266` | `box-shadow: 0 0 8px var(--wf-node-api-glow)` | 8px | 外发光 |
| 8 | `workflow/components/vueflow/PageFlowVueFlow.vue:807` | `box-shadow: 0 18px 48px var(--wf-picker-shadow)` | 48px | 浮层大投影 |

- 相关的非违规写法（本次 MUST NOT 改动）：`PageFlowNode.vue:252/456/461` 的 `0 0 0 3px` / `0 0 0 1px` / `0 0 0 4px` 是 **spread 环**（模糊为 0），`.pf-node:241` 与 `.pf-node.selected` 已用 `--app-shadow-sm/md`。
- 动机见 `proposal.md`。

## Goals / Non-Goals

**Goals**

- 全仓模糊半径大于 0 的阴影命中数为 0（含自定义属性内嵌值）
- 浮层与强调态改用扁平硬偏移后仍与下层纸面可区分
- 零消费方的阴影自定义属性不残留
- 把「阴影扁平」立为可测规格，防止回归

**Non-Goals**

- 不统一阴影的**偏移档位**（2px/3px/4px 并存）与色源（rgba 黑 vs 墨色），该口径留给变更 11 的尺度收敛
- 不改 `PageFlowVueFlow.vue:806` 的对称 `border-radius: 14px`（变更 10）
- 不改 `device-inspector` 的截图/元素面板布局与 `workflow` 的节点几何
- 不引入新的阴影令牌（复用既有三档 + 既有组件档）

## Decisions

**D1 优先复用 `--app-shadow-*` 三档，而非为每处新造令牌**
理由：`tokens.css` 已是唯一登记处，三档覆盖 `sm/md/lg` 的层次需求；逐处新造令牌会扩大死令牌面。
备选：新增 `--comp-floating-shadow` 等语义令牌 —— 否决（本期无跨模块复用需求）。

**D2 需要保留模块色源时，只去掉模糊与竖直偏移，保留既有色源**
适用 #3 #4 #5 #6 #8：改为 `4px 4px 0 0 <既有色源>`（图钉与屏幕影用各自既有偏移量 `1px 2px 0 0` / `4px 4px 0 0`）。
理由：色源是模块已登记的绘制色（`--color-ink-05-a10/a30` 等），保留可维持模块观感差异；只把"柔"改成"硬"。
备选：全部替换为 `--app-shadow-lg` —— 部分否决：会让 device-inspector 与 workflow 的浮层失去色源差异，且 `--app-shadow-lg` 的 `rgba(0,0,0,0.06)` 对浮层过淡。

**D3 外发光（`0 0 8px`）整体替换为 `--app-shadow-md`**
适用 #7。理由：外发光本质是"用模糊做强调"，与扁平语言不可调和；API 节点已有 `border-left: 4px solid <accent>` 承担强调，改用常规硬偏移影即可，且 `.pf-node` 基类本就是 `--app-shadow-sm`。

**D4 删除随之成为零消费方的自定义属性**
适用 `--nav-save-glow`（仅 #2 消费）与 `--wf-node-api-glow`（仅 #7 消费）。理由：规格要求零消费方声明不残留（`frontend-l2-page-region`「No L2 declaration without a consumer」的同源精神）；且保留会误导后续维护者以为仍有光晕。
备选：保留以备将来 —— 否决，死声明即债。

**D5 `AgentBasicInfo.vue` 删除私有 `--avatar-shadow` 改用 `--app-shadow-sm`**
理由：该变量唯一用途是给头像预览卡一个阴影，同时它是该模块唯一的裸 `rgba()`；用共享档位可同时消除裸色与模块私有阴影名。
备选：把 `rgba(61,52,40,0.08)` 登记为颜色原子 —— 否决，为一个 8% 暖墨新增颜色原子不划算，且视觉差异不可辨。

## Risks / Trade-offs

- [浮层从"柔和投影"改成"硬偏移影"后可能与下层纸面区分度下降] → 所有涉及处都保留 `2px/3px` 墨色描边（放大预览 `border: 3px solid var(--ink)`、元素选择浮层有 `--wf-picker-border`、屏幕图与电话框有描边），tasks 含 Chromium 对比断言
- [去掉 `--nav-save-glow` / `--wf-node-api-glow` 后若有隐藏消费方会退化] → 已全仓 grep 确认各只有一处消费；tasks 含删后复检命中数为 0
- [解析器误报或漏报模糊阴影] → 采用"把裸 0 计入长度序列"的解析器，并额外对 `--*shadow*` 自定义属性单独扫描；tasks 含两种扫描均归零
- [误改 spread 环（`0 0 0 Npx`）导致焦点环/选中环失效] → 明确列为非违规并在 tasks 中复检 ring 数量不变

## Migration Plan

1. 先改 8 处阴影，再删两条死属性，最后复扫复核
2. 回滚策略：纯样式改动，回滚即 `git revert`；无数据、接口与路由迁移

## Open Questions

（无）