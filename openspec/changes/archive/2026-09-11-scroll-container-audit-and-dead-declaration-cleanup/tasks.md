## 1. 失效声明清理（视觉零变化）

- [x] 1.1 定位根因：`App.vue` 的 `.main-content :deep(.doc-page)` 编译为 `.main-content[data-v-x] .doc-page`（权重 0,3,0）> `.doc-page`（0,1,0）与 `.doc-page.wb-shell`（0,2,0）
- [x] 1.2 删除 `.doc-page` 的 `height:100%` 与 `overflow-y:auto`，改为注释说明滚动归属
- [x] 1.3 等价性论证：13 处 `.doc-page` 全部位于 `.main-content` 内 → 覆盖恒成立 → 删除的是失效声明
- [x] 1.4 复检：postcss 95 块 0 错误；Vite 下发 `style.css` 200

## 2. 滚动容器审计（只读）

- [x] 2.1 写 `temps/scroll-audit.mjs`（postcss 遍历 style 块与 `.css`，统计 `overflow-y`/`overflow` 规则）
- [x] 2.2 产出 `temps/scroll-containers.md`：49 条规则逐条登记（文件 / 选择器 / 形式 / 是否配 `min-height:0` / 是否骨架内）
- [x] 2.3 汇总：未配 `min-height:0` **21** 条 · 骨架内 **10** 条 · 简写 **11** 条

## 3. 门禁验证

- [x] 3.1 postcss 全量解析 → **95 块 / 0 语法错误**
- [x] 3.2 Vite dev server（5173）→ `style.css` **200**
- [x] 3.3 `vue-tsc --noEmit` → **35 条既有错误不变**
- [x] 3.4 `node tests/check-style-gates.mjs` → 通过
- [x] 3.5 明确边界：其余 48 条滚动规则、断点、侧栏宽度、无骨架页面**均未动**（会改行为/外观，需确认）
