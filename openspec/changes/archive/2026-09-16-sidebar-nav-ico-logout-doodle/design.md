## Context

动机见 proposal.md。侧栏已有 `--mod-color`（`AppSidebar.vue` 按 `MOD_COLORS` 注入）与 doodle 墨边方盒，但 `.nav-ico` 固定白底；`.logout-btn` 为 EP `link` + 白底。参考稿 `temps/hand-drawn-doodle-sidebar.html` 中 `.nav-ico` 为逐项色块底，危险主按钮为 `--red` `#ff6b6b` + 白字。

约束：颜色走 `tokens.css`；不改导航数据与鉴权。

## Goals / Non-Goals

**Goals:**

- `.nav-ico` 默认/hover/active 均用 `--mod-color` 填色
- 「退出」展开/折叠均为马克笔红实心控件
- 令牌、组件、DESIGN_SYSTEM 三者一致

**Non-Goals:**

- 不改 `sidebarNavConfig` 路由或图标名
- 不改账号切换、登出 API
- 不重做侧栏布局、active 黄底书签条

## Decisions

1. **图标底用已有 `--mod-color`，不新增 per-item class**  
   路由色已注入，CSS `background: var(--mod-color)` 即可。备选：nth-child 写死色序——会与模块映射漂移，否决。

2. **Lucide 一律 `--ink`**  
   现有 8 模块色均为高明度，墨描边可读。不为 `--c-report` 单独做浅色描边，避免分叉。若验收对比不足再补例外。

3. **马克笔红进入令牌 `--app-marker-red: #ff6b6b`**  
   与参考稿 `--red` 对齐；`--app-status-danger`（`#FFB5A7` 桃粉）对比不足、也不像「红色」。侧栏 `.logout-btn` / `.sidebar__icon-logout` 引用该变量。同步 `DESIGN_SYSTEM.md` 色板一行。

4. **去掉 EP `link`，用 class 画实心按钮**  
   `el-button` 的 `link` 会抢透明底与下划线语义。保留 `el-button` 与 `data-testid`，去掉 `link`/`danger`，样式全由 `.logout-btn` 承担。

## 模块防火墙自检

- 跨 App import：无（仅前端 `shared` 样式）
- 禁止跨 App import service/runner/consumer/state_machine：不涉及
- 写库收敛 api.py：不涉及
- 前端不直连数据库：不涉及

## Risks / Trade-offs

- [桃粉 danger 与朱红并存] → 状态色仍用 `--app-status-danger`；仅侧栏危险 CTA 用 `--app-marker-red`，并在 DESIGN_SYSTEM 标明用途。
- [EP 深度选择器残留] → 用现有 `!important` 覆盖 EP，并去掉 `link` 减少冲突。
- [折叠按钮只有符号] → 同步红底以免两态割裂。
