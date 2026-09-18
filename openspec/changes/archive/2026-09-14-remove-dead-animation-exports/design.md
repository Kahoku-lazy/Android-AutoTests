## Context

动机见 `proposal.md` - Why。判定方法（本次核心）：**以「真实代码 import 的可达闭包」为准**，而不是「名字在文本里出现过」。

- 解析 `animations.ts` 的 35 个顶层声明，建立**文件内调用图**（如 `pressFeedback → buttonPress, particleBurst`）
- 收集所有 `import { … } from '…/animations'`（含测试），得到外部入口 6 个
- 从入口做传递闭包 → 可达 8 个；不可达 27 个

关键排除项（名字出现但**不是**本模块调用）：

| 名字 | 出现处 | 实际是什么 |
|------|--------|-----------|
| `pulse` | `TaskResultPanel.vue:173,195` | 该组件**本地的 `@keyframes pulse`**，与导出无关 |
| `countUp` | `frontend/tests/dashboard/p2/README.md` | 测试说明文档里的叙事文字 |
| `typewriter` | `dev_docs/项目笔记/平台前端主题参考模版/*.html` | 主题原型页里自带的独立实现 |
| `particleBurst` | `frontend/AGENTS.md` L0 §⑤ | 文档登记（本次随之删除该行） |

约束：保留项的行为不得改变；只删「无任何调用路径」的声明。

## Goals / Non-Goals

**Goals:**

- 把 `animations.ts` 收敛为「只有真在用的动效工具」
- 同步清理它对 `AGENTS.md` L0 §⑤ 的登记影响（`particleBurst` 是已登记的 L0 写入点）

**Non-Goals:**

- 不改 6 个在用函数的签名与行为
- 不重构 `runMotion` / `prefersReducedMotion` 的 reduced-motion 机制
- 不动 `dev_docs` 下的主题原型 HTML（自带独立实现，属参考素材）
- 不做 P3（死令牌）与 `.agent-card` 等小项

## Decisions

### 1. 判据 = 可达闭包，不是字符串命中

- **选择**：从真实 import 出发做传递闭包；可达即保留，不可达即删
- **理由**：字符串命中会因 CSS 关键帧、文档叙述、原型页而误判（见 Context 表）；反之闭包法能正确处理「函数被删函数调用」的整簇（`pressFeedback → buttonPress → …`）
- **备选**：按 `frontend/src` 名字计数 —— 会把 `particleBurst`（仅文档提及）判为在用，被否决

### 2. 整簇删除，不保留「可能有用」的工具

- **选择**：27 个全部删除，包括看起来通用的 `slideIn` / `contentSwap` / `cardTilt` 等
- **理由**：AGENTS 规则 8「抽 shared 组件等第二个真实消费方；单处使用不提前抽象」—— 0 消费的通用工具正是该规则要清的对象；需要时从 git 历史恢复即可
- **备选**：保留一批「常用动效」备查 —— 与规则 8 相悖，且会把死代码重新积累起来，否决

### 3. 保留 `runMotion` / `prefersReducedMotion`

- **选择**：两者作为内部 helper 保留（被 6 个在用导出依赖）
- **理由**：reduced-motion 短路与 `duration: 0` 降级是 `align-frontend-motion` 的成果，必须继续覆盖在用函数

### 4. 随之移除 `createTimeline` 导入

- **选择**：`import { animate, stagger, createTimeline }` → `import { animate, stagger }`
- **理由**：`createTimeline` 仅被 `sequentialHighlight` / `fadeSwap` 使用，两者均删；留着会产生未使用导入（lint/typecheck 噪声）

### 5. 文档同步：删掉 `particleBurst` 的 L0 登记行

- **选择**：从 `frontend/AGENTS.md` L0 §⑤ 的运行时写入表中移除 `shared/animations.ts:158（particleBurst）` 一行
- **理由**：该行描述的是「粒子由 `body.appendChild` 写入、`onComplete` 清理」；函数删除后该登记不再成立，留着即文档失真

## 模块防火墙自检

- 跨 App import：不涉及（纯前端工具库）
- 禁止跨 App import service/runner/consumer/state_machine：不涉及
- 所有 INSERT/UPDATE/DELETE 收敛到 api.py：不涉及（无写操作）
- 前端不直连数据库；仪表盘不做写操作：不涉及

## Risks / Trade-offs

- [删掉将来想用的动效工具] → 可从 git 历史恢复；符合规则 8 的准入判据（第二个真实消费方）
- [误删在用函数会立刻打断功能] → 已用 import 闭包 + 测试文件纳入扫描范围；删后 `typecheck`（会报未定义/未使用导入）+ 构建双验
- [文档与实现再次不一致] → 同一变更内同步 L0 §⑤；并在 tasks 中要求 grep 复核 `particleBurst` 残留
- [测试引用被误删] → `staggerReveal` 被 2 个测试文件 import，已列入保留集

## Migration Plan

1. 复核可达闭包（35 → 可达 8 / 不可达 27）
2. 以保留集重写 `animations.ts`（同时收紧 animejs 导入）
3. 同步 `frontend/AGENTS.md` L0 §⑤
4. `npm run typecheck` + `npx vite build --mode development` + `vue-frontend-check`
5. 回滚：`git checkout` 一个 `.ts` + 文档，无数据迁移
