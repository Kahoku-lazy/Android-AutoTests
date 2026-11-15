## Context

动机见 `proposal.md` - Why。当前实现约束：

- `frontend/src/modules/dashboard/index.vue` 的 `.doc-body` 下有四个 `<section class="doc-section doc-section--board">`，依次用 `ch-ops` / `ch-ai` / `ch-asset` / `ch-trend` 四个类区分色标。
- 运行指标五卡与用例项目卡用的是同一款入口卡 `StatsAppCard`（薄包装 `KpiCard`，`variant="entry"`），二者都排在 `.dashboard__stats-grid`（`repeat(auto-fill, 168px)`）里。
- 「测试资产」章节额外用 `.asset-cols`（两列网格）包住唯一的「测试用例」子区；该网格原为「用例 + 元素」两列，元素定位退役后只剩一列。
- 章节色标由 `--ch-accent` 提供（`ch-ops` = `--c-device`，`ch-asset` = `--c-case`），章节头右侧 chip 走 `.chip-row` / `.chip.chip--teal`。

## Goals / Non-Goals

**Goals:**

- 章节数由四变三，两段内容收进一个「平台概览」章节板。
- 「测试用例」子标题与用例数 chip 保留，用例项目卡继续整卡跳转项目工作台。
- 不新增组件、不改统计接口与数据口径。

**Non-Goals:**

- 不改「AI 用量」「趋势与动态」两章的任何结构或样式。
- 不改 `KpiCard` / `StatsAppCard` 的视觉与交互。
- 不对 `.doc-body` 的滚动、留白、页脚做调整。

## Decisions

**1. 合并后复用 `.ch-ops` 作为章节类，不再新增 `.ch-overview`。**

章节色标 `--ch-accent` 只能取一个值。运行指标是这段内容的主线，取设备绿（`.ch-ops` 现成的 `--c-device`）语义最稳；用例侧的青绿由章节头 `chip--teal` 与卡片自身色值继续承担。

备选：新增 `.ch-overview` 类——只为一个章节服务、色标仍需二选一，等于给同一块内容加一层命名，收益为零。

**2. 两段各自一个 `.dashboard__stats-grid`，中间插 `.subhead`，不合并成一个大网格。**

运行指标固定 5 张、用例项目 0..N 张，塞进同一网格会读不出分组；`.subhead` 已有现成样式（含右侧延伸分隔线），正好承担「测试用例 Cases」这一层。

备选：沿用 `.asset-cols` 两列包住用例子区——该网格是为「用例 + 元素」两列设计的，元素退役后只剩一列会留半空，故一并撤掉。

**3. 用例数 chip 上移到「平台概览」章节头右侧。**

原来挂在「测试资产」章节头；该章节消失后，chip 跟着内容走，留在唯一章节头的 `.chip-row` 里，保持「用例总数」在首屏可见。

**4. 清理 `.ch-asset` 与 `.asset-cols` 的样式规则。**

两处规则删除前先确认没有第二个消费方（`grep` 全仓），避免留下孤立选择器。

## 模块防火墙自检

- 跨 App import：无。本次只动 `frontend/` 的 Vue 模板与页面级 CSS。
- 禁止跨 App import service/runner/consumer/state_machine：无后端改动。
- 所有 INSERT/UPDATE/DELETE 收敛到各 App 的 `api.py`：本次不涉及任何写操作。
- 前端不直连数据库；仪表盘不做写操作：沿用既有只读 stats / activities 数据源，未新增请求。
- 未引入新的跨模块依赖。

## Risks / Trade-offs

- [「测试资产」从章节降为子区，用例库入口的视觉权重下降] → 子标题、`Cases` tag 与章节头用例 chip 全部保留，用例项目卡仍整卡可点直达项目工作台。
- [删除 `.asset-cols` / `.ch-asset` 可能牵动别处引用] → 实现前全仓 `grep` 确认无第二消费方，门禁跑 `npm run lint:styles` / `lint:lines`。
- [两段挤进一个章节板后纵向过密] → 两段之间由 `.subhead` 自带上下 margin 分隔，章节板下内距维持 `--app-space-lg`，为卡片 12px 右下硬阴影留空间。
