## 1. 尺寸基准改为截图真实像素

- [x] 1.1 `ScreenshotView.vue` 新增 `sourceSize()`（优先 `img.naturalWidth/naturalHeight`，缺失时回落 props），`fitBox()` 改用它；验证：真机对比读数——旧基准（1440×3040）图片盒 **290×614**、比例 **0.4723**；新基准（截图真实 1080×2340）图片盒 **283×614**、比例 **0.4609**，与截图真实比例 **0.4615** 一致（差值来自取整，≤1px）
- [x] 1.2 `drawOverlay()` 的缩放基准、`displayScale()`（命中测试）与 `scrollToRow()` 的换算全部改用同一个 `sourceSize()`；验证：全文件 `props.screenW` 仅剩 `sourceSize()` 内的兜底与 props 变更 watcher（`grep 1440/3040` 只剩 ScreenshotView 的 prop 默认值）
- [x] 1.3 `index.vue` 去掉 `|| 1440` / `|| 3040` 假兜底；验证：模块内 `1440` / `3040` 仅剩 ScreenshotView 的 prop 默认值 2 处（`ScreenshotView.vue:8-9`），`index.vue` 命中 0

## 2. 同源 watcher 合并（由清退单移入）

- [x] 2.1 两处 `watch(() => props.selected, …)` 合并为一处（先重绘，再 `if (!el) return` + `nextTick(scrollToRow)`）；验证：该文件 `watch(() => props.selected` 命中 **1** 处；真机（`temps/inspector-watcher-final.mjs`，前提是 `fix-inspector-row-dblclick-selection` 已修好选择手势）——选中后画布哈希 `2305192828 → 3235392701`（`redrawOnSelect: true`，选中行 1），切换到另一条快照后 `3235392701 → 2945092193`（`redrawOnClear: true`，选中行 0），0 pageerror

## 3. 验收数据准备与真机走查

- [x] 3.1 用设备 `R5CT62RH88F`（1080×2340）抓取快照 `#345`（99 元素、截图 `inspector/shots/capture_20260921_170004_715750.png`）并「保存到元素定位」为页面 `#46`（页面名 `临时-截图基准校验`，99 元素入库）；验证：`get_page_full` 可返回该页与元素，截图文件 HTTP 200
- [x] 3.2 修前/修后对比：`temps/shot-basis-old.png`（模拟旧基准：页面级禁用 `naturalWidth`，等价于修前行为）与 `temps/shot-basis-new.png`；读数见 1.1；脚本 `temps/inspector-basis-check.mjs`

## 4. 门禁与归档

- [x] 4.1 `openspec validate fix-saved-page-shot-basis --strict`；验证：valid
- [x] 4.2 `npm run lint:styles`；验证：`LINT_EXIT=0`（批 1–4 全通过）
- [x] 4.3 `npx vite build`；验证：退出码 0，`✓ built in 1m 31s`
- [x] 4.4 `purge-inspector-dead-code` 已移除 watcher 合并项；验证：该单 tasks 中不再出现 `watch(() => props.selected` 字样（清退单已同步修正为 4 文件、17 任务）
