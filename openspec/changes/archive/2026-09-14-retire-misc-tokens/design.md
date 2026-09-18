## Context

动机见 `proposal.md` - Why。P3 死令牌三批推进的收尾批：

| 批 | 内容 | 个数 | 状态 |
|---|------|:--:|------|
| ① | `@deprecated` 两族（`--app-module-*` + 旧色） | 31 | 已归档 `2026-09-14-retire-deprecated-tokens` |
| ② | 模块专属色（AI / Case / 仪表盘统计卡） | 68 | 已归档 `2026-09-14-retire-module-scoped-tokens` |
| **③** | 中性色/阴影/字号/独立区杂项 | **25** | 本变更（P3 收尾） |

约束：本批删除会留下 2 条孤立注释与 1 处过时的 section 标题，必须同批处理；不改任何消费端代码（本批 0 消费，无消费端可改）。

## Goals / Non-Goals

**Goals:**

- 清掉最后 25 个零消费令牌，P3 死令牌归零
- 同批清掉由此产生的注释残留（2 条孤儿注释 + 1 处标题），使 `tokens.css` 不出现「说了却没有」的描述
- 修正 `doodle-craft/references/tokens.md` §1.7 中指向已删令牌的 `icon` 行

**Non-Goals:**

- 不动 `--el-*` 覆盖层（由 Element Plus 全量样式消费）
- 不改动 `hifi-guide.md` / `exec-arch.html` 中各自 `:root` 的同名 `--font-display`（非本仓令牌）
- 不重命名 / 不合并任何存活令牌（例如保留 `--app-footer-yellow-text`、`--app-icon-purple-bg` 等在用兄弟）

## Decisions

### 1. 判据：带边界的全仓出现次数

- **选择**：对 25 名逐个做 `名称(?![-a-z0-9])` 的全仓计数，而非只数 `var()`
- **理由**：本批清完后 P3 归零，值得用更强判据；实测每个名字全仓仅 1 次出现（自己的定义行）→ 既无消费，也无别名引用
- **备选**：仅用 `var()` 计数 —— 无法发现注释 / 文档中的悬空引用，本批正好有 1 处（tokens.md）

### 2. 孤儿注释与过时标题同批处理

- **选择**：删 2 条注释（登录页光晕 / @deprecated legacy aliases），并把 `阴影/遮罩/光晕` 标题改为 `阴影/遮罩`
- **理由**：这三处都是本次删除的**直接后果**——注释下已无令牌、标题所列的类别已不存在；留着会让后来者以为存在光晕/字号别名令牌
- **范围控制**：除此之外不动任何注释、不重排、不改格式；section 头有存活令牌的（`中性色` / `辅助/图标/杂项色` / `独立区`）一律保留

### 3. 文档同步只改 `tokens.md` 一行

- **选择**：删 §1.7 表的 `icon` 行
- **理由**：该行第三列即 `--app-icon-shadow`，令牌删除后该行指向不存在的东西；同表 sm/md/lg 三行变量仍存在，保留
- **确认不改**：`hifi-guide.md` 的 `--font-display: 'DM Sans'` 与 `exec-arch.html` 的 `--font-display:'Nunito'` 都是各自文档/页面 `:root` 里的独立定义，仅同名

### 4. 验证口径：静态 0 消费 + 门禁，不做浏览器核验

- **选择**：以「全仓出现次数 = 1（仅定义行）→ 删除后 = 0」为删除依据；跑 typecheck / 构建 / `vue-frontend-check` §7 强制扫描；不做浏览器目视
- **理由**：未被引用的自定义属性不参与计算值，删除对渲染恒等 —— 比「目视无异常」更强；注释与标题改动不产生任何计算样式

## 模块防火墙自检

- 跨 App import：不涉及（纯前端令牌）
- 禁止跨 App import service/runner/consumer/state_machine：不涉及
- 所有 INSERT/UPDATE/DELETE 收敛到 api.py：不涉及（无写操作）
- 前端不直连数据库；仪表盘不做写操作：不涉及

## Risks / Trade-offs

- [误删仍在用的令牌] → 带边界的全仓计数，每名仅 1 次出现（定义行）；兄弟令牌（`--app-footer-yellow-text` / `--app-icon-purple-bg` / `--app-shadow-sm|md|lg` / `--doodle-ink|bg|radius|shadow`）逐一确认在用
- [注释/文档残留悬空引用] → 本批已把 2 条孤儿注释、1 处过时标题、1 行文档表一并处理
- [同名令牌误伤技能文档] → `--font-display` 两处外部出现已核实为各自 `:root` 定义（`'DM Sans'` / `'Nunito'`），不动
- [P3 收尾后仍死代码] → 收尾时重跑一次全量死令牌统计，确认只剩 `--el-*`（EP 全量样式消费，非死）

## Migration Plan

1. 复核 25 个 0 消费（带边界计数）· 复核动态读取路径
2. 删除 `tokens.css` 的 25 行 + 2 条孤儿注释 + 1 处标题改写
3. 同步 `doodle-craft/references/tokens.md` §1.7
4. `npm run typecheck` + `npx vite build --mode development` + `vue-frontend-check`
5. 回滚：`git checkout` 一个 `.css` + 一个 `.md`，无数据迁移
