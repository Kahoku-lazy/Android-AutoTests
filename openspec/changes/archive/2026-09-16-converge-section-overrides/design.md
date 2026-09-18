## Context

- `.doc-section` 的全局皮肤定义在 `style.css:207-271`：`.doc-section` 用 2.5px 墨色实线边 + `--app-radius-md` + `--app-shadow-sm`；`.doc-page--fixed .doc-section` 覆写内边距为 `18px 20px`；`.doc-section__title` 为 `--app-size-md`（16px）/ 700。
- `ai-assistant/EvaluatorTab.vue:581` 以裸选择器声明 `.doc-section { … border: 1px solid var(--ai-bg-subtle) … }` —— 与全局 `.doc-page--fixed .doc-section` **同为 (0,2,0)**，1px 近白线替换 2.5px 墨线，即"粗墨纸边消失"。
- `report-generator/index.vue:375-380` 以裸选择器重复声明全局已提供的 `background` / `border` / `border-radius` / `box-shadow`，并把 `.doc-section__title` 放大到 `--app-size-xl`（24px）；另在模板 269-270 行用行内 `style` 覆写内边距为 `0` 与 `14px 16px 0`。
- `ai-assistant/index.style.css:39-46` 以裸选择器重定义 `.doc-section__header`，其中 `display` / `justify-content` / `gap` / `margin-bottom` 与全局重复，真实差异只有 `align-items: baseline` 与 `flex-shrink: 0`。
- `dashboard/DashboardView.style.css:25` 的 `.doc-section--board` 是**合规**的私有 modifier（作为附加类使用），本变更不动。
- 动机见 `proposal.md`。

## Goals / Non-Goals

**Goals**

- `.doc-section` 的皮肤（背景 / 描边 / 圆角 / 阴影 / 内边距 / 标题字号）全站单一来源
- `/ai-assistant/evaluator` 恢复 2.5px 墨色纸边
- `/reports` 的 `doc-tag` 描边可见（消除"白底白框"）
- 模块真实差异（波浪下划线、header 对齐）以作用域限定的形式保留
- 模板中不再有对 `.doc-section` 的行内 padding 覆写

**Non-Goals**

- 不改 `.doc-section` 全局皮肤本身（变更 8 处理 `.doc-body` 垂直内边距时再统一）
- 不改 `dashboard` 的 `.doc-section--board`
- 不拆 `EvaluatorTab` 的行内 style 与圆角字面量（变更 10 / 15）
- 不改 `report-generator` 的 `AppTabs` 皮肤重写（变更 8）

## Decisions

**D1 删除重复全局属性的声明，而不是把整块搬到模块作用域**
理由：这些声明（背景/描边/圆角/阴影）与全局同值，保留即"第二真相源"，一旦全局调整就会出现分叉；规格要求"全局唯一定义"。只有**真实差异**才以 `.<模块根类>` 作用域保留。
备选：整块加 `.report-workbench` 前缀 —— 否决，重复声明仍然存在。

**D2 `/reports` 分区标题回到全局 16px，保留波浪下划线装饰**
理由：字号属"刻度"层级，跨模块应统一；波浪下划线是页面级装饰，不影响刻度与语义，且是该页的既有识别特征，删除属过度收敛。
备选：整体删除模块分区样式 —— 否决，会丢失装饰且改动面更大。

**D3 `doc-tag` 重定义整体删除**
理由：该重定义唯一的实质作用是 `1.5px solid var(--app-border-light)`（白色 → 描边不可见），其余属性全局 `.doc-tag` 已提供；删除后描边恢复为可见墨线。
备选：把 `--app-border-light` 改成 `--ink` —— 可行但仍在复制全局皮肤。

**D4 `EvaluatorTab` 直接删除两条裸重定义**
理由：其 `.doc-section` 只与全局差 `border`（更差）与 `padding` / `margin-bottom`；容器已是 flex 列 + `gap`，无需 `margin-bottom`；删除即恢复全局纸边与字号。
备选：加 `.ai-workbench` 作用域保留 `padding` —— 否决，全局内边距已是同一档（18/20 vs 24），保留只会造成模块间差异。

## Risks / Trade-offs

- [`/reports` 分区标题由 24px 缩到 16px、内边距与 header 间距变化，观感有变化] → 这正是"统一到全局皮肤"的目标；装饰保留；tasks 含浏览器计算样式断言
- [删除 `EvaluatorTab` 的 `margin-bottom` 后分区间距变小] → 容器 `.ai-workbench .doc-body` 是 flex 列且带 `gap: var(--app-space-sm)`，分区之间仍有余量；tasks 含目视确认项
- [行内 padding 改为类选择器后若类名拼写不一致会失去贴边效果] → tasks 含"检索 `style="padding` 命中数为 0"与表格分区贴边的断言

## Migration Plan

1. 先改 `report-generator`（样式 + 模板行内 → 类），再改 `ai-assistant` 两处，最后全仓检索复核
2. 回滚策略：纯样式与 class 改动，回滚即 `git revert`；无数据、接口与路由迁移

## Open Questions

（无）