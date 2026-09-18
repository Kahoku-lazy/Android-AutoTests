## 1. 事实复核

- [x] 1.1 复核步骤 ②③ 落地范围与归属变更；验证：`unify-l3-container` 的 proposal 明确含「6 处点阵 + `.doc-body` 水平内边距 32→24 + `.wb-body` 登记例外」，`fix-l3-container-residual` 收敛残留裸覆写，`converge-l3-block-language` 落块语言判据；spec 侧确认 `frontend-l3-container:38` 与 `frontend-l2-page-region:83` 均登记了 `.wb-body` 例外
- [x] 1.2 复核实测数值；验证：`--doodle-bg` 消费 5 处（grep）· `gap:14px` + `gap: 14px` 共 6 处 / 5 个文件 · `--app-paper-dot` 全仓 0 命中 · `doc-section` 65 处命中、`<AppCard` 出现在 9 个文件
- [x] 1.3 复核 `AGENTS.md` 待改数值；验证：`main.ts` 34 行 · `style.css` 230 行 · `tokens.css` 300 行 · `--app-topbar-h` 在第 212 行 · `--side-w` 在第 213 行（`index.html` 16 行与 `sidebarNavConfig.ts` 55 行原值即正确，未动）

## 2. L3 报告同步

- [x] 2.1 §五 9 条改写为当前状态；验证：291/292/293/295/296/299 改为 `class="ok"` 并附归档变更名，297 `--doodle-bg` 改 5 处，298 `gap:14px` 改 6 处 / 5 文件并写明挂起理由
- [x] 2.2 §六 结论与三步状态改「②③ 已落地」；验证：307 改为「L3 已按裁决收敛…」，310 三步全 ✅ 并各附归档变更名
- [x] 2.3 §七 变更记录补条目；验证：新增 5 条（步骤② / 步骤③ / P3 三批 / 残留死代码清理 / 唯一挂起项），条目由 3 → 8
- [x] 2.4 footer 同步范围更新；验证：改为「含步骤①②③、P3 死令牌三批、残留死代码清理，共 10 个归档变更」并列出三份 spec

## 3. L2 报告同步

- [x] 3.1 §五 4 条改写；验证：278 画布例外已登记、280 死声明已清除（附 `remove-dead-doc-page-declarations`）、281 点阵已收敛、283 `gap:14px` 改 6 处 / 5 文件
- [x] 3.2 §六「下一层工作」改写；验证：已落地项与新剩余项（页头截断缺 `title` 回退 · 6 处裸 px）分段写明
- [x] 3.3 footer 同步范围更新；验证：改为列出 `remove-dead-doc-page-declarations` / `unify-l3-container` / P3 三批 / `cleanup-residual-dead-code` 等

## 4. `frontend/AGENTS.md` 同步

- [x] 4.1 L0 §② 行数改正；验证：`style.css` 全文 230 行 · `tokens.css` 全文 300 行（`main.ts` 37 行未动，见下方说明）
- [x] 4.2 L1 §③ 令牌行号改正；验证：`--side-w`（`tokens.css:213`）· `--app-topbar-h`（`tokens.css:212`），回读 `tokens.css:212,213` 确认为这两个令牌

## 5. 验证

- [x] 5.1 逐条回读改动后的句子；验证：两份报告 `<li>`/`</ul>` 结构完好（`<li` 与 `</li>` 的 3 处差额在报告第 7–9 行的导航项，**改动前即如此**，非本变更引入）；L3 残留检索「待开 / L3 尚未收敛 / 待步骤」= 0，L2 残留「是死声明 / 点阵纹理仍有两个来源 / 一处裸 px」= 0
- [x] 5.2 改动范围核对；验证：`git diff --numstat -- frontend/AGENTS.md` = `298 16 frontend/AGENTS.md`（本变更）；两份 HTML 报告被 `.gitignore:121` 的 `dev_docs/**/*.html` 排除（该目录 8 份 HTML 全部未跟踪，属仓库既有约定），因此不产生 `git diff` —— 已写入 proposal · Impact 与 design · Migration Plan，回滚口径改为手工回退

## 6. 范围说明（未顺手改动，留待后续）

- [x] 6.1 `frontend/AGENTS.md` L0 §② 的 `main.ts`（写 37，实测 34）与 L1 §② 各文件行数（`App.vue` 写 71/实测 73 · `AppSidebar.vue` 写 302/实测 299 · `AppSidebar.style.css` 写 ~520/实测 509 · `PaperDoodles.vue` 写 116/实测 115 · `useSidebarResize.ts` 写 75/实测 74）存在同类偏移，但**并非本会话变更所致**，且这些文件正被并行工作修改 → 未纳入本变更，只在此登记；验证：实测行数见 1.3 与本节
