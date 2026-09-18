## Context

见 `proposal.md` - Why。实测：`ChatView.css` 的 `ChatView.css` 路径引用 = 0、`--chat-*` 变量引用 = 0；`views/shared/` 被 5 处非 scoped `@import` 引用（RegisterCard ×2 / LoginCard ×2 / AccountSwitchPrompt ×1）；`DoodleNote.vue` 7 处 `var(--x, #字面量)`。

## Goals / Non-Goals

**Goals:** 清理已确认的死样式资产 · 消除目录命名撞车 · 去掉令牌字面量兜底 · 全程可恢复、零视觉变化。
**Non-Goals:** 不做 400+ 处管道溯源（另立 C-2）· 不改 `views` 的样式加载方式（仍为组件内 `@import`）· 不重命名 `views/styles/` 内容 · 不动 23 处跨仓其它兜底。

## Decisions

### D1 · 隔离而非删除
`ChatView.css` 移入 `temps/quarantine/`。理由：仓库工作区存在多个来源的未提交改动，直接删除不可恢复；隔离等价于「不在源码树」，且可随时恢复。若后续确认无需恢复，可在 C-2 一并删除。

### D2 · `views/shared` → `views/styles`
撞车点在目录名 `shared`（平台级命名空间）。改名而非上收到 `shared/styles/`，理由：这两份样式只被 views 的 3 个组件消费，属于视图层局部资产；上收会把「视图私有」变成「全局可引用」，与 L2/L3 归属口径相反。

### D3 · 兜底字面量的移除前提
逐个确认被引用变量存在（`--app-marker-red` / `--c-case` / `--c-workflow` / `--app-offline` 均在 T0 兼容别名层）后才删兜底；任一不存在则保留并登记。本次 7 处全部通过。

## 模块防火墙自检

| 红线 | 本变更 |
|------|--------|
| 跨 App import / 写库 / 前端直连数据库 | 不涉及：仅 `frontend/src` 样式资产移动与变量引用 |
| 新增依赖 | 无 |

## Risks / Trade-offs

- [改名后若有动态拼接的 `@import` 路径会断] → 全仓扫描 `views/shared/` 命中 = 0 后收尾；`@import` 是静态字面量，可静态覆盖
- [隔离的文件被遗忘] → 在 `temps/quarantine/` 留同名文件，并在本变更 design 记录来源与恢复方式
- [构建级验证缺失] → `vite build` 仍被沙箱拦（spawn EPERM）；以门禁 + 裸值 + 类型检查三重替代，浏览器核验未做

## Migration Plan

1. 确认 0 引用 → 隔离 `ChatView.css`
2. `views/shared/` 改名 + 5 处 `@import` 同步
3. 校验被引用变量存在 → 移除 7 处字面量兜底
4. 回归：`lint:styles` · 裸值复核 · `vue-tsc`
5. 回滚：文件移动可逆（rename）；兜底改动集中在 1 个文件

## Open Questions（登记为 C-2 范围）

- 管道溯源：模板内联 `style` 230 处 · SVG 元素属性 99 处 · prop 传色约 24 处 · `script` 字符串 55 处 · `.ts` 25 处，按 §3.1 判定树逐处改引用（需按边界分类后再动）
- 跨仓仍有 23 处 `var(--x, #字面量)` 兜底，需逐处确认变量存在后清理，并考虑纳入门禁
- `workflow/index.vue` 的非 scoped `<style>` 块（`.wf-modal-hint` / `.wf-modal-label`）仍需补理由注释（另一处同类块已有注释）
- 文档挂账：`DESIGN_SYSTEM.md` 悬空引用 · `tokens.css` 段号「六」重复