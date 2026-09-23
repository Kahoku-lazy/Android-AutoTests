## Context

- 现状（读码核实）：`ScreenshotView.vue:128-138` 的 `fitBox()` 用 `props.screenW/screenH` 计算 `scale = min(cw/W, ch/H)` 并写死图片盒宽高；`:193-204` 的 `drawOverlay()` 用 `const s = w / props.screenW` 换算元素框。
- 数据缺口：`apps/element_locator/models.py:93-107` 的 `Page` 无屏幕尺寸字段；`apps/element_locator/api_snapshot.py:198-207` 的 `get_page_full` 不返回屏幕尺寸；`store.ts:306-317` 的 `viewSavedPage` 因此写出没有 `screen_w/screen_h` 的 snapshot 对象，`index.vue:117-118` 用 `|| 1440` / `|| 3040` 兜底。
- 真相来源：`apps/device_inspector/service.py:58-66` 的截图是整屏截图（`engine.screenshot_file`），且 `capture_snapshot` 记录的 `screen_w/screen_h` 取自 `device_info.displayWidth/Height` → **截图的像素宽高就等于屏幕宽高**。
- `.screen-img` 是无 `object-fit` 的 `width/height: 100%`（`ScreenshotView.css:62-68`）→ 盒比例与图片比例不一致时会被拉伸。
- 当前无可用对照数据：库内 5 个已保存页面中 2 个的截图路径指向已删文件（404）、3 个没有截图 → 验收必须先抓一张新快照并保存为页面。设备 `R5CT62RH88F`（1080×2340）在线空闲。
- `watch(() => props.selected, …)` 在 `ScreenshotView.vue` 出现两处（`:121-125` 带 `if (!el) return`、`:252` 无守卫）。后者是**清空选中（selected → null）时唯一确定的重绘点**（前者提前返回），因此只能合并、不能删。

## Goals / Non-Goals

**Goals:**

- 任意分辨率、任意页面记录完整度下，元素框与截图对齐
- 截图宽高比不被改变
- 去掉会掩盖数据缺失的假兜底
- 顺手合并同源 watcher（从清退单移入，语义不变）

**Non-Goals:**

- 不给 `Page` 加屏幕尺寸字段（零数据依赖方案已足够）
- 不改截图的生成与落盘（后端零改动）
- 不改元素框的配色 / 线宽 / 手势语义
- 不引入 `object-fit: contain`（盒比例已正确，再加会叠出第二套适配逻辑）

## Decisions

**D1 以 `img.naturalWidth/naturalHeight` 为唯一基准**
`fitBox()` 与 `drawOverlay()` 都从已加载的 `<img>` 取真实像素尺寸；取不到（未加载 / 尺寸为 0）时回落到 props 与现有 10px 阈值逻辑。
备选：给 `Page` 加 `screen_w/screen_h` → 否决：要迁移、要回填，且截图自身即真相（`service.py:58-66` 保证整屏截图）。
备选：从元素的 `bounds` 最大值推断屏幕尺寸 → 否决：内容不满屏时推断值偏小，且会随页面内容变化。

**D2 `screenW/screenH` props 降级为加载前兜底，`index.vue` 去掉假兜底**
`index.vue:117-118` 不再写 `|| 1440` / `|| 3040`；组件 props 默认值保留（类型契约不变），但仅在截图未就绪时参与。
备选：保留假兜底 → 否决：它把「这条记录没有屏幕尺寸」伪装成「屏幕是 1440」，正是本次故障的成因。

**D3 两处同源 watcher 合并为一处（从清退单移入）**
合并为「先 `scheduleDrawOverlay()`，再 `if (!el) return` + `nextTick(() => scrollToRow(el))`」。行为等价性：两个同源 watcher 在同一次 flush 内按创建序执行，`scheduleDrawOverlay` 自带 `overlayDrawPending` 去重 → 原实现的净效果 = 重绘一次 + 有选中时滚动一次。
备选：保留两处不动 → 否决：同源 watcher 分置两处会诱导读者「删掉重复的那个」，而那是清空态唯一的重绘点。
备选：直接删无守卫那处 → 否决：回归清空不重绘。

## 模块防火墙自检

- 跨 App import：零新增
- 跨 App import service/runner/consumer/state_machine：不涉及
- 写库收敛 api.py：不涉及（无后端改动）
- 前端不直连数据库：不涉及
- HTTP 出口：不变（本变更不发任何请求）
- 共享层：不改 `tokens.css` / `workbench-theme.css` / `AppTable`；`ScreenshotView.css` 仅在被删声明处（死 CSS 与无效 font-size 由清退单处理，本变更不碰）
- 后端 / 端点 / 路由 / 迁移：零改动

## Risks / Trade-offs

- [截图未加载完成时用兜底尺寸会短暂画错框] → 保持既有 `w < 10` 早退（未加载时本就跳过绘制），加载完成由 `@load` 触发重绘
- [jsdom 下 `naturalWidth` 恒为 0，组件级断言不可靠] → 单测里 stub 图片尺寸，或直接在真机以截图与像素读数验收；不以 jsdom 作为主验收手段
- [真机验收需要一条有可用截图的已保存页面] → 先抓一张新快照并「保存到元素定位」生成页面；设备已在线
- [与 `purge-inspector-dead-code` 同文件] → 已约定 watcher 合并移入本单，清退单同步移除该项；应用顺序以清退单在前、本单在后，或反之均不会冲突（改动点不同行）

## Migration Plan

1. 改 `ScreenshotView.vue` 的尺寸基准 → 合并 watcher → `index.vue` 去假兜底
2. 真机：抓新快照 → 保存为页面 → 回看，记录修前/修后对比（元素框重合、宽高比）
3. 门禁：`npm run lint:styles`、`npx vite build`、真机走查（选中/清空联动、双击画框）
4. 归档：delta 写入 `device-inspector-page`
5. 回滚：纯前端改动，`git revert`；无数据迁移

## Open Questions

（无）
