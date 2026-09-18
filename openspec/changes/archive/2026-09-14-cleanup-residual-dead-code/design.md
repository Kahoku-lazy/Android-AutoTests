## Context

动机见 `proposal.md` - Why。这 5 项是 P0~P4 死代码复查的**最后一批**「声明了却没有消费方」的残留；与 P3 的区别是：P3 删的是设计令牌（CSS 自定义属性），本变更删的是选择器段、关键帧、JS 开关与组件 prop。

约束：每项都必须先证明「0 消费方」再删除；有任何一处可见变化就移出本变更。

## Goals / Non-Goals

**Goals:**

- 删掉 4 项可静态证明为死的代码（`.agent-card` 选择器段 · `no-bg-anim` 开关 · `toastSlideDown`/`.el-message--top` · `AppTabs` 的 2 个空 prop 及其传参）
- 同步 `frontend/AGENTS.md` 中描述这些死项的三处文字（否则文档继续把死开关写成「已知缺口」）

**Non-Goals:**

- 不动 `gap:14px`（6 处，可见变更，需浏览器核验）
- 不动任何在用样式/组件行为：`--app-green`/`--app-blue`（`motion.css` 的 `.wb-loader` 在用）、`.el-message` 皮肤、`.el-card:not(.ac-card)` 悬浮过渡
- 不重构 `AppTabs`（不做 prop 改名、不加新特性）

## Decisions

### 1. `.agent-card`：只删选择器段，保规则

- **选择**：删 `.wb-shell .agent-card,` 与 `.wb-shell .agent-card:hover,` 两行
- **理由**：该规则是「卡片悬浮过渡」，活选择器是 `.el-card:not(.ac-card)`；删掉死段后规则语义不变
- **备选**：整条规则删除 —— 会连带删掉在用过渡，否决

### 2. `no-bg-anim`：删 JS 开关并同步 AGENTS.md

- **选择**：删 `router.ts` 的增删块，并删掉 AGENTS.md L0 §⑤ 该行与 §⑥ 的缺口条目
- **理由**：0 个 CSS 消费方意味着这个「/login 禁用背景动画」的优化从未生效；文档把它列为「已知缺口」会让后来者以为存在一个待修的开关
- **风险**：外部用户脚本理论上可依赖该 class —— 全仓扫描 0 引用，且该 class 无任何样式效果，判定为可接受

### 3. `toastSlideDown` / `.el-message--top`：两条一起删

- **选择**：删关键帧定义与使用它的那一条规则
- **理由**：`el-message--top` 不是 EP 产出的 class（EP dist CSS 0 命中），本仓也没有 `customClass` 挂它 → 规则不可达；关键帧只被这条规则引用，必须成对删除
- **备选**：保留关键帧「以备后用」—— 死代码，否决

### 4. `AppTabs` 的空 prop：删 prop + 删传参 + 收口文档

- **选择**：删 `leafAnimation` / `shadow` 声明与类名计算，删 `report-generator` 的 2 行传参，删 `useFilterTabs` JSDoc 示例中的 2 个属性，并改写 AGENTS.md 的注意条目
- **理由**：`ac-tabs--leaf` / `ac-tabs--shadow` 全仓无 CSS 规则 → prop 是纯噪音；留着会误导后续页面继续白传
- **顺带纠正**：AGENTS.md 原写「3 个模块正在白传」，实测只有 `report-generator` 一处

### 5. `gap:14px` 移出本变更（需可见性核验）

- **选择**：不在本变更收敛裸 px 间距
- **理由**：间距刻度为 `--app-space-xs/sm/md/lg`（4/8/12/16…），**没有 14px**；把它改成 md(12) 或 lg(16) 会产生 2px 视觉变化，属「可见变更」，不能以「纯删除」的口径关单；本环境无登录态，无法做浏览器核验
- **处理**：保留现状并在报告中登记为待定项，由用户决定是否接受 2px 变化

### 6. 验证口径：静态 0 消费 + 门禁，不做浏览器核验

- **选择**：每项以「关键字全仓扫描 0 命中/仅剩声明处」为依据；跑 typecheck / 构建 / `vue-frontend-check`；不做浏览器目视
- **理由**：4 项删除都不参与任何计算样式或运行分支（`.agent-card` 不被匹配、`no-bg-anim` 无样式、`el-message--top` 不可达、`ac-tabs--*` 无规则）

## 模块防火墙自检

- 跨 App import：不涉及（前端内部清理）
- 禁止跨 App import service/runner/consumer/state_machine：不涉及
- 所有 INSERT/UPDATE/DELETE 收敛到 api.py：不涉及（无写操作）
- 前端不直连数据库；仪表盘不做写操作：不涉及

## Risks / Trade-offs

- [删掉在用选择器] → `.agent-card` 段与 `.el-card:not(.ac-card)` 段同规则，只删前者；`ac-tabs` 基础类保留（`.ac-tabs` 有 10 处 CSS）
- [删掉路由侧优化导致背景动画空转] → 该优化从未生效（0 消费方），删除不改变任何实际开销
- [文档与代码再次漂移] → 同一变更同步 AGENTS.md 三处
- [AGENTS.md 并发写入] → 编辑前重新读取（该文件正被并行工作修改）
- [`gap:14px` 被遗忘] → 已登记进 proposal/design/tasks 与结单报告，作为显式待定项

## Migration Plan

1. 逐项复核 0 消费方（5 项）
2. 按文件删除：`motion.css` → `router.ts` → `style.css` → `AppTabs.vue` → `report-generator/index.vue` → `useFilterTabs.ts`
3. 同步 `frontend/AGENTS.md` 三处
4. `npm run typecheck` + `npx vite build --mode development` + `vue-frontend-check`
5. 回滚：`git checkout` 6 个源码文件 + 1 个文档，无数据迁移
