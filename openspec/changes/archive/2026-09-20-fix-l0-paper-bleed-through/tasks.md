## 1. 去掉页级不透明纸面

- [x] 1.1 删除 `frontend/src/modules/device-inspector/index.vue` 页根上的不透明 `--paper`；若裸 `.doc-page` 块只剩全局已有属性则整块删除。验证：该文件页根不再声明 `background-color: var(--paper)`。
- [x] 1.2 删除元素定位三页 `.doc-body` 的不透明 `--paper`（`ProjectList.vue`、`ProjectWorkspace.vue`、`LocatorFileView.vue`），保留分隔线与滚动声明。验证：三文件 `.doc-body` 无 `background-color: var(--paper)`。
- [x] 1.3 删除 `frontend/src/modules/dashboard/DashboardView.style.css` 中 `.dashboard-workbench .doc-page` 的不透明 `--paper`，保留章节钉板 `.doc-section--board` 底色。验证：页根无该声明，钉板 `background: var(--paper)` 仍在。
- [x] 1.4 删除 `case-manager/ProjectWorkspace.vue` 与 `CaseFileSheet.vue` 的 `.doc-body` 不透明纸面；保留 `CaseFileSheet` 的 `.case-sheet__table-wrap` 底色。验证：两处 `.doc-body` 无纸面填充，表包装底色仍在。

## 2. 核对与回归

- [x] 2.1 静态核对 `report-generator` 各页、`device-pool`、`ai-assistant` 页根没有同类页级 `--paper`；有则只删页级、不改卡片。验证：`frontend/src/modules` 内 `.doc-page` / `.doc-body` 不再出现不透明 `var(--paper)` 填充（登录页与内容块除外）。
- [x] 2.2 浏览器打开 `/inspector`、`/elements`、`/dashboard`、`/cases` 工作台：主区间隙可见 `PaperDoodles`，点击工具条/表格不受挡；再看 `/reports` 卡片间隙（不改卡片）。验证：上述页涂鸦可见，登录页仍为暖白实色且无涂鸦。
- [x] 2.3 在 `frontend` 目录执行 `npx vite build --mode development`，构建通过。验证：命令 exit code 为 0。
