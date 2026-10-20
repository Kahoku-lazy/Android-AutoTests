## Context

见 `proposal.md` 的 Why。设计需要承接的现状事实：

- `apps/element_locator` 有 5 个模型（`LocatorProject` / `LocatorDirectory` / `Page` / `Element` / `PageFlow`），`apps/device_inspector` 有 1 个（`Snapshot`）。跨模块引用只有三处：`device_inspector → element_locator`（保存到元素定位）、`element_locator → device_inspector`（返回 `ImportConflictError`）、`dashboard → element_locator`（元素统计）。
- 页面流与本功能的耦合有三层：前端 `workflow/api.ts` 调 `/elements/pages/`、`workflowStore` 持有 `linked_elements` / `linked_page_domain`、后端 `workflow/semantics.py` 解析 `element_id` / `trigger_element` / element domain；起点节点的「起始页面」模式同样挂 `linked_page_id` / `linked_page_name` / `linked_elements`。
- `utils/xpath.py` 仅被 `device_inspector/service.py` 与 `utils/element_layers.py` 引用；`utils/element_layers.py` 仅被 `device_inspector/api.py` 引用。两个 App 删除后两者成为死代码。

## Goals / Non-Goals

**Goals**

- 6 张表与全部代码、路由、前端页面一次删净，规格库同步退役对应 9 份能力。
- 页面流在"没有元素定位"的前提下仍完整可用：页面节点手工命名、起点只剩「启动 App」、存量文档能打开能保存。
- 仪表盘不再出现元素类 KPI，且统计接口不返回元素字段。

**Non-Goals**

- 不清理 `media/inspector/` 下的历史截图与缩略图文件（删表后成为孤儿资产，另行处理）。
- 不清理视觉与布局类规格里的"举例型"引用（`frontend-doodle-*`、`frontend-l0`~`l5`、`frontend-split-pane`、`case-manager-workspace-preview`），另立一单。
- 不改页面流的画布交互、节点上限、覆盖层与起始节点数量约束。

## Decisions

### D1：先删表迁移、后删代码（顺序不可颠倒）

做法：在两个 App 目录**仍存在时**各加一条迁移，用 `RunSQL` 执行 `DROP TABLE IF EXISTS`（`di_snapshots`；`el_page_flows` / `el_elements` / `el_pages` / `el_locator_directories` / `el_locator_projects`）；跑完 `migrate` 再删除 App 目录、`INSTALLED_APPS` 注册与路由。

理由：App 目录一旦先删，迁移加载不到，表会永久残留且 `makemigrations` 会认为有未应用的模型变更；`IF EXISTS` 让迁移在已手工清过表的库上也能成功（幂等）。

### D2：页面节点改为纯手工内容，不再关联任何库

做法：`workflow/types/workflow.ts` 的节点属性去掉 `linked_elements` / `linked_page_domain` / `linked_page_id` / `linked_page_name`；`workflowStore` 删除"关联页面 / 刷新元素目录 / 添加元素端口"三类动作与对应提示；`NodeContextMenu` 删除元素挑选面板与"N 个元素"文案；`PageFlowVueFlow` 删除关联元素池读取；`api.ts` 删除 `getPageCatalog` / `getPageItems`；`data/pageCatalog.ts` 一并删除（仅服务该功能）。

理由：用户已确认"改为纯手工命名"。页面节点的名称与描述继续由用户填写，输出口由用户手工添加，页面流不因缺少元素库而失去表达能力。

### D3：起点只保留「启动 App」，存量 `page` 降级

做法：起点模式按钮与分支删除「起始页面」；渲染时 `start_kind` 非 `app` 一律按 `app` 呈现（复用既有 `url` / `api` 降级路径）。保存时不再写入 `start_kind=page`。

理由：`page` 模式的全部数据都来自元素定位；保留半死的模式会让用户看到点不进去的"已关联页面"。

### D4：存量文档四键由数据迁移清空

做法：在 `workflow` App 加一条迁移，遍历 `wf_documents.config_json`，删除节点 `properties` 里的 `linked_elements` / `linked_page_domain` / `linked_page_id` / `linked_page_name`（只删这四个键，其余属性原样保留）。迁移必须可逆到"结构不变、仅键消失"的程度（反向迁移不恢复数据，只说明不可逆）。

理由：用户已确认四个键全清；只删键不动文档结构，页面流仍能打开、保存。

### D5：后端语义摘要去掉 element 分支并容错

做法：`workflow/semantics.py` 删除 `_element_domain`、`trigger_element` 与 `element_id` 的产出；读取 `properties` 时一律用 `.get()`，缺 `linked_*` 字段视为无关联，不抛错。

理由：存量文档在迁移前后都可能带这些字段；摘要生成给 AI 读，任何键缺失都不该让整篇文档不可用。

### D6：仪表盘删卡 + 删字段，两端口径一致

做法：`apps/dashboard/views.py` 删除 `Element` / `Page` 的 import 与计数、stats 响应去掉元素相关字段；前端仪表盘删除「Android元素」KPI 卡。

理由：规格 `dashboard-chapter-boards` 明确"统计响应 MUST NOT 再包含元素或元素页面计数"；后端先删字段可避免前端出现空卡。

### D7：规格退役 = 逐条 REMOVED，归档时删空主规格

做法：8 份专属能力在 delta 里逐条 `REMOVED`（含 Reason / Migration）；`ai-page-flow-capture` 同样整份退役；归档后这些主规格的 `## Requirements` 会变空，按 OpenSpec 口径删除主 spec 文件。

理由：没有任何需求需要保留，留空骨架会持续误导。

### D8：分批边界

本单只做"代码 + 数据 + 9 份规格退役 + 3 份强关联修改"。视觉/布局类规格的举例引用（约 11 份）另单清理——它们约束的是共享视觉件与布局，页面删除不影响这些契约成立，但举例文字会指向已删页面。

## Risks / Trade-offs

- [删表不可逆，数据无法找回] → 用户已明确"数据全部删掉"；迁移用 `IF EXISTS` 幂等，误跑不会报错；建议执行前自行备份数据库。
- [删除 App 后 `django_migrations` 仍留历史记录] → Django 只按 `INSTALLED_APPS` 加载迁移，残留记录不影响 `migrate` 与 `check`；`makemigrations --check` 会因模型消失而提示一次性变更，执行后即稳定。
- [存量页面流打开报错] → 四键迁移 + 组件与语义层全部容错（缺字段按无关联处理），并在任务里要求手工打开一篇历史文档验证。
- [AI 助手仍引导调用 `list_page_flows` / `get_page_flow`] → 这两个工具的实现已随工作区重构删除；任务里要 grep 确认提示词与工具表里不再出现，避免模型调用不存在的工具（与上一单 `fix-agent-screenshot-contract` 同类问题）。
- [前端仍有指向 `/elements` 的深链] → 侧栏、路由与 `MOD_COLORS` 三处一并删除；任务要求 grep 全前端确认零命中。

## Migration Plan

1. 写两条删表迁移 + 一条文档键清理迁移 → `python manage.py migrate`。
2. 删除两个 App 目录、`INSTALLED_APPS`、`urls.py` 路由、表前缀映射。
3. 后端解绑（dashboard / workflow semantics）、删 `utils` 两个工具。
4. 前端删两模块与页面流解绑。
5. 规格退役与门禁。

回滚：数据删除后不可回滚；代码层回滚需同时恢复数据库备份，否则恢复的 App 会指向不存在的表。

## Open Questions

无。三项取舍已在 2026-10-20 会话确认：页面节点纯手工命名、起点删除「起始页面」模式、存量四个关联键全清。
