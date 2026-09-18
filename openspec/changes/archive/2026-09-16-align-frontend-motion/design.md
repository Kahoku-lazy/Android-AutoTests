## Context

动机见 `proposal.md` - Why。相关现状（已核对代码）：

- `frontend/src/shared/styles/motion.css:64-70` 定义 `.fade-slide-*`：时长/缓动为硬编码 `0.28s ease`，位移为裸值 `16px/-10px`；全前端无消费方。
- `frontend/src/App.vue:18-22` 主区为 `<router-view>` + `<keep-alive :max="5">`，无 `<transition>`。
- `frontend/src/shared/styles/tokens.css:323-327` 已有 `--app-ease` / `--app-spring` / `--app-duration-fast|--app-duration|--app-duration-slow`；间距令牌 `--app-space-md`=16px、`--app-space-sm`=8px。
- `frontend/src/shared/animations.ts` 是 animejs 封装，现有 5 个消费方；该文件无任何 `prefers-reduced-motion` 判断（项目内 7 处降级都在模块 CSS，不覆盖 JS 编排）。
- `frontend/src/shared/dev/scroll-guard.ts:50-54` 以 `.main-content__body > *` 取页面根，用于开发环境滚动自检。
- 技能口径：`.agents/skills/doodle-craft/references/tokens.md` §1.9 规定「路由切换、弹窗进出 0.25s（`--app-duration-slow`）」。

约束：不改侧栏结构、不改模块业务组件与页面布局；不得破坏「视口固定 + 内层滚动」。

## Goals / Non-Goals

**Goals:**

- 主区路由切换有过渡，且时长/缓动/位移全部走既有令牌
- CSS 过渡与 JS 编排动效都遵守 `prefers-reduced-motion`
- 滚动契约（`scroll-guard` 页面根）与 `keep-alive` 缓存契约不变

**Non-Goals:**

- 不改各模块内既有入场动效、图表动效的视觉设计
- 只为单处过渡新增全局动效令牌
- 不改 L0 滚动策略、不改侧栏、不改路由表

## Decisions

### 1. 包裹顺序：`<transition>` 在外，`<keep-alive>` 在内

- **选择**：`<router-view v-slot="{ Component }"><transition name="fade-slide" mode="out-in"><keep-alive :max="5"><component :is="Component" :key="route.path" /></keep-alive></transition></router-view>`
- **理由**：Vue 3 的推荐顺序；`<transition>` 不产生 DOM 节点，因此 `scroll-guard` 的 `.main-content__body > *` 仍命中页面根，滚动自检不受影响
- **备选**：`<transition>` 放进 `<keep-alive>` 内 —— 无法对路由切换整体生效，排除

### 2. 过渡模式：`mode="out-in"`

- **选择**：`out-in`，一次路由切换总时长 ≈ 2 × 0.25s
- **理由**：主区页面是整块流式布局，离场与进场同时进行会重叠，引发布局跳动与滚动条抖动；`out-in` 语义清晰、实现最简
- **备选**：无 `mode` 交叉淡入（总时长 ≈ 0.25s）—— 需对离场页做绝对定位，与 `.main-content__body` 滚动容器冲突，风险高，放弃
- **影响**：体感比规范的单段 0.25s 慢；若验收嫌慢，只调 `motion.css` 一处的时长引用（纯调参，不动结构和 spec）

### 3. 令牌对齐，消灭硬编码

- **选择**：`transition: opacity/transform var(--app-duration-slow) var(--app-ease)`；`enter-from: translateY(var(--app-space-md))`（16px）；`leave-to: translateY(calc(var(--app-space-sm) * -1))`（-8px）
- **理由**：符合 doodle-craft 核心原则「令牌，不硬编码」；原 `10px` 裸值改用间距令牌派生，方向语义不变、量级微调 2px
- **备选**：为位移新增全局令牌 —— 只为单处过渡新增全局令牌不划算，放弃

### 4. reduced-motion：CSS 层降级

- **选择**：在 `motion.css` 加 `@media (prefers-reduced-motion: reduce) { .fade-slide-enter-active, .fade-slide-leave-active { transition: none } }`
- **理由**：与项目内既有 7 处降级写法一致，改动集中在一个文件

### 5. reduced-motion：JS 层短路

- **选择**：在 `animations.ts` 内加模块私有 `prefersReducedMotion()`（带 `typeof window` 保护），各导出函数入口短路：返回 `void` 的函数（如 `countUpFormatted`）直接写终值后 `return`；返回 animejs 句柄的函数以 `duration: 0` 完成，保持返回类型
- **理由**：公开签名与返回类型不变（AGENTS.md 规范 1.6），5 个消费方零改动
- **备选**：在各消费方各自判断 —— 5 处重复且易漏，放弃

## 模块防火墙自检

- 跨 App import：不涉及（纯前端壳层与共享工具）
- 禁止跨 App import service/runner/consumer/state_machine：不涉及
- 所有 INSERT/UPDATE/DELETE 收敛到 api.py：不涉及（无写操作）
- 前端不直连数据库；仪表盘不做写操作：不涉及

## Risks / Trade-offs

- [out-in 总时长约 0.5s 偏慢] → 时长只有一处引用，可快速调参；spec 不锁死总时长
- [过渡影响滚动位置或产生双滚动条] → `out-in` 无重叠，且不改 `.main-content__body` 滚动口径；目视验证固定视口工作台页
- [JS 短路破坏调用方] → 保持签名与返回类型不变，逐消费方核对 + `npm run typecheck`
- [被 keep-alive 缓存的页面再次进入会重播 enter] → 属 Vue 默认行为，可接受，不额外处理
- [无 window 环境下判定 reduced-motion 报错] → `animations.ts` 已是浏览器侧工具，判定处加 `typeof window` 保护

## Migration Plan

1. `motion.css`：对齐令牌 + 加 reduced-motion 降级块
2. `App.vue`：接线 `<transition>`
3. `animations.ts`：加 reduced-motion 短路
4. `cd frontend && npm run typecheck`，并本地目视：路由切换、登录页、至少一个固定视口工作台页
5. 回滚：移除 `<transition>` 包裹与降级块即可，无数据迁移
