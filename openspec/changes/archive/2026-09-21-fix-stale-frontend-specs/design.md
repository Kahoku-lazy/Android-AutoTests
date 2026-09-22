## Context

- 这 5 个红色 spec 文件在 `git status` 中是**干净**的（tracked + 无改动），说明它们与 HEAD 代码的落差是**提交时落下**的，不是并行开发中的半成品；因此修它们不会与别人的在飞改动冲突。
- 三处上游决定的证据：
  - `51e4809e` 提交信息：「refactor(api): /api 路由统一带尾斜杠，关闭 APPEND_SLASH 并删除容错中间件」——`device-pool/api.ts` 8 个端点全部带尾斜杠（`api.ts:6,17,23,27,31,35,39,43,47`）。
  - `git log --diff-filter=D -- .../ModuleNavigator.vue` → `e51acebd`；`grep ModuleNavigator frontend/src` 只剩 `WorkbenchHeader.vue:5` 的一句注释。
  - `apps/dashboard/views.py:124-151` 实际返回 `devices:{online,total}`、`cases:{total,enabled,breakdown}`、`elements:{total,pages,type_breakdown}`、`workflow`（仅 total）、`execution_summary`、无 `reports`；`shared/types/dashboard.ts` 与之逐字对应，且 HEAD 版本同样没有 `trend/reports/page_flows/new_cases`。
  - `DashboardView.logic.ts:34-36` 的 `ELEMENT_BREAKDOWN` 只剩 android，注释「Web/API 两域随元素定位下线」，与归档 change `2026-09-21-remove-element-locator-web-api` 一致；`apps/dashboard/views.py:84` 同一句注释。

## Goals / Non-Goals

**Goals:**

- `npx vitest run` 全绿，且不靠 `skip`/`todo`/改 `include` 遮住问题
- 保住的覆盖不退：逐字段映射、空值回退、部分缺字段回退、分页越界收敛都必须仍有断言
- `npx vue-tsc --noEmit` 中由这 4 个 spec 造成的类型报错消失

**Non-Goals:**

- 不恢复任何已删除的产品能力（组件 / DTO 字段 / 元素域）
- 不改 `src/**`、`apps/**`
- 不改 `PRIORITY_TEMPLATE.md` 的分类约定

## Decisions

**D1 删 `ModuleNavigator.spec.ts`，而不是把它标记 `skip`**
依据：被测文件 HEAD 已不存在（`git cat-file -e HEAD:.../ModuleNavigator.vue` 失败），`src/` 中 0 引用。一个 import 就解析失败的文件永远无法变绿，`skip` 只是把失败藏起来（违反「错误不应默默忽略」）。将来若组件回归，测试应随组件一起回来。

**D2 对齐断言到真实 DTO，而不是删除这 4 个用例**
依据：用例意图（「完整数据逐字段映射」「空对象：全部回退默认值」「部分字段缺失：缺失项回退，存在项保留」）依然成立且必要，只是字段清单过期。保留用例、更新字段集，比删掉覆盖更好；也不引入新字段（不发明需求）。

**D3 fixture 去掉多余字段（`trend`/`reports`/`pass_rate`/`new_cases` 等）**
依据：`makeRaw()` 标注返回 `DashboardRawData`，多余字段是**对象字面量多余属性**，本身就是 `vue-tsc` 报错源；保留它们等于在 fixture 里继续声明不存在契约。

**D4 device-pool 分页期望改为 3，而不是把 `DEFAULT_PAGE_SIZE` 改回 10**
依据：`constants.ts:45-46` 的注释「分页配置（只有 5；默认 5）」与 `PAGE_SIZE_OPTIONS = [5]` 是有意的产品决定（设备表按 5 行撑高），测试 106-110 行的收敛断言本就按 5 成立。改产品常量才是越界。

**D5 同步两个 README 登记表**
依据：`tests/README.md` 的模块注册表按「P0 文件 / P1 文件」计数，dashboard 当前登记 P1=4、说明含「导航」；删文件后不改就又是一处失真。

## 模块防火墙自检

- 跨 App import：零新增（只动 `frontend/tests/**` 与 2 个测试 README）
- 前端 HTTP 出口 / 端点：不变
- 共享层 / tokens：不变
- 后端 / 迁移：零改动

## Risks / Trade-offs

- 删掉 `ModuleNavigator.spec.ts` 会丢掉「9 张模块卡 / 统计数值注入 / 点击跳转」的覆盖——但这些覆盖的对象已不在产品里，属**已失效覆盖**而非丢失保障；若该组件以新形态回归（例如并入 `StatsCard` / `TaskResultPanel`），需按新形态重写。
- `useDashboardStats.spec.ts` 的断言变少（例：不再断言 `reports.total`）是产品字段消失的必然结果；本单不补新字段，避免「顺手发明需求」。
