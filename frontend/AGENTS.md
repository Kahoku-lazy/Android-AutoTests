# frontend 索引 — 模块文档导航

> **层级**：根 `AGENTS.md` → **本文件（索引）** → `.agents/docs/frontend/**`（全局规范 + 模块文档）
>
> 本文件只保留**技术规范**与导航，不承载其余规则。**进入某个模块改代码前，先读下表列出的文档**；
> 文档里的红线、契约、样式与关单附加项，效力等同模块级约束。

## 技术规范

1. 编程语言： TypeScript 5.4
2. 前端框架： Vue 3.4 + Vite 5 + Element Plus
3. 状态管理： Pinia
4. 其它技术： Vue Router、ECharts、Mermaid、axios

## 怎么用

1. 先读上面的「技术规范」与根 `AGENTS.md`。
2. 改全局写法（项目结构 / 布局区域归属 / Vue 硬性规范 / 字号刻度）→ 读下表「全局规范」两篇。
3. 定位要改的模块 → 读下表对应文档（一个模块可能有多篇，按功能域分开）。
4. 跨模块改动 → 两个模块的文档都要读；样式与令牌口径以 `frontend_vue_conventions.md` 与各模块文档为准。

## 全局规范 → 文档

| 文档 | 讲什么 |
|------|--------|
| [frontend_project_structure.md](../.agents/docs/frontend/frontend_project_structure.md) | `public/` 与 `src/` 的分工、模块模板结构（按需取用）、L0–L5 布局区域与模块拥有的层级 |
| [frontend_vue_conventions.md](../.agents/docs/frontend/frontend_vue_conventions.md) | 7 条硬性规范（组件只渲染、禁魔法字符串、PascalCase、500 行拆分、字号只取刻度）+ 组合式 API 偏好与示例 |

## 模块 → 文档

| 模块 | 文档 | 讲什么 |
|------|------|--------|
| ai-assistant | [ai_assistant_workbench_and_cards.md](../.agents/docs/frontend/ai_assistant/ai_assistant_workbench_and_cards.md) | `/ai-assistant` 助手网格在上、工作流网格在下；两种卡片形态与「配置/任务」两个动作；配置与任务弹窗、新建入口位置 |
| ai-assistant | [ai_assistant_chat_thread_and_log_panel.md](../.agents/docs/frontend/ai_assistant/ai_assistant_chat_thread_and_log_panel.md) | 对话页页头与工具条、对话栏选中信号与改名/删除/取消三分、运行日志卡的位置宽度与三态、时间唯一来源 |
| ai-assistant | [ai_assistant_style_and_redlines.md](../.agents/docs/frontend/ai_assistant/ai_assistant_style_and_redlines.md) | 虚线只允许的四个落点与 OWNERS、笔色只取 tokens、卡片红线、快速验证命令 |
| bug-manager | [bug_manager_bug_list_page.md](../.agents/docs/frontend/bug_manager/bug_manager_bug_list_page.md) | `/bugs` 列表职责、`api.ts` → `/api/bugs/*` 单一出口、列表与详情契约 |
| bug-manager | [bug_manager_redlines_and_verify.md](../.agents/docs/frontend/bug_manager/bug_manager_redlines_and_verify.md) | 只做/禁止对照表、快速验证命令 |
| ops-console | [ops_console_user_management_page.md](../.agents/docs/frontend/ops_console/ops_console_user_management_page.md) | `/ops/users` 入口与页面构成、运营分组守卫、`/api/ops/users/` 端点与服务端分页、身份判定口径 |
| ops-console | [ops_console_style_and_redlines.md](../.agents/docs/frontend/ops_console/ops_console_style_and_redlines.md) | `--c-ops` 模块色、抽屉自持样式、五条红线、快速验证命令 |
| report-generator | [report_generator_report_ledger.md](../.agents/docs/frontend/report_generator/report_generator_report_ledger.md) | 报告台账只做/禁止表、查看报告按来源分流、`summary` 契约与唯一 HTTP 出口 |
| report-generator | [report_generator_layout_and_closeout.md](../.agents/docs/frontend/report_generator/report_generator_layout_and_closeout.md) | 版式与 `--c-report`、`constants.ts` 唯一真相源、关单附加项 |
| serial-log | [serial_log_entry_and_permissions.md](../.agents/docs/frontend/serial_log/serial_log_entry_and_permissions.md) | `/serial-log` 入口、两个模块私有 Tab、`/api/serial-log/` 端点与超管权限 |
| serial-log | [serial_log_style_and_redlines.md](../.agents/docs/frontend/serial_log/serial_log_style_and_redlines.md) | 多根节点面板的样式归属、`--c-device` 强调色、三条红线 |
| task-list | [task_list_task_board_page.md](../.agents/docs/frontend/task_list/task_list_task_board_page.md) | `/tasks` 任务清单职责、任务无详情页、`/api/tasks/*` 出口与 `report_run` 契约 |
| task-list | [task_list_redlines_and_verify.md](../.agents/docs/frontend/task_list/task_list_redlines_and_verify.md) | 只做/禁止对照表、快速验证命令 |

## 暂无模块文档的目录

| 目录 | 现状 |
|------|------|
| `case-manager` | 无模块文档（原 `AGENTS.md` 为 0 字节空文件，已删除） |
| `dashboard` | 无模块文档（原 `AGENTS.md` 为 0 字节空文件，已删除） |
| `device-pool` | 无模块文档（原 `AGENTS.md` 为 0 字节空文件，已删除） |
| `views/` | 无模块文档（原 `AGENTS.md` 为 0 字节空文件，已删除） |

上表内的目录，以及任何未列入「模块 → 文档」的模块，其改动按根 `AGENTS.md` 与上面「全局规范」两篇执行；
需沉淀模块口径时新增 `.agents/docs/frontend/{module_with_underscore}/{module_with_underscore}_{feature}.md` 并回到本表登记。
