## Context

11 处 `required` 的兜底来源（逐处读代码得出）：

| 文件 | 字段 | 现有兜底 |
|------|------|----------|
| `case-manager/ProjectList.vue:110` | 项目名称 | composable `useProjects.ts:36-40` 的 `ElMessage.warning` |
| `workflow/PrototypeList.vue:110` | 原型名称 | composable `usePrototypes.ts:48-52` 的 `ElMessage.warning` |
| `device-inspector/SaveToElementsDialog.vue:112,128` | 选择页面 / 页面名称 | 组件 `confirm()` 的两处 `ElMessage.warning` |
| `element-locator/LocatorFilePanel.vue:213,226,233,246` | 名称 / 定位值 / 名称 / URL | `saveWeb` / `saveApi` 的 `ElMessage.warning` |
| `ai-assistant/EvaluatorTab.vue:512` | 试卷名称 | `saveBank()` 的 `ElMessage.warning` |
| `ai-assistant/components/TaskBoard.vue:68` | 任务目标 | 提交按钮 `:disabled="!form.goal.trim()"` |
| `ai-assistant/components/AgentBasicInfo.vue:22` | 名称 | 父组件 `AgentDetail.save():123-129` 的显式默认（线路名 → 「平台小助手」） |

`LocatorFilePanel` 的 4 处分布在**两套互斥表单**上（`file.kind === 'web_element'` 与 else 分支），需要两个独立 ref 与两套 rules。

## Goals / Non-Goals

**Goals:**

- 把 10 处必填从「临时 Toast / 按钮 disabled」升级为 EP 字段级校验（`:rules` + `validate()`）
- 让「必填星号」与实际校验一致，消除误导性 UI
- 在 spec 与速查中把缺口从「11 处」更新为「10 处已接入 + 1 处登记例外」

**Non-Goals:**

- 不改 `AgentBasicInfo.vue`（空名有默认兜底，加规则会改行为）
- 不删除 composable 里的第二层空值守卫（`addProject` / `addPrototype`）
- 不给其余 35 个非必填 `el-form-item` 补规则
- 不改任何表单的字段集 / 布局 / 提交载荷结构

## Decisions

**D1 · 校验失败改用字段内联提示，替换原 Toast**

spec 场景明确要求「在该字段上展示 Element Plus 校验提示」。若同时保留 Toast，同一错误会提示两次。因此把「空值」这一类 Toast 移除，交由 `:rules` 呈现；其它错误（接口失败等）的 Toast 一律保留。

**D2 · `AgentBasicInfo` 不接入 `:rules`，登记为例外**

父组件对空名有显式默认（`payload.name = (routeName || '').trim() || '平台小助手'`），即「空名 = 取默认名」是既有产品行为。加 `:rules` 会把它变成「空名 = 禁止提交」，属行为变更而非缺陷修复；按「只碰必须碰的」保留现状并登记。

**D3 · 未接入校验的表单保留原兜底**

`TaskBoard` 的提交按钮已有 `:disabled`，接入 `:rules` 后两者并存：按钮仍禁用，Enter 等路径由 `validate()` 兜住。不删 `:disabled`（它是首屏可见的即时反馈）。

**D4 · 每套表单独立 ref，不用一个 ref 管两个互斥表单**

`LocatorFilePanel` 的两套表单互斥渲染（`v-if` / `v-else`），各建一个 `ref` 与 rules 对象，避免「另一套未挂载时 ref 为 null」的分支判断。

## 模块防火墙自检

- 跨 App import：不涉及。只改 `frontend/src` 内部
- 禁止跨 App import service / runner / consumer / state_machine：不涉及
- 所有 INSERT / UPDATE / DELETE 收敛到各 App 的 api.py：不涉及，无后端写操作
- 前端不直连数据库；仪表盘不做写操作：不涉及，不改任何 `api.ts` / HTTP 调用
- 新增跨模块依赖：无（`el-form` 的 `rules` / `FormInstance` 均来自既有 element-plus）

## Risks / Trade-offs

- [`validate()` 返回 Promise 且 reject，忘记 catch 会产生未处理拒绝] → 统一用 `try { await ref.value?.validate() } catch { return }` 结构，并把 `ref.value` 判空包进去（对话框未挂载时 ref 为 null）
- [错误提示从 Toast 变内联，属可见行为变化] → 已在 spec 场景中写明，并按「有意统一」交付；浏览器目视登记为待补
- [移除空值 Toast 后，若某表单的 rules 未覆盖到该字段，用户将失去提示] → 逐处核对 `prop` 与 rules 的字段名一致，并以 typecheck + 人工复核双确认
- [composable 守卫成为不可达分支] → 保留为第二层防御（未来其他调用方仍受保护），在设计文档登记而非删除

## Migration Plan

- 无数据迁移；回滚为 revert 本变更提交
- 验证顺序：`vue-tsc --noEmit`（改动文件零错误）→ `vue-frontend-check` 静态扫描 → 6 个表单的浏览器目视（本环境待补）
