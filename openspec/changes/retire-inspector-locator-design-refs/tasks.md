## 1. 承载页与登记面（清单型）

- [ ] 1.1 `frontend-doodle-button`：硬边按键「已登记承载页清单」去掉设备检查器（`.inspector-workbench`）与元素定位文件详情页（`.locator-workbench.file-view`），并把涉事 Requirement 里对这两页的举例改为仍存在的承载页（设备管理 / 用例管理）。验证：`Select-String -Path openspec/specs/frontend-doodle-button/spec.md -Pattern 'inspector|locator|设备检查器|元素定位'` 零命中
- [ ] 1.2 `frontend-doodle-sketch-table`：模块色与描边线型登记去掉「设备检查器（`--c-element`）」与「元素定位文件详情页」，保留设备管理、报告、用例管理的登记。验证：同上 grep 零命中

## 2. 举例型（路由 / 面包屑 / 浮层 / 面板）

- [ ] 2.1 `frontend-doodle-subpage-nav`：单页模块举例去掉「设备检查器」，面包屑举例去掉元素定位文件页，改为用例管理等价举例。验证：grep 零命中
- [ ] 2.2 `frontend-doodle-sketch-card`：三处「用例 / 元素定位 / 页面流」列表举例改为「用例 / 页面流」。验证：grep 零命中
- [ ] 2.3 `frontend-l0-design-tokens`：截图面板与元素选择浮层的举例去掉检查器表述。验证：grep 零命中
- [ ] 2.4 `frontend-l2-page-region`：路由举例去掉 `/inspector` 与 `/elements/*`。验证：grep 零命中
- [ ] 2.5 `frontend-l3-container`：页面举例去掉 `/inspector`、`/elements`、`/elements/projects/:code`、`/elements/projects/:code/files/:fileId`。验证：grep 零命中
- [ ] 2.6 `frontend-l4-data-surface`：设备检查器表格分页举例改为用例管理或设备管理等价举例。验证：grep 零命中
- [ ] 2.7 `frontend-l5-overlay`：弹层举例去掉「保存到元素定位」。验证：grep 零命中

## 3. 参照型（参照物消失）

- [ ] 3.1 `frontend-split-pane`：「两个工作台（元素定位 / 用例管理）共用」改为「用例管理工作台使用，后续分栏页可复用」。验证：grep 零命中
- [ ] 3.2 `case-manager-workspace-preview`：「与元素定位项目工作台逐项同源」改为「以用例管理自身既有左栏目录树与工具栏为基线」，并注明跨模块对照对象已随元素定位退役消失。验证：grep 零命中

## 4. 收尾与门禁

- [ ] 4.1 全规格库 grep 复核：`Get-ChildItem openspec/specs -Recurse -Filter *.md | Select-String -Pattern 'inspector|/elements|设备检查器|元素定位'` 命中仅允许出现在明确保留处（如「随元素定位退役」这类说明），逐条记录理由
- [ ] 4.2 `openspec validate retire-inspector-locator-design-refs --strict` 通过；归档后 `openspec validate --all` 无失败项
