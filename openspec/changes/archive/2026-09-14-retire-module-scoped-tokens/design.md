## Context

动机见 `proposal.md` - Why。P3 死令牌按 `tokens.css` 段落分三批推进，本变更做第二批：

| 批 | 段 | 个数 | 状态 |
|---|----|:--:|------|
| ① | `模块色（@deprecated 旧命名）` + `@deprecated 旧色` | 31 | 已归档 `2026-09-14-retire-deprecated-tokens` |
| **②** | `模块专属色 · AI Assistant` + `· Case Manager` + `· 仪表盘统计卡` | **68** | 本变更 |
| ③ | 中性色/阴影/字号/独立区（`--app-bg-warm` `--app-glow-*` `--app-font-size-*` `--font-display` `--doodle-*` 等杂项） | 25 | 后续 |

约束：三族内仍被消费的兄弟令牌**必须保留**；本批不产生孤立注释；不改任何消费端代码。

## Goals / Non-Goals

**Goals:**

- 清掉三族模块专属死令牌（68 个），其中含 2 个传递性死亡令牌
- 修正 `doodle-craft/references/tokens.md` §1.11 中 11 行已不存在的令牌说明

**Non-Goals:**

- 不做批次③（25 个杂项令牌）
- 不修改任何 `var()` 消费端（含 `AnimalFace.vue`、StatsCard、Case Manager 组件）
- 不动 `--el-*` 覆盖层（由 Element Plus 全量样式消费）

## Decisions

### 1. 判据：精确 `var()` 计数 + 无动态读取路径

- **选择**：以 241 个文件（`frontend/src` + `frontend/tests` + `frontend/index.html`）的精确计数为删除依据，并额外核 `var(--${…})` 动态构造与 `getPropertyValue`
- **理由**：`var(--x)` 字面扫描无法覆盖 JS 读变量 / 模板拼接两条路径；实测均无（仅 `useSidebarResize.ts` 写 `--side-w`）→ 判据完备

### 2. 传递性死亡必须显式确认（本批新增 2 个）

- **发现**：`--ai-bg-success` / `--ai-bg-error` 的「elsewhere 消费 = 0」，唯一引用是同批要删的别名行
- **选择**：一并删除（批次② 实际 68 个 = 16 + 38 + 12 + 2）
- **理由**：只删别名会让它们变成**新的**死令牌，属于同一件事未做完；先做 in-file 别名引用分析再定删除集合，避免「删了还留孤儿」
- **备选**：保留 2 个别名 —— 会留下 2 个零消费令牌，否决

### 3. 同族在用兄弟一律保留

- **选择**：保留 `--case-border-subtle`(3) · `--case-border`(1) · `--ai-hint-orange`(3) · `--app-stat-text`(1)
- **理由**：`--app-stat-text` 是 `views/components/AnimalFace.vue:124` 的 `--af-ink` 取值源，`--af-ink` 在该组件内被 20+ 处 SVG 使用 → 真实在用；其余三个同理有消费点

### 4. 注释不产生孤儿，无需删注释行

- **选择**：只删令牌行；`/* HintCard 类型色 */`、`/* ── 模块专属色 · Case Manager ── */`、`/* ── 仪表盘统计卡 ── */` 三个 section 头均保留
- **理由**：每个 section 都至少剩 1 个存活令牌（`--ai-hint-orange` / `--case-border*` / `--app-stat-text`），注释仍然准确

### 5. 文档同步只改 `tokens.md`

- **选择**：删 §1.11 表的 11 行死令牌行，保留 `--app-stat-text` 行
- **理由**：该表逐行列出 CSS 变量名，删除后 11 行会指向不存在的令牌；`.agents` 其它文件的同族匹配均指向存活令牌（`--app-bg-subtle` / `--app-bg-card` / `--app-highlight` / `--app-status-*`）或该技能自带 `:root`（`prototype-design` 的 `--font-display`，属批次③）

### 6. 验证口径：静态 0 消费 + 门禁，不做浏览器核验

- **选择**：以「68 名全仓消费 = 0 且无动态读取」为删除依据；跑 typecheck / 构建 / `vue-frontend-check` 的 §7 强制扫描；不做浏览器目视
- **理由**：未被引用的自定义属性不参与计算值，删除对渲染恒等 —— 比「目视无异常」更强

## 模块防火墙自检

- 跨 App import：不涉及（纯前端令牌）
- 禁止跨 App import service/runner/consumer/state_machine：不涉及
- 所有 INSERT/UPDATE/DELETE 收敛到 api.py：不涉及（无写操作）
- 前端不直连数据库；仪表盘不做写操作：不涉及

## Risks / Trade-offs

- [误删仍在用的令牌] → 逐令牌精确计数；4 个兄弟令牌显式保留；`--app-stat-text` 的间接使用已追到 `AnimalFace.vue` 的 `--af-ink`
- [删完别名留下新孤儿] → 已做 in-file 别名分析，把 2 个传递性死亡令牌纳入本批
- [令牌通过 JS / 模板拼接读取] → 已排查 `getPropertyValue`、`setProperty`、`var(--${…})`，均无
- [技能文档与实现不一致] → 同一变更同步 `tokens.md` §1.11

## Migration Plan

1. 复核 68 个 0 消费 + 4 个在用兄弟 + 2 个传递性死亡
2. 删除 `tokens.css` 的 68 行令牌定义
3. 同步 `doodle-craft/references/tokens.md` §1.11
4. `npm run typecheck` + `npx vite build --mode development` + `vue-frontend-check`
5. 回滚：`git checkout` 一个 `.css` + 一个 `.md`，无数据迁移
