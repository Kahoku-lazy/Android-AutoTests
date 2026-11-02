> HTML 交互原型（**Web 桌面**）：[html-bugs-prototype/index.html](./html-bugs-prototype/index.html)。

# BUG单管理 UI 原型需求

## 1. 文档信息

| 项 | 内容 |
| --- | --- |
| 页面名称 | BUG单管理 |
| 主路由 | `/bugs` |
| 文档版本 | v1.0 |
| 编写日期 | 2026-10-29（Asia/Shanghai） |
| 关联模块 | `modules/bug-manager/*`；`MOD_COLORS["/bugs"]={var(--c-runner)}` |
| 关联 HTML | [html-bugs-prototype/](./html-bugs-prototype/) |

### 1.1 路由表

| path | name | 组件 | meta.title |
| --- | --- | --- | --- |
| `/bugs` | `bug-manager` | index.vue | BUG单管理 |

### 1.2 抽屉
- BugDetailDrawer：详情、状态流转（待处理/已解决/已忽略）、关联任务链接。

## 2. 目标与范围

### 2.1 做什么

- 集中登记任务错误；按 UI 自动化 / 用例编写分类。
- 关键词与状态筛选；同步历史错误。
- 抽屉查看详情并改状态。

### 2.2 不做什么

- 不在本页新建任意 BUG（来源于任务失败同步）。
- 不改 /api/bugs 契约。

## 3. 用户与场景

| 角色 | 场景 | 期望 |
| --- | --- | --- |
| 测试 | 同步历史 | 补录失败任务 |
| 开发 | 标记已解决 | 状态更新 |
| 排查 | 点关联任务 | /tasks/:id |

## 4. 信息架构与页面布局

KPI 概览 + 分类 FilterTabs + 筛选栏 + 表 + Drawer。

> 交付形态为**桌面 Web**。

## 5. 视觉规范

模块色 `var(--c-runner)` / `var(--c-runner)`。

## 6. 组件与交互

| 组件 / 区域 | 说明 |
| --- | --- |
| KpiCard | 全部/UI/用例编写/待处理 |
| FilterTabs | 分类 |
| AppTable | BUG 表 |
| BugDetailDrawer | 详情与状态 |

### 6.1 主流程

1. **加载**：listBugs
2. **同步**：POST /bugs/sync/
3. **打开详情**：GET /bugs/:id
4. **改状态**：PATCH
5. **任务链**：/tasks/:id

## 7. 状态

| 状态 | 表现 |
| --- | --- |
| open/resolved/ignored | 状态徽章 |
| loading/syncing | 按钮禁用文案 |
| empty | 暂无 BUG 单 |

## 8. 接口（原型 Mock）

| 接口 | 用途 |
| --- | --- |
| `/bugs/` | 列表+summary |
| `/bugs/:id/` | 详情 |
| `PATCH /bugs/:id/` | 改状态 |
| `POST /bugs/sync/` | 同步 |

## 9. 已知缺口 / 新增建议 / 待设计

- 新增建议：按严重级别字段（现无）。
- 待设计：指派负责人。

## 10. 验收清单

- [ ] KPI
- [ ] 分类 Tab
- [ ] 同步 Mock
- [ ] 抽屉状态流转
- [ ] 任务链接 Toast

## 11. 线框

上 KPI 下表；右侧抽屉。

## 12. 交叉链接

- HTML：[./html-bugs-prototype/](./html-bugs-prototype/)
- 索引：[./00-模块原型索引.md](./00-模块原型索引.md)
