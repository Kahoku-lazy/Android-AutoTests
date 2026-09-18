## 1. 文档

- [x] 1.1 在 `frontend/AGENTS.md` 的 L1 速查之后、`### 跨模块共享文件：shared/` 之前插入「### L2 层速查：页头区 / 页面根区」，含六段式。验证：`rg -n "层速查" frontend/AGENTS.md` 命中 3 节（L0:44 / L1:106 / L2:168）
- [x] 1.2 ②代码范围表与 ③/④ 各条与主 spec 及实际代码一致，不引入新规则。验证：逐条对照 `openspec/specs/frontend-l2-page-region/spec.md` 的 **9 条**契约（实测 Requirement 数 = 9），无超出契约的断言
- [x] 1.3 ⑤契约判据带可测数值（96px / 24px / 四个按钮色值 / 主题锚点），⑥记录 3 条已知缺口。验证：`--app-topbar-h`=96px、`--app-space-lg`=24px 实测命中；数值与两个已归档变更的实测记录一致
- [x] 1.4 节首写明行为真相源指向 `openspec/specs/frontend-l2-page-region/spec.md`。验证：该路径在节内出现且文件存在（9 条契约）

## 2. 自检与校验

- [x] 2.1 静态自检：文档引用的路径与类名在代码中存在。验证：`WorkbenchHeader.vue`（含 `.wb-header`）· `lucide-registry.ts`（**14** 个已登记名，实测 14）· `scroll-guard.ts` · `style.css` 的 `.doc-page`/`.doc-body`/`.doc-page--fixed .doc-body` · `workbench-theme.css` 的 `.wb-shell`/`.workflow-workbench` · `workflow/index.vue` 根与 `.wb-body` —— 全部命中；结构判据 19/19
- [x] 2.2 运行 `openspec validate docs-l2-quickref --strict`。验证：Change ... is valid（退出码 0）
