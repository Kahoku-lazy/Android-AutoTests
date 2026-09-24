## 1. 去掉类型标签

- [x] 1.1 `ProjectTree.vue` 行模板删除 `.explorer-row__kind` 节点（含 `--dir` / `--file` 分支）。验证：`npx vue-tsc --noEmit` 零错误、`npx eslint src/modules/case-manager` 仅剩既有 1 条 warning
- [x] 1.2 删除 `.explorer-row__kind` / `--dir` / `--file` 三条样式规则。验证：全仓检索 `explorer-row__kind` 仅剩本次变更文档命中（产品代码 0）
- [x] 1.3 行内其余节点（图标 / 名称 / 尾随信息 / 进入指示）与交互未变。验证：见 2.2 断言的右键菜单与批量选择

## 2. 行栅格适配窄左栏（去掉标签后暴露的既有溢出）

- [x] 2.1 行栅格由「5 列固定宽（`28px minmax(120px,1fr) 72px 140px 100px`）」改为「图标 / 名称（可压缩省略）/ 尾随信息 / 进入指示」四列，名称取 `minmax(72px, 1fr)`、尾随信息取 `minmax(0, max-content)`。验证：两行 `scrollWidth === clientWidth === 246`
- [x] 2.2 进入指示由「展开 / 收起」「进入表格 →」压成图标级（`▾` / `→`），语义放 `title`。验证：断言行内文本为「📂 临时分组 0 项 ▾」「📄 临时用例表 09-24 11:03 →」
- [x] 2.3 文件行时间省去年份（`MM-DD HH:mm`），完整时间戳放元素 `title`。验证：断言 `metaTitle = 2026-09-24 11:03`

## 3. 验证与关单

- [x] 3.1 模块门禁：`npx vue-tsc --noEmit` 零错误 · `npx eslint src/modules/case-manager` 无新增 · `npm run lint` 69 条与基线持平 · `npm run lint:styles` 批 1–4 全绿 · `npx vite build --mode development` 通过
- [x] 3.2 Chromium 端到端断言（临时项目「临时-标签断言」，跑完即删，`DELETE` 200）：`kindNodeCount = 0`；两行文本不含独立类型标签；两行 `scrollWidth === clientWidth`；目录行「0 项」+ `▾`、文件行「09-24 11:03」+ `→` 且 `title` 为完整时间；右键菜单仍为「重命名 / 删除文件」；批量模式仍出现勾选框与「全选 / 删除 / 退出」；0 控制台错误。证据：`temps/case-tree-kind-assert.json` + 截图
- [x] 3.3 边界检查：`python tools/gen_arch_stats.py --check-boundaries`
