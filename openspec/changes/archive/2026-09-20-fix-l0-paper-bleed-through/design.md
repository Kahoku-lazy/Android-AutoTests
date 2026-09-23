## Context

见 `proposal.md` Why。叠层已是：壳层 `--paper` + `PaperDoodles`（`z-index: 0`）+ `.main-content__body`（`z-index: 1`）。全局 `.doc-page--fixed` / `.doc-body` 已是 `background: transparent`。模块 scoped 再写不透明 `--paper`，权重盖过全局透明，涂鸦被整页挡住。对照：`device-pool` 页根没有这层纸面，涂鸦能从间隙透出。

## Goals / Non-Goals

**Goals:**

- 只删页面根 / `.doc-body` 上挡涂鸦的不透明纸面声明。
- 删除后若裸 `.doc-page` 块只剩全局已有属性（如 `display:flex`），整块删掉，避免残留违规裸选择器。
- 用浏览器确认检查器、元素定位、仪表盘、用例工作台主区间隙可见涂鸦。

**Non-Goals:**

- 不改登录页、L0 壳层、`PaperDoodles` 图形。
- 不改内容块底色（含报告 `.doc-section`、检查器筛选栏、表格、树、截图画布、仪表盘章节钉板）。
- 不把报告白卡片改成透明；间隙透出即可。
- 不借机清全仓所有裸 `.doc-page` 覆写。

## Decisions

1. **只去掉页级填充，不改涂鸦层 z-index。** 涂鸦在 `__body` 之下；挡它的是不透明页根，不是层级反了。备选：把涂鸦抬到内容之上并 `pointer-events:none` —— 否决，会压在卡片上、破坏「稀疏水印在纸面」的层次。
2. **报告模块只核对、默认不改样式。** 列表/详情页根没有 `--paper` 填充；用户看到的「不像 L0」主要是 `.doc-section` 白卡片铺满。备选：给报告分区去底 —— 否决，那是内容面，超出本单。
3. **用例文件页只去 `.doc-body` 纸面，保留表包装纸面。** `.case-sheet__table-wrap` 是数据面容器。备选：连表包装一起透明 —— 否决，表格需要自己的底。
4. **登录页保留纸面。** 无 `PaperDoodles`，壳层纸面是唯一底。备选：登录也改透明 —— 否决，无涂鸦可透，且登录不走工作台壳。

## 模块防火墙自检

- 跨 App import：不涉及后端。
- 禁止跨 App import service/runner/consumer/state_machine：不涉及。
- INSERT/UPDATE/DELETE 收敛到 api.py：不涉及写库。
- 前端不直连数据库：无新 HTTP。

## Risks / Trade-offs

- [去掉 `.doc-body` 纸面后，分栏页顶部分隔线下面露出涂鸦，显得「空」] → 这是目标观感；内容块底色不动。
- [检查器工作区几乎铺满，涂鸦仍很少] → 工具条/筛选栏周围与页边仍应可见；不为此给工作区去卡片底。
- [scoped 删除后全局 `transparent` 生效，个别页依赖页根不透明盖住滚动露底] → 壳层已是同色 `--paper`，露底仍是暖白，只是多了涂鸦。
- [误删内容块 `--paper`] → 任务按文件清单改，禁止 ripgrep 全局替换。

## Migration Plan

1. 按 `tasks.md` 逐文件删声明并视情况删空 `.doc-page` 块。
2. 浏览器过一遍清单页；不通过则只补漏删的页级填充。
3. 回滚：恢复各文件的 `background-color: var(--paper)`（无数据迁移）。

## Open Questions

无。范围与保留项已在探索中对齐。
