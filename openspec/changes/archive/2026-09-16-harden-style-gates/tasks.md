# 任务：门禁加固

## 1. 引用完整性覆盖全部样式载体

- [x] 1.1 删除 `carrierRefs` 对 `.css` 的空返回与对 `.vue` `<style>` 块的抹白，改为逐行扫描全部模板/脚本/样式文本
- [x] 1.2 把载体遍历的文件类型由 `.vue/.ts/.js` 扩为 `.vue/.css/.ts/.js`，并据此合并重复的扫描范围常量
- [x] 1.3 实测覆盖数：载体引用 2661 → 3909 处

## 2. 运行时注入按边界汇集

- [x] 2.1 预读全部载体文件，把 `injectedNames` 的结果按 `boundaryOf(rel)` 汇集
- [x] 2.2 逐一核实新增的 8 处悬空 + 4 处跨边界，确认全部为 `X.vue` 注入、`X.style.css` 消费的误报（`--mod-color` / `--mc-color` / `--device-table-*` / `--ac-accent` / `--ac-tilt`）
- [x] 2.3 判定结果：悬空 0 / 跨边界 0 / 模块声明持字面量 0

## 3. 批 4 几何尺度门禁

- [x] 3.1 探测三类字面量真实存量（137 处），据实区分合法例外与待修违规
- [x] 3.2 G12 阴影模糊半径：层按逗号切分、跳过 `inset` 前缀与非 px 片段，模糊半径非 0 即阻断
- [x] 3.3 G13 圆角：`RADIUS_FIGURE` 图形量白名单 + `RADIUS_SHAPE` 已登记造型，等价四值展开单独判定为冗余
- [x] 3.4 G14 动效：`transition`/`animation` 简写中的裸时长必须取自令牌，`1.4s`/`1.5s` 为例外，`none` 合法；裸缓动 `ease` 判定排除 `--app-ease` 令牌名

## 4. 批 1 / 批 1b

- [x] 4.1 批 1（字号下限）由告警改为硬门禁，删除已无用途的 `--strict` 开关，同步头部用法注释
- [x] 4.2 新增驼峰 `fontSize` 探测（`.vue/.css/.ts/.js`），批 1b 记录上限：总数 18、低于 12px 7 处，超出即阻断

## 5. 修复门禁捕获的既有违规

- [x] 5.1 `TaskAttemptCard.vue`：删除 4 处指向未声明令牌的死兜底（`--app-border` ×3、`--app-bg-muted`）
- [x] 5.2 `LoginView.style.css:152/185`：等价四值圆角折叠为 `18px 26px` / `14px 20px`
- [x] 5.3 `SkeletonCard.vue:51`：等价四值圆角折叠为 `3px 5px`
- [x] 5.4 `RateBar.vue:54/60`：`width 0.3s` → `var(--app-duration-slow)`
- [x] 5.5 `motion.css:74`：`0.22s` ×2 → `var(--app-duration-slow)`

## 6. 验证与关单

- [x] 6.1 `node tests/check-style-gates.mjs` → EXIT=0，批 1/1b/2/3/4 全通过
- [x] 6.2 反证测试 A：`.vue` `<style>` 块内与 `.css` 内的悬空令牌各 1 处 → 2 处 G5 阻断，EXIT=1，移除后恢复 EXIT=0
- [x] 6.3 反证测试 B：模糊阴影 + 未登记圆角 + 裸时长 → 3 处阻断，EXIT=1，移除后恢复 EXIT=0
- [x] 6.4 反证测试 C：图表新增 `fontSize: 9` → 批 1b 超上限阻断，移除后恢复 EXIT=0
- [x] 6.5 `npm run lint:styles` → 0
- [x] 6.6 `npx vite build --mode development` → 0（34.21s）
- [x] 6.7 确认无探针残留（`grep gate-probe` = 0）并归档关单
