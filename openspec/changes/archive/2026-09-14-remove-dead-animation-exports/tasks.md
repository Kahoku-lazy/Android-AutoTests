## 1. 复核可达闭包

- [x] 1.1 复核「6 个在用导出 + 2 个内部 helper」与「27 个不可达声明」，并确认 `pulse`（本地 @keyframes）/ `countUp`（测试 README）/ `typewriter`（原型 HTML）/ `particleBurst`（AGENTS 文档）均为**非代码调用**；验证：结论与 design §Context 表一致

## 2. 重写 animations.ts

- [x] 2.1 以保留集重写 `frontend/src/shared/animations.ts`：保留 `prefersReducedMotion` / `runMotion` / `countUpFormatted` / `sidebarNavEnter` / `staggerReveal` / `selectPop` / `iconBounce` / `loadingDots`，删除其余 27 个声明；验证：文件行数约 70 行，导出数 = 6
- [x] 2.2 收紧 animejs 导入为 `{ animate, stagger }`（移除 `createTimeline`）；验证：文件内不再出现 `createTimeline`
- [x] 2.3 复核在用的 6 个函数保持原实现：保留段是**按行号切片逐行复制**（取自本变更 apply 前的文件读取结果，行号 22-50 / 117-119 / 165-167 / 263-270 / 272-275 / 282-284），非重写；验证：新文件 CR=0（LF），且 `typecheck` + 构建通过。注：`git show HEAD` **不是**有效基线（HEAD 早于未提交的 `align-frontend-motion` 改动，252 行 vs 302 行）

## 3. 文档同步

- [x] 3.1 从 `frontend/AGENTS.md` L0 速查 §⑤ 的运行时写入表中移除 `shared/animations.ts:158（particleBurst）` 一行；验证：`rg "particleBurst" frontend` 0 命中

## 4. 门禁与静态验证

- [x] 4.1 运行 `cd frontend && npm run typecheck`；验证：无本变更引入的新错误（既有无关报错需注明）
- [x] 4.2 构建校验 `npx vite build --mode development`；验证：构建成功
- [x] 4.3 用 `vue-frontend-check` 技能过一遍前端门禁；验证：本次为纯删除（无新增样式/逻辑），逐项记录无新增违规
- [x] 4.4 静态证明复核：对 27 个删除名做全仓 `rg`，确认除 `P2 变更文档` 与 `dev_docs` 原型素材外无代码引用；验证：结果与 design 判定一致
