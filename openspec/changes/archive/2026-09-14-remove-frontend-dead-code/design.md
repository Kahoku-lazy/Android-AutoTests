## Context

动机见 `proposal.md` - Why。相关现状（已核对）：

- `GroupTreePanel.vue` 全仓引用只剩自身文件头注释；其原消费方（element-locator 的 WebElementManager / ApiEndpointManager）已随 `remove-legacy-element-locator-managers` 删除。
- `.soft-icon*` 全仓引用只剩 `style.css` 自身与 `frontend/AGENTS.md` 的缺口说明；L2 删除 `WorkbenchHeader` 的 `mark` emoji 回退后已无消费方。

约束：只在必须触碰处下手；不改任何仍有消费方的类；不动 L0–L2 既有骨架与令牌。

## Goals / Non-Goals

**Goals:**

- 删除上述两处死代码，使「检索命中 = 真实在用」
- 同步 `frontend/AGENTS.md` 的登记，避免二次误导

**Non-Goals:**

- 不重构 `style.css` 其它段落或重排格式
- 不动 `--doodle-ink` 等仍被消费的令牌
- 不处理 L3 的其它问题（点阵规则、`.doc-body` 内边距、块语言），它们分别属步骤 ② 与 ③

## Decisions

### 1. 「可删」的唯一判据是「全仓 0 引用」

- **选择**：以 `rg` 全仓检索（含 `*.vue` / `*.css` / `*.ts` / `*.spec.ts` / 文档）0 命中作为唯一判据
- **理由**：避免凭观感删代码；两处均已复核
- **备选**：保留并在 AGENTS.md 标注「已弃用」—— 与「清死代码」目标相悖，且 `style.css` 属 L0 段，越留越容易被误用

### 2. `GroupTreePanel.vue` 直接删除，不做迁移

- **选择**：整文件删除
- **理由**：它是 L3 共享分栏件，但当前没有任何 L3 页面在用；L3 分栏由 device-inspector（`.workspace`）与 element-locator（`.page-workbench__split`）各自实现，保留它不会收敛分栏口径
- **备选**：改造为「通用项目树件」以备未来复用 —— 需求不存在，属过度设计，放弃

### 3. `.soft-icon*` 从 `style.css` 原地删除

- **选择**：删除 `style.css:56-103` 的 8 组规则（含段落注释）
- **理由**：L0 段「既有类留在原处不动」的前提是它**仍有消费方**，该前提已不成立
- **备选**：只删变量、保留类壳 —— 留下无规则消费的类名，与 L2「No declaration without a consumer」精神冲突

## 模块防火墙自检

- 跨 App import：不涉及（纯前端）
- 禁止跨 App import service/runner/consumer/state_machine：不涉及
- 所有 INSERT/UPDATE/DELETE 收敛到 api.py：不涉及（无写操作）
- 前端不直连数据库；仪表盘不做写操作：不涉及

## Risks / Trade-offs

- [误删仍在使用的类] → 删除前 `rg` 全仓复核 0 命中，删除后 `npm run typecheck` + 构建双验
- [外部未入库代码引用] → 本项目不对外发布组件包，风险为 0
- [文档不同步造成二次误导] → 同一变更内更新 `frontend/AGENTS.md` L2 §⑥

## Migration Plan

1. `rg` 复核两处 0 引用
2. 删除 `GroupTreePanel.vue`
3. 删除 `style.css` 的 `.soft-icon*` 段
4. 更新 `frontend/AGENTS.md` L2 §⑥
5. `cd frontend && npm run typecheck` + 构建校验
6. 回滚：`git checkout` 两个文件即可，无数据迁移
