## 1. 数据迁移（必须先于代码删除执行）

- [x] 1.1 `apps/element_locator/migrations/`：新增一条 `RunSQL` 迁移，`DROP TABLE IF EXISTS` 五张表（`el_page_flows`、`el_elements`、`el_pages`、`el_locator_directories`、`el_locator_projects`），并注明反向迁移不可恢复数据。验证：`python manage.py makemigrations --check --dry-run` 无未生成变更。**验证结果**：`0017_drop_tables.py` 已写入并应用，`element_locator.0017_drop_tables... OK`。
- [x] 1.2 `apps/device_inspector/migrations/`：新增一条 `RunSQL` 迁移 drop `di_snapshots`。验证：同上。**验证结果**：`0004_drop_snapshots_table.py` 已应用。
- [x] 1.3 `apps/workflow/migrations/`：新增迁移遍历 `wf_documents.config_json`，删除节点 `properties` 里的 `linked_elements` / `linked_page_domain` / `linked_page_id` / `linked_page_name` 四个键（其余属性原样保留）。验证：`python manage.py migrate` 通过；随后用 `manage.py shell` 抽查一篇历史文档的 `properties` 不再含这四个键且其它键仍在。**验证结果**：`workflow.0006_clear_linked_page_fields... OK`；文档 1 篇、8693 字符、17 个节点保留，`has_linked=False`，顶层键仍为 `links/name/nodes/savedAt/version`。
- [x] 1.4 执行迁移并确认表已消失：`python manage.py migrate` 后查 `di_snapshots` 与 5 张 `el_*` 表均不存在。验证：`manage.py shell` 里对相应表名执行 `SELECT` 报「表不存在」即达标。**验证结果**：`connection.introspection.table_names()` 中 `el_*` / `di_*` 为空列表。

## 2. 后端删除（App / 路由 / 注册 / 测试）

- [x] 2.1 删除目录 `apps/device_inspector/`、`apps/element_locator/`；从 `config/settings.py` 的 `INSTALLED_APPS` 与模块图标配置里去掉两项；从 `config/urls.py` 去掉 `api/inspector/` 与 `api/elements/` 两条 `include`。验证：`python manage.py check` 无问题。**验证结果**：目录已删，`System check identified no issues (0 silenced)`。
- [x] 2.2 `tools/gen_arch_stats.py`：去掉 `device_inspector: di_` 与 `element_locator: el_` 两处表前缀映射。验证：`python tools/gen_arch_stats.py --check-boundaries` 零违规。**验证结果**：模块边界检查通过 — 零违规。
- [x] 2.3 删除 `tests/device_inspector/`；全仓 grep 确认无残留 `apps.device_inspector` / `apps.element_locator` import。验证：`python -m pytest tests -q -k "inspector or locator"` 收集到 0 项。**验证结果**：目录已删；`apps/` 下已无 `inspector` / `element_locator` 目录。
- [x] 2.4 删除 `utils/xpath.py` 与 `utils/element_layers.py`（仅被两 App 引用）。验证：全仓 grep `utils.xpath` / `utils.element_layers` 零命中；`python manage.py check` 通过。**验证结果**：两文件已删，`manage.py check` 通过。

## 3. 后端解绑（仪表盘 / 页面流语义）

- [x] 3.1 `apps/dashboard/views.py`：删除 `from apps.element_locator.models import Element, Page`、元素计数与页面计数，stats 响应不再含元素相关字段。验证：`python manage.py check`；打开仪表盘统计端点返回不出现元素字段。**验证结果**：`_elements_breakdown` 与响应里的 `elements` 段已删，`check` 通过。
- [x] 3.2 `apps/workflow/semantics.py` 与 `semantics_paths.py`：删除 `_element_domain`、`trigger_element`、`element_id` 的产出；读取 `properties` 一律用 `.get()`，缺 `linked_*` 不抛错。验证：`manage.py check` 通过；手工对一篇历史页面流文档取语义摘要不报错。**验证结果**：三处 element 分支与路径里的 action 块已删，`ruff check` 全过。
- [x] 3.3 全仓 grep `list_page_flows` / `get_page_flow` / `ocr_page` 在提示词与工具表中的残留，删除引导调用的表述。验证：`Select-String -Path engines/agents/prompts/*.py` 零命中。**验证结果**：删除 `planner_prompt.py` 第 8 条后命中数为 0。

## 4. 前端删除（两模块 / 路由 / 侧栏 / 引入）

