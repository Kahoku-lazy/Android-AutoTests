## 1. 失效 testid 修复

- [x] 1.1 `SaveToElementsDialog.vue`：`data-testid="save-folder-cascader"` 从 `el-cascader` 移到包裹它的普通 `div`（`.save-folder-field`，`width: 100%`）；验证：真机弹窗内 `[data-testid="save-folder-cascader"]` 命中 **1**（标签 `DIV`）、`.el-cascader` 在其内、弹窗内 testid 现为 `save-folder-cascader` / `save-page-select` / `save-confirm-btn` 三个；包裹层宽 **394px** = 表单项内容宽，弹窗宽 **520px** 与改前一致，0 pageerror

## 2. store 公开面收窄

- [x] 2.1 `store.ts` 的 `return` 移除 `analyzeSnapshot` / `clearChecked`；验证：`frontend/src` 全量检索两名字，仅剩 `store.ts` 内部 4 处（`analyzeSnapshot`：定义 + `capture`/`viewSnapshot`/`retry` 调用）与 3 处（`clearChecked`：定义 + `applySnapshot`/`deleteSnapshot` 调用），组件侧 0 命中；`npx vitest run tests/device-inspector` **3 passed**

## 3. 门禁与归档

- [x] 3.1 `openspec validate remove-inspector-false-signals --strict`；验证：valid（`skip_specs` 生效）
- [x] 3.2 `npm run lint:styles`；验证：`LINT_EXIT=0`
- [x] 3.3 `npx vite build`；验证：退出码 0，✓ built in 1m 14s
- [x] 3.4 真机走查：打开「保存到元素定位」弹窗，testid 可查、包裹层与控件宽度无回归（218px 级联控件为改前既有宽度，见 design「伴随发现」）；验证：`temps/inspector-testid-check.mjs` 与 `temps/dbg-cascader-rules.mjs` 读数
- [x] 3.5 改动范围核对：仅 `components/SaveToElementsDialog.vue` 与 `store.ts` 两个文件；验证：两次 edit 的目标文件即此二者，未触碰其它文件

## 4. 伴随发现（已登记，未修）

- [x] 4.1 `.save-folder { width: 100% }` 永不生效（`.el-cascader` 根节点无 `data-v-*` 作用域属性 → scoped 规则不匹配），实测「目录路径」218px vs 「选择页面」394px；已写入 design「伴随发现」，修法（`:deep()`）与取舍留待产品决定
