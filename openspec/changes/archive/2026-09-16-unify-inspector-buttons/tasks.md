## 1. 皮肤落地

- [x] 1.1 在 `index.vue` 的 `<style scoped>` 新增页面作用域皮肤：`:deep(.el-button:not(.is-text):not(.is-link))` 与 `:deep(.action-btn)` 共用几何（`2px solid var(--ink)` / `border-radius: 2px` / `box-shadow: 2px 2px 0 0 var(--ink)` / `color: var(--ink)` / `font-weight: 700`），hover 为 `translate(-1px,-1px)` + `3px 3px 0 0 var(--ink)`，disabled 为 `opacity:.5` + `box-shadow:none`。验证：`cd frontend && npx vite build --mode development` 通过。
- [x] 1.2 `CaptureForm.vue` 删除 `.action-btn` / `.action-btn:hover` / `.action-btn:disabled` / `.action-btn--primary` 四条重复声明，几何与文字改由页面作用域统一承担；保留 `.cap-form` / `.cap-device` / `.cap-method`。验证：`rg "\.action-btn" frontend/src/modules/device-inspector` 仅剩 `index.vue` 一处定义。
- [x] 1.3 深色底与主色底按既有语义保留：`获取` 沿用墨黑底 `var(--ink)` + `--color-white` 文字；弹窗 `保存` 沿用 `--el-color-primary` 柠黄 + `var(--ink)` 文字。验证：`cd frontend && npm run lint:styles` 为 0（未新增纯色字面量、未引入未登记令牌）。
- [x] 1.4 原生 disabled 与 Element Plus `.is-disabled` 两条路径都收口到 `opacity:.5` + `box-shadow:none`，不出现「半透明但仍带位移阴影」的混合态。验证：选择器静态核对 + 任务 2.3 实测。

## 2. 实测验证（含反证）

- [x] 2.1 新增 `temps/inspector-buttons-check.mjs`，沿用 `temps/button-skin-check.mjs` 既有模式：`createRequire('frontend/')` 取 playwright，用 `vue/compiler-sfc` 的 `compileStyle` 编译真实 scoped CSS（`:deep()`/`:not()` 参与断言）并剥掉 `[data-v-*]`，在 Chromium 中以真实类名渲染后测量计算样式。验证：脚本退出码 0。
- [x] 2.2 断言几何与状态：工具条按键与弹窗按键的 `border` 为 `2px solid` 墨色、`border-radius` 四角均为 `2px`、`box-shadow` 为 `2px 2px 0 0` 加墨色且模糊半径为 `0`；hover 后 `transform` 呈左上位移 1px 且阴影偏移为 `3px 3px`。验证：断言逐条通过。
- [x] 2.3 断言 disabled 两条路径：原生 `button:disabled`（未选设备时的「获取」）与 EP `.is-disabled`（无快照时的「保存到元素定位」）均为 `opacity .5` 且 `box-shadow: none`。验证：断言逐条通过。
- [x] 2.4 断言 `.is-text` 排除生效：抽屉删除键 `border-width` 为 `0`、背景透明、`box-shadow: none`，保持无底无边图标形态。验证：断言逐条通过。
- [x] 2.5 断言对比度：「获取」（墨黑底 + 浅色字）与「保存」（柠黄底 + 墨字）两组，以相对亮度公式计算文字对底色对比度均 ≥ 4.5:1。验证：断言逐条通过（不靠肉眼判断）。
- [x] 2.6 **反证**：把改动前 `index.vue:264-272` 与 `CaptureForm.vue:48-57` 的声明逐条照抄进 `#oldWrap` 作用域，断言其 `border-radius`/`box-shadow` 与目标态**不同**；证明 2.2 的断言在旧规则下会失败，排除「恒真断言」。验证：反证断言通过且差异被打印。
- [x] 2.7 未登记页面回归：以不带 `.inspector-workbench` 的 `#OTHER` 作用域渲染同类按键，断言其几何与配色与变更前一致（证明皮肤未外溢）。验证：断言逐条通过。
- [x] 2.8 共享件与全局主题零差异：`git status --porcelain` 中 `FilterTabs.vue`、`ErrorState.vue`、`DoodleBtn.vue`、`workbench-theme.css`、`style.css`、`tokens.css` 无变更，并用文件 mtime 交叉确认。验证：零差异。

## 3. 关单

- [x] 3.1 `openspec validate unify-inspector-buttons --strict` 通过。
- [x] 3.2 `openspec archive unify-inspector-buttons -y` 归档；随后 `openspec validate --all` 全绿，并确认 `frontend-doodle-button` 主 spec 中该要求已按 RENAMED 更名生效、旧名无残留、ADDED 需求与 Scenario 已并入。验证：归档输出与全量校验均为通过。
