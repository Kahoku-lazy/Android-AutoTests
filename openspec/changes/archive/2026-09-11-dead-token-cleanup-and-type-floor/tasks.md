## 1. 令牌清理（13 个零使用）

- [x] 1.1 精确审计：跳过定义行与注释、统计**原始令牌名**出现（含 `style="--x:"` 绑定与 `setProperty`）→ 149 个零使用令牌；锁定 3 个纯废弃家族（`--app-glass-*` 5 + `--doodle-font-*` 4 + `--app-sidebar-*` 4）
- [x] 1.2 删除 13 行定义；验证三个家族名全仓库 **0 残留**
- [x] 1.3 同步 tokens.css 文件头 @deprecated 清单（去掉 `--app-glass-*`）
- [x] 1.4 复检令牌总数 **307 → 294**

## 2. 字号归 12px

- [x] 2.1 `FilterTabs.vue:47`（11px）→ `var(--app-size-xs)`
- [x] 2.2 `CaseFileSheet.vue`（11px / 10px）→ `var(--app-size-xs)`
- [x] 2.3 `ProjectTree.vue:654`（11px）→ `var(--app-size-xs)`
- [x] 2.4 `ToolboxPanel.style.css:184`（10px）→ `var(--app-size-xs)`
- [x] 2.5 `PageElementsPanel.vue:227`（**9px** —— 由新增门禁脚本发现，原正则口径漏判单数字号）→ `var(--app-size-xs)`

## 3. 门禁化

- [x] 3.1 新增 `frontend/tests/check-style-gates.mjs`（字号下限 12px；默认告警、`--strict` 阻断；与 `tests/run.mjs` 等同目录惯例一致）
- [x] 3.2 `frontend/package.json` 新增 script `lint:styles`
- [x] 3.3 门禁在默认与 `--strict` 两种模式下均通过（0 违规）

## 4. 门禁验证

- [x] 4.1 `node tests/check-style-gates.mjs` → 通过（exit 0）；`--strict` → 通过（exit 0）
- [x] 4.2 `node node_modules/vue-tsc/bin/vue-tsc.js --noEmit` → 35 条既有错误不变，**0 条**与本次改动相关
- [x] 4.3 13 个被删令牌名全仓库残留 **0 处**；`font-size < 12px` **0 处**
- [x] 4.4 风险登记：字号提升可能让 6 个小徽标（9~11px → 12px）略微变宽，属预期视觉微调，已在 Impact 注明
