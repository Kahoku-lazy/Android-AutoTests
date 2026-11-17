## Context

- 章节头结构在 `index.vue` 的 `.chapter-head`：图标块 + eyebrow + 标题 + 描述；规格 `dashboard-chapter-boards` 目前要求三者并存。
- 刷新按钮在 `WorkbenchHeader` 的 `#actions` 插槽，点击调 `refreshData`；`useDashboardAutoRefresh` 已存在但未被页面启用（默认 30s）。
- `useDashboardStats._fetchAndMap` 每次成功都写全部 ref 与 `lastUpdated`，没有变化检测。
- 页脚 `.dashboard__footer` 位于 `.doc-body`（`overflow-y: auto`）末尾，因此随滚动移动。

## Goals / Non-Goals

**Goals:**

- 章节头一眼一个标题；页头无按钮；数据变化才刷新；页脚固定。

**Non-Goals:**

- 不改接口与数据模型；不改图表组件；不动其它页面的刷新策略。

## Decisions

### 1. 用「数据指纹」而不是「深度比较每个 ref」判变化

`JSON.stringify` 统计 + 四张图 + 任务列表 + 活动去比较，一次比较覆盖整包；指纹显式排除 `last_updated`，避免时间戳每轮不同导致永远“有变化”。代价是序列化开销（数据量在 KB 级，5 秒一次可忽略）。

### 2. 复用已有 `useDashboardAutoRefresh`，只把间隔从 30s 改成 5s

该 composable 已处理「页面隐藏跳过」「回到可见立即拉取」「卸载清理」，不需要新写轮询。

### 3. 页脚移出滚动容器，而不是 `position: sticky`

`.doc-page--fixed` 是 flex 列、`.doc-body` 负责滚动；把页脚放成 `.doc-body` 的兄弟节点即可天然固定，sticky 反而要处理层级与遮挡。

## 模块防火墙自检

- 只改 `frontend/src/modules/dashboard/**` 与一条测试；无跨模块 import、无后端改动。

## Risks / Trade-offs

- [5 秒轮询增加后端压力] → 只读接口 + 已有缓存；后续可改为按页面可见性降频。
- [指纹比较漏掉某些字段] → 指纹覆盖所有展示用 ref；新增字段时必须同步加入指纹，已在代码注释中标注。
- [页脚移出后底部间距变化] → `.doc-body` 下内距从 `lg` 收到 `sm`，页脚自带外边距。
