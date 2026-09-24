## 1. 文件行去时间

- [x] 1.1 `ProjectTree.vue` 行模板：`.explorer-row__meta` 改为仅在目录行渲染，文件行不再输出时间与 `title`。验证：`npx vue-tsc --noEmit` 零错误、`npx eslint src/modules/case-manager` 仅剩既有 1 条 warning
- [x] 1.2 删除失去消费方的 `formatTime` / `formatFullTime`。验证：文件内检索两个函数名命中 0
- [x] 1.3 `.explorer-row__meta` 样式保留（仍服务目录行计数）。验证：`npm run lint:styles` 批 1–4 通过

## 2. 验证与关单

- [x] 2.1 模块门禁：`npx vue-tsc --noEmit` 零错误 · `npx eslint src/modules/case-manager` 无新增 · `npm run lint` 基线不增 · `npm run lint:styles` 通过 · `npx vite build --mode development` 通过
- [x] 2.2 Chromium 对比断言（临时项目「临时-对齐断言」，含 1 个有子项目录 + 1 个空目录 + 1 个文件；跑完即删，`DELETE` 200）：用例行文本为「📂 临时分组 1」「📄 临时用例表 进入 ›」「📂 临时空组 空」——文件行**不含时间戳**，与元素定位的「📄 … 进入 ›」同构；两页行皮肤（默认描边透明 / 圆角 6px / 内边距 4px 8px / 行高 34px / 虚线引导线 / 选中 2px 墨框 + 硬阴影）逐值相同；名称元素为自然宽度（70px，5 个字未压缩）；右栏预览「时间」列仍在；0 控制台错误。证据：`temps/align-workbench-assert.json` + `temps/align-case.png`
- [x] 2.3 边界检查：`python tools/gen_arch_stats.py --check-boundaries` → ✅ 零违规
- [x] 2.4 文档同步：`doodle-craft` 的 `references/page-layout.md` §4.7.1 的「登记的数据差异」行已替换为「树行的职责边界」规格行
