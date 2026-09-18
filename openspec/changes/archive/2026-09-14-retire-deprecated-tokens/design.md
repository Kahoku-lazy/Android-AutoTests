## Context

动机见 `proposal.md` - Why。P3 全量分组（122 个，按 `tokens.css` 段）：

| 批 | 段 | 个数 | 备注 |
|---|----|:--:|------|
| **①** | `模块色（@deprecated 旧命名）` | 8 | 本变更 |
| **①** | `@deprecated 旧色（待收敛）` | 23 | 本变更（同段另 6 个仍在用 → 保留） |
| ② | `模块专属色 · AI Assistant` | 18 | 后续 |
| ② | `模块专属色 · Case Manager` | 38 | 后续 |
| ② | `模块专属色 · 仪表盘统计卡` | 12 | 后续；`.agents/skills/doodle-craft/references/tokens.md` §1.11 有文档 |
| ③ | 中性色 / 阴影 / 杂项 / 字号段杂项 | 23 | 后续；`doodle-craft` 与 `prototype-design` 技能有文档 |

本批 31 个的死因都写在注释里（旧命名 / 旧主题 / 待收敛），因此删除符合既有意图；其余批次涉及模块专属色段与技能文档正文，需逐批讨论。

约束：同段**仍被消费**的 6 个令牌必须保留；不改任何消费端代码。

## Goals / Non-Goals

**Goals:**

- 清掉两族显式 `@deprecated` 的死令牌（31 个）
- 修正 `doodle-craft` 技能中关于 `--app-module-*` 的失效说明

**Non-Goals:**

- 不做批次 ②（模块专属色 68 个）与批次 ③（杂项 / 待收敛 23 个）
- 不动 `--el-*` 覆盖层（由 EP 全量样式消费）
- 不改任何 `var()` 消费端

## Decisions

### 1. 先做显式 `@deprecated` 的两族

- **选择**：`--app-module-*`（8）+ `@deprecated 旧色`（23）
- **理由**：这两族的段注释已经宣告「新代码禁用 / 待收敛」，删除是执行既有意图而非新决策；批次 ②/③ 里的模块专属色仍可能被将来复用，需单独讨论
- **备选**：一次性删 122 个 —— diff 过大、且会与 `doodle-craft` / `prototype-design` 技能文档批量冲突，否决

### 2. `@deprecated 旧色` 段**按令牌粒度**收缩，不整段删

- **选择**：保留 `--app-green` · `--app-blue` · `--app-accent-blue` · `--app-accent-purple` · `--app-ink` · `--app-ink-muted`
- **理由**：这 6 个在当前代码中**仍有 `var()` 消费**（如 `--app-ink-muted` 被 dashboard/device-pool/report-generator 使用）；整段删会立刻打破样式
- **备选**：整段删除 —— 会引入可见回归，否决

### 3. 令牌已被「非 `var()`」方式读取？已排查

- **选择**：确认全仓无 `getPropertyValue('--<token>')` 读取
- **理由**：`var(--x)` 扫描无法覆盖 JS 读 CSS 变量的路径；实测全仓只有 `useSidebarResize.ts` 的 `setProperty('--side-w')`（写入，且不在本批）→ 本批判据成立

### 4. 文档同步到 `doodle-craft/SKILL.md`

- **选择**：删除第 61 行「另有语义色 `--app-module-*` 系列…改模块色时两处同步」
- **理由**：该句是本批唯一会失真的文档表述（`html-report/PROMPT.md` 里的 `--text-secondary` 是它自己 `:root` 的同名令牌，与本次无关，不动）

### 5. 验证口径：静态 0 消费 + 门禁，不做浏览器核验

- **选择**：以「31 个令牌全仓 `var()` 消费 = 0（且无 `getPropertyValue` 绕过）」作为删除依据；跑 typecheck / 构建 / `vue-frontend-check`；**不做浏览器目视**
- **理由**：未被引用的自定义属性不参与任何计算值，删除对渲染恒等 —— 比「目视无异常」更强

## 模块防火墙自检

- 跨 App import：不涉及（纯前端令牌）
- 禁止跨 App import service/runner/consumer/state_machine：不涉及
- 所有 INSERT/UPDATE/DELETE 收敛到 api.py：不涉及（无写操作）
- 前端不直连数据库；仪表盘不做写操作：不涉及

## Risks / Trade-offs

- [误删仍在用的令牌] → 逐令牌做 `var()` 全仓计数；同段仍在用的 6 个明确保留
- [令牌通过 JS 读取] → 已排查 `getPropertyValue` / `setProperty`，仅 `setProperty('--side-w')` 且不在本批
- [技能文档与实现不一致] → 同一变更同步 `doodle-craft/SKILL.md`
- [批次 ②/③ 继续时重复劳动] → 分组表已落 design，后续批次按表推进

## Migration Plan

1. 复核 31 个 0 消费 + 同段 6 个仍消费
2. 删 `--app-module-*` 段；收缩 `@deprecated 旧色` 段
3. 同步 `doodle-craft/SKILL.md`
4. `npm run typecheck` + `npx vite build --mode development` + `vue-frontend-check`
5. 回滚：`git checkout` 一个 `.css` + 一个 `.md`，无数据迁移
