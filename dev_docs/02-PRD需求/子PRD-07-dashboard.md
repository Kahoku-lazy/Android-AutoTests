# 子PRD — 仪表盘 (Dashboard)

> 关联模块：`apps/dashboard/` · 前端：`frontend/src/modules/dashboard/`
> 关联全局：`./实际需求文档.md` · 跨模块只读聚合（设备 / 用例 / 元素 / 执行 / 报告 / AI）
> HTML 全功能规格：[`html/子PRD-07-dashboard-全功能需求.html`](./html/子PRD-07-dashboard-全功能需求.html)
> 版本：v1.0 · 状态：已实现 · 日期：2026-07-10

---

## 1. 模块功能目标

仪表盘是登录后的**首页聚合层**，不拥有业务写操作，只做跨模块只读统计与导航入口。核心职责：

1. **平台概览**：设备在线数、用例数、元素/页面数、执行次数、智能体数、报告数一屏可见
2. **执行趋势**：近 N 日成功/失败执行与新建用例趋势图
3. **近期任务**：最近执行摘要 + 活跃运行提示
4. **活动时间线**：跨模块最近事件流
5. **快捷入口**：跳转新建用例、执行测试、元素截图、AI 对话、查看报告

### 用户故事

| # | 角色 | 故事 | 验收标准 |
|---|------|------|----------|
| US-01 | 测试工程师 | 登录后进入仪表盘，一眼看到设备/用例/执行健康度 | `/dashboard` 加载后 KPI 卡片有真实 API 数据，无硬编码 |
| US-02 | QA 负责人 | 查看近两周执行成功/失败趋势 | 趋势图有 labels + success/failed 序列 |
| US-03 | 测试工程师 | 从首页一键跳到常用工作流 | 快捷操作跳转路径正确 |
| US-04 | 任意登录用户 | 无数据时页面不崩、有空态 | 全 0 时仍渲染，不报错 |

### 1.1 模块边界

```
dashboard（聚合层 · 无自有业务表）
      │ 只读 ORM / api
      ├─ device-pool
      ├─ element-locator
      ├─ case-manager
      ├─ test-runner
      ├─ report-generator
      └─ ai-assistant
```

**禁止**：仪表盘直接写其他 App 的表；跨模块写必须走对方 `api.py`。  
**禁止**：前端硬编码统计数字。

---

## 2. 功能清单

| 编号 | 功能名称 | 优先级 | 一句话描述 |
|:--:|------|:--:|------|
| F-01 | 平台统计 KPI | P0 | 设备/用例/元素/执行/智能体/报告聚合卡片 |
| F-02 | 执行趋势图 | P0 | 近 12 日成功/失败/新建用例 |
| F-03 | 近期任务面板 | P1 | 最近用例执行摘要与活跃运行 |
| F-04 | 活动时间线 | P1 | 跨模块最近事件 |
| F-05 | 快捷操作与模块导航 | P0 | 跳转各业务模块 |

---

## 3. 功能详细规格

### 3.1 F-01：平台统计 KPI

| 目标 | 衡量方式 | 目标值 |
|------|----------|:--:|
| 数据来源 | 全部来自 API | 100% |
| 设备口径 | 与设备列表可见状态一致 | ONLINE/BUSY 计入，隐藏 OFFLINE/DISCONNECTED |
| 加载失败 | 前端提示 | ElMessage / 空态，不白屏 |

**API**：`GET /api/dashboard/stats/` → `{ ok, data: { devices, cases, elements, runs, agents, reports, pass_rate, execution_chart, ... } }`

### 3.2 F-02：执行趋势图

展示近 12 日 `success` / `failed` / `new_cases` 序列；通过率 `pass_rate` 单独展示。

### 3.3 F-03 / F-04：任务与活动

| 端点 | 说明 |
|------|------|
| `GET /api/dashboard/stats/` | 含 `recent_tasks` |
| `GET /api/dashboard/activities/` | 最近活动列表 |

活跃运行摘要须经 `test_runner` 公开 API，禁止直接 import `_active_runs`（防火墙 #1）。

### 3.4 F-05：快捷操作

| 文案 | 路由 |
|------|------|
| 新建用例 | `/cases/new` |
| 执行测试 | `/runner` |
| 元素截图 | `/elements` |
| AI 对话 | `/ai-assistant` |
| 查看报告 | `/reports` |

---

## 4. API 一览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/dashboard/stats/` | 平台总览 |
| GET | `/api/dashboard/activities/` | 活动流 |
| GET | `/api/devices/stats/` | 设备摘要（可复用） |
| GET | `/api/cases/stats/` | 用例摘要（可复用） |

统一响应：`{"ok": true, "data": {...}}` / `{"ok": false, "error": "..."}`  
鉴权：JWT Bearer（与平台一致）。

---

## 5. 数据与依赖

- **自有表**：无（纯聚合）
- **上游只读**：`dp_devices` · `cm_test_definitions` · `el_elements`/`el_pages` · `tr_test_runs`/`tr_test_results` · `rg_reports` · `ai_agents`
- **下游**：无写依赖；导航到各业务模块

---

## 6. 验收标准

| # | 场景 | 期望 |
|---|------|------|
| AC-01 | 已登录访问 `/` 或 `/dashboard` | 进入仪表盘且 KPI 有数据或合法空态 |
| AC-02 | 断网/API 失败 | 有错误提示，页面结构仍在 |
| AC-03 | 设备池仅 OFFLINE 设备 | 仪表盘设备 total 与设备页可见口径一致 |
| AC-04 | 点击快捷操作 | 路由跳转正确 |
| AC-05 | 代码依赖检查 | 不跨 App import `service` / 内部 `_active_runs` |

---

## 变更记录

| 版本 | 日期 | 变更摘要 |
|------|------|----------|
| v1.0 | 2026-07-10 | 按前端 7 模块补齐仪表盘子 PRD；对齐 `apps/dashboard` 聚合端点 |
