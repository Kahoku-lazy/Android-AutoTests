## Context

`LoginErrorOverlay.spec.ts` 现有 stub 与断言的错配，实测证据（运行该 spec 的输出）：

| 现象 | 证据 |
|---|---|
| 组件未解析 | `[Vue warn]: Failed to resolve component: el-dialog`、`el-button` |
| 断言目标不存在 | 测试 5/6 报 `Cannot call trigger on an empty DOMWrapper`（`.el-dialog` / `.el-overlay`） |
| 具名插槽不渲染 | 测试 3 找不到 `[data-testid="login-error-dismiss"]` —— 它位于 `<template #footer>`，而未解析元素只渲染默认插槽 |
| 另有 3 条「假通过」 | 测试 1（visible=false 不渲染）与测试 4（visible=false ESC 不触发）在组件未渲染时恒真；测试 2 靠默认插槽内容碰巧通过 |

工程约束：`vite.config.js` 的 `test.projects` **没有 `setupFiles`**，模块清单由 `tests/module-scan.mjs` 生成；同目录两个已通过的 spec（`LoginCard.spec.ts` / `AccountSwitchPrompt.spec.ts`）都自带内联 `global.stubs`。`vite.config.js` 注释明确「单测用 stub 替换 el-*，避免 Element Plus 按需 CSS 拖垮 Vitest」。

## Goals / Non-Goals

**Goals**：让该 spec 的 6 条断言恢复可达并按项目约定通过；顺带把「遮罩必须跳出 transform 包含块」这一 L5 约束在单测层留下可观察的守卫。

**Non-Goals**：不注册真实 EP；不改生产组件；不把断言改弱以迁就 stub；不给全仓建统一 `setupFiles`（现有约定是按 spec 自带，破坏它属于越界改造）。

## Decisions

**D1：补内联 stub，而不是注册真实 Element Plus 插件。**

| 方案 | 结论 | 理由 |
|---|---|---|
| 补内联 `el-dialog` / `el-button` stub（**采用**） | ✅ | 与同目录两个 spec 的既有约定一致；不引入 EP 全量 JS；`vite.config.js` 注释已表明单测走 stub 是有意选择 |
| `setupFiles` 里 `app.use(ElementPlus)` | ❌ | 违背既有口径；把 6 条用例的失败换成整套单测的启动成本上升 |
| 把断言改回自建遮罩时代的 DOM | ❌ | 与 `frontend-l5-overlay`「覆盖层统一走 EP」冲突，属回退 |

**D2：stub 只模型化组件真正依赖的 EP 契约，不追求像素级复刻。**

组件对 `el-dialog` 的依赖只有四项，stub 逐一对齐：`modelValue` 控制挂载、`.el-overlay`（遮罩）+ `.el-dialog`（对话框）两层类名、默认插槽与 `footer` 具名插槽、ESC 与点遮罩均 emit `update:modelValue(false)`。

**D3：不在 stub 里模拟 Teleport，改为断言 `append-to-body` prop。**

真实 EP 遮罩点击用的是 mousedown + mouseup 组合判定（`useSameTarget`），而 `append-to-body` 的效果是「遮罩尺寸 = 视口」，两者都属**布局/浏览器**层面，jsdom 无量layout能力，强行模拟只会得到假精度。因此：
- stub 用 `@click` 表达「点遮罩关闭」的**语义契约**（组件未设 `close-on-click-modal="false"`，语义就是可点遮罩关闭，符合 `frontend-l5-overlay`「纯展示弹层保持默认」）；
- `append-to-body` 用 `findComponent(...).props('appendToBody')` 断言——这是该约束在单测层唯一可观察的契约；
- 真实尺寸证据继续由 `temps/login-layer-map/` 的 Playwright 实测承担（`overlayRects` / `overlayControl`）。

**D4：保留 `stubs: { transition: false }`，`teleport: true` 变为无害冗余。**

stub 内不再有 Teleport，故该 stub 无效但无害；保留可避免未来实现回退到 Teleport 时断言突然失效。`transition: false` 仍需保留以避免过渡态影响断言时序。

## Risks / Trade-offs

- [stub 保真度不足，掩盖真实 EP 行为差异] → 已登记 stub 覆盖边界（只覆盖组件依赖的四项契约）；浏览器层回归由 Playwright 实测 bundle 承担，二者分工在 tasks 中写明
- [新增的 `appendToBody` 断言与 EP prop 名耦合，EP 大版本改名会红] → 可接受：该断言与 L5 需求强绑定，改名时**应当**被提醒复核；若将来 EP 移除该能力，需回到 design 重选方案
- [其他 spec 将来复制这段 stub 造成重复] → 本次只有这一处需要；抽公共 helper 属过度设计，登记为 Open Question，第 3 处出现时再抽

## Migration Plan

无。测试文件单点改动，回滚 = 还原该 spec。

## Open Questions

是否需要把这份 `el-dialog` stub 提炼到 `tests/helpers/` 供后续 L5 组件复用？当前仅 1 处消费，按「不为单一消费方造抽象」暂不抽。
