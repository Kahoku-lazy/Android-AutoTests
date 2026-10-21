## Context

报告工作台的状态筛选（全部 / 已完成 / 失败 / 已停止）已存在，但 UI 用 `AppTabs` 承载：`index.vue` 在 `AppTabs` 内用 `v-for` 为每个状态渲染一个 `el-tab-pane`，每个 pane 里都放同一张 `AppCard + AppTable`。结果是一个状态一份表格 DOM，筛选行为实际是「切 pane」而不是「过滤同一张表」；页签样式又被报告页的 `.report-tabs :deep()` 覆写成 `--c-report` 深色底 + `--ink` 文字（对比度不足）。

共享层已有专门用于筛选的 `FilterTabs`（原生 button、支持 `count` 角标，device-pool 与 task-list 已在用），比内容页签更贴合「状态过滤」的语义。

## Goals / Non-Goals

**Goals:**

- 状态筛选条落到「测试报告」分区头右侧，与标题同一行；窄屏自动换行。
- 四个筛选项带实时数量角标；切换筛选只更新同一张表的数据。
- 用共享 `FilterTabs` 的既定外观替换报告页私有页签皮肤，消除深色底 + 墨字。
- 删除重复表格 DOM 与页签内层滚动，纵向滚动只留在 `.doc-body`。

**Non-Goals:**

- 不改筛选的匹配口径（已完成含 completed/success，失败只含 failed，已停止只含 stopped；其它状态只在「全部」出现）。
- 不改表格列、行点击进 `/tasks/:id`、分页、显示行数与空态。
- 不改 `FilterTabs` 组件本身，也不新增颜色或令牌。
- 不改后端接口与统计口径。

## Decisions

### D1：用 `FilterTabs` 替换 `AppTabs`

`AppTabs` 是内容页签，语义是「不同内容面板」；状态筛选是同一张表的不同子集，应使用共享 `FilterTabs`。这同时消掉四个 pane 的重复表格，并把筛选条从表格容器里提到分区头。

备选「保留 `AppTabs` 只改颜色」被否：重复 DOM 与「切 pane 而非过滤」的结构问题仍在，且页签与表格工具栏的层级依旧混乱。

### D2：计数由页面 `computed` 计算，作为 `FilterTabs` 的 `count`

- 全部：`runs.length`（当前查询条件下的全部任务卡）。
- 已完成：`status === completed | success`。
- 失败：`status === failed`。
- 已停止：`status === stopped`。

计数与 `filteredRuns` 使用同一组 `STATUS_KEYS` 常量，避免筛选口径与角标口径分叉。其它状态（running / pending / interrupted / error）只计入「全部」，不新增第五个筛选项。

### D3：筛选条放在分区头右侧，表格卡独占一块

`doc-section__header` 本身就是 `space-between` + `wrap`；把 `FilterTabs` 放右侧即可与标题同排，窄屏换行。分区头内边距统一为 `--app-space-md`，表格卡保留原来的 16px 侧边距，形成「标题 + 筛选」与「表格」两级。

### D4：沿用共享筛选标签默认皮肤

不覆写 `FilterTabs` 的激活色。共享默认是浅底 + 墨框 + 胶囊圆角，文字始终为 `--ink` 或 `--app-text-secondary`，对比度达标；报告页不再写 `.report-tabs` 私有皮肤。备选「继续用 `--c-report` 深色底」被否，正是本次要修的低对比问题。

## 模块防火墙自检

- 纯前端展示层变更；不新增跨 App import，不触碰后端。
- 报告仍为只读：不新增写操作，不直打 `/api/tasks/*`。
- 行点击仍进入 `/tasks/:id`；任务编号仍不是 `/reports/:id` 链接。
- 不新增第三份状态标签映射：筛选项文案取 `constants.ts` 的 `STATUS_TAB_LABELS`。

## Risks / Trade-offs

- [筛选条从表格上方移到分区头，用户肌肉记忆变化] → 仍处于同一分区、同一屏内，且与 task-list 的筛选位置一致。
- [数量角标让「全部」显示为 0 时显得空] → 保留 0 角标，四个筛选项位置稳定，避免切换时布局跳动。
- [窄屏下标题与四个胶囊换行] → `doc-section__header` 已有 `flex-wrap`，换行后筛选条整行左对齐。