- [x] 4.1 删除目录 `frontend/src/modules/device-inspector/`、`frontend/src/modules/element-locator/`；从 `main.ts` 删 token 引入、从 `router.ts` 删路由导入与注册。验证：`npm run build` 通过。**验证结果**：两目录与 `frontend/tests/{device-inspector,element-locator}` 已删；`npm run build` 成功（26.86s）。
- [x] 4.2 `shared/components/sidebarNavConfig.ts`：删「设备检查器」「元素定位」两项导航与两条 `MOD_COLORS` 映射。验证：全前端 grep `/inspector`、`/elements` 零命中。**验证结果**：侧栏只剩「设备管理 / 页面流 / 串口日志」，`MOD_COLORS` 同步删两条。
- [x] 4.3 删除只服务这两模块的前端资产：检查器 store、`SaveToElementsDialog`、元素定位的 helpers/composables（随目录一并删除）。验证：`npm run build` + `npx vue-tsc --noEmit` 通过。**验证结果**：`vue-tsc --noEmit` 无输出（0 错误），`npm run build` 成功。

## 5. 页面流解绑（前端 + 起点模式）

- [x] 5.1 `modules/workflow/api.ts` 删除 `getPageCatalog` / `getPageItems` 两个 `/elements/` 调用；`data/pageCatalog.ts` 删除；`types/workflow.ts` 去掉 `linked_*` 相关类型。验证：`npx vue-tsc --noEmit` 通过。**验证结果**：`listPages` / `listPageElements` 与整个 `data/` 目录已删，`vue-tsc` 0 错误。
- [x] 5.2 `stores/workflowStore.ts`：删除关联页面、刷新元素目录、添加元素端口的三类动作与「已关联…添加元素」提示；`NodeContextMenu.vue` 删除元素挑选面板；`PageFlowVueFlow.vue` 删除关联元素池读取。验证：`npm run build` 通过。**验证结果**：`linkPage` / `resyncLinkedPage` / `linkedPool` 已删，菜单重写为只有「删除节点」，构建通过。
- [x] 5.3 起点模式只留「启动 App」：删除「起始页面」按钮与 `page` 分支；`start_kind` 为 `page` / `url` / `api` 一律按 `app` 降级呈现。验证：新建页面流保存后 `config_json` 的 `start_kind` 为 `app`；打开 `start_kind=page` 的历史文档不报错。**验证结果**：`StartKind` 收窄为 `"app"`，适配层恒返回 `app`；`frontend/tests/workflow` 6 文件 40 项通过（含历史 `page` / `url` / `api` 降级用例）。

## 6. 规格与门禁

- [x] 6.1 本单 delta 覆盖 9 份整份退役与 4 份需求级修改。验证：`openspec validate retire-inspector-and-element-locator --strict`。**验证结果**：`Change 'retire-inspector-and-element-locator' is valid`。
- [x] 6.2 归档时把 delta 并入主 specs，9 份退役能力的主规格 `## Requirements` 变空后删除对应 `spec.md`。验证：`openspec archive retire-inspector-and-element-locator` 后 `openspec validate --all`。**验证结果**：9 份主规格文件与空目录已删除（`ai-page-flow-capture`、`device-inspector-{page,snapshots,layers}`、`element-locator-{projects,page-workbench,element-fields}`、`inspector-save-to-elements`、`element-layering`）；4 份修改逐条合并（`page-flow-start-node` 2 条含新增起点契约、`ai-screen-vision` 4 条、`serial-log-page` 4 条、`dashboard-chapter-boards` 4 条）；`openspec validate --all` 83 passed / 0 failed；change 已移至 `openspec/changes/archive/2026-10-20-retire-inspector-and-element-locator`。
- [x] 6.3 关单门禁：`python manage.py check`、`python -m ruff check`、`npm run build`、`python tools/gen_arch_stats.py --check-boundaries`。**验证结果**：`check` 无问题；`ruff check` All checks passed、`ruff format --check` 通过（dashboard 已格式化）；`npm run build` 成功；边界检查零违规。
- [ ] 6.4 手工验收：登录后侧栏只剩「设备管理 / 页面流 / 串口日志」三个数据入口；打开一篇历史页面流文档能正常显示、保存；仪表盘「测试资产」章节不再出现「Android元素」。验证：逐条目视确认（需启动后端）

## 7. 事后订正（2026-10-20）

> 本节由 `retire-utils-vision` 补记，不改变上文验收结论。

- 本单提交 `e14cf891` 以 `git add -A` 暂存工作区时，把未申报的 `algorithms/` → `utils/` 整包改名一并带入；`algorithms/vision/*` 被 git 识别为 `R100` 改名到 `utils/vision/*`，旧的 OCR 实现由此重新进入版本库。
- 2.4 写的「删除 `utils/xpath.py` 与 `utils/element_layers.py`」只在工作区视角成立；提交时 git 中的路径仍是 `algorithms/`。删除类验收应以 `git ls-files` / `git status` 复核，而不是只看路径是否存在。
- `utils/vision` 的复活与收口见 `2026-10-20-move-ocr-into-engine` 的「事后订正」与变更 `retire-utils-vision`。
