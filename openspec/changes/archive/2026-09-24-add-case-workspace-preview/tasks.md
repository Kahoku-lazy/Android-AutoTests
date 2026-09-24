## 1. 预览组件

- [x] 1.1 新增 `frontend/src/modules/case-manager/components/CasePagePreview.vue`：props `file: TreeFileNode`、emit `open`；调 `getFileSheet` 读数据；用共享 `AppTable`（`accent="var(--c-case)"`）渲染五列：用例 ID / 测试类型 / 业务类型 / 标题 / 时间；不导入任何写函数。验证：`npx vue-tsc --noEmit` 零错误、`npx eslint src/modules/case-manager` 仅剩 `ProjectTree.vue:348` 一条**既有** warning（基线 69 条未增）
- [x] 1.2 类型列以枚举中文标签呈现且不可点；页脚为分页（共享 `usePagination`，每页 10 行 + 「第 X / Y 页 · 共 N 条」+ 上一页 / 下一页，边界禁用）；标题行只放**一个**「进入页面编辑」入口。验证：断言表头五列、页脚文案与禁用态、`ctaCount = 1`
- [x] 1.3 三态用共享件：加载 `SkeletonCard`、失败 `ErrorState`（可重试）、该文件无用例 `EmptyState`。验证：进入工作台未选文件时右栏为引导空态（`emptyPane = true`）且非空白

## 2. 工作台分栏

- [x] 2.1 `case-manager/tokens.css` 增加左栏宽度令牌 `--case-tree-pane-w: var(--layout-pane-left)`；同步把 `element-locator/tokens.css` 的 `--locator-tree-pane-w` 也改为引用同一 T0 档位（原先写字面量 320px 属 G7 门禁的漏网写法）。验证：`npm run lint:styles` 批 3 硬门禁由「失败 1 处」转为「模块声明持字面量 0」
- [x] 2.2 `ProjectWorkspace.vue` 改为左树右预览：`matchMedia("(min-width: 1280px)")` 判定宽屏；宽屏点文件写本地选中态、右栏挂 `CasePagePreview`（带 `:key`）；窄屏点文件 `router.push` 到 `/files/:fileId`；页头副标题给内容概况。验证：断言 `grid-template-columns: 280px 912px`；1024px 下无右栏且点文件地址变为 `/cases/projects/6/files/3`
- [x] 2.3 目录树 `@delete-file` / `@move-item` 等既有事件绑定不变。验证：`ProjectTree` 事件链未改，工作台仍能删文件与移动节点

## 3. 验证与关单

- [x] 3.1 模块门禁：`npx vue-tsc --noEmit` 零错误 · `npx eslint src/modules/case-manager` 无新增 warning · `npm run lint` 69 条（与基线持平）· `npm run lint:styles` 四批全绿 · `npx vite build --mode development` 通过。用例模块无独立 p0 用例集，故以「构建 + 端到端断言」替代单测
- [x] 3.2 Chromium 端到端断言（自建临时项目「临时-预览断言」+ 1 个文件 + 13 条用例，跑完即删，`DELETE` 返回 200）：宽屏点文件 URL 不变且右栏表头恰为五列；双击无输入框 / 无类型下拉 / 无标签菜单；预览期间写请求 `[]`；分页首页 10 行 + 上一页禁用、次页 3 行 + 下一页禁用、两页并集 13 条且零重复；「进入页面编辑」按键数 1 且点击后到 `/cases/projects/6/files/3`（详情页 13 行、26 个可编辑标签）；1024px 下无右栏、点文件跳详情；0 控制台错误。证据：`temps/case-preview-assert.json` + 四张截图
- [x] 3.3 边界检查：`python tools/gen_arch_stats.py --check-boundaries` → ✅ 零违规
- [x] 3.4 文档同步：`doodle-craft` 的 `references/page-layout.md` §4.7.1 补「用例管理工作台同壳：右栏为只读用例预览（五列）」并登记左栏宽度取 T0 档位；把「工作台断点迁移到 lg=1200px」列为待办
