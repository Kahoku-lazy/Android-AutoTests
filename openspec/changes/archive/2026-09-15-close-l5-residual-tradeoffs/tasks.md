## 1. store 解耦 UI（②）

- [x] 1.1 `workflow/stores/libraryStore.ts`：`opts.confirmEmptyOverwrite` 由 `boolean` 改为 `(remoteNodes: number) => Promise<boolean>`，分支内改为 `const ok = await opts.confirmEmptyOverwrite(remoteNodes); if (!ok) return`；验证：store 内不再出现 `ElMessageBox`（实测 0 处）
- [x] 1.2 移除 `libraryStore.ts:6` 的 `import { ElMessageBox } from 'element-plus'`；验证：该文件无 `from 'element-plus'` 导入（实测 0 处）
- [x] 1.3 `workflow/index.vue`：新增 `confirmEmptyOverwriteDialog(remoteNodes)`（`try { await ElMessageBox.confirm(原文案, '覆盖确认', { 确定/取消/warning }) ; return true } catch { return false }`），`persistPageFlow` 传该回调；验证：空图覆盖的确认条件、文案与取消语义与改动前一致（`workflow/index.vue:141-154`，文案逐字保留）

## 2. 弹层关闭策略（①）

- [x] 2.1 按判据补齐 4 处含输入弹层的 `:close-on-click-modal="false"`：`workflow/index.vue:425`（目录对话框）· `device-inspector/components/SaveToElementsDialog.vue:95` · `ai-assistant/components/TaskBoard.vue:80`（新建任务表单）· `ai-assistant/EvaluatorTab.vue:520`（试卷编辑器，与既有 `destroy-on-close` 同行）；验证：4 处均带该属性
- [x] 2.2 复核其余 15 处符合判据（预览/抽屉/只读选择不写该属性；危险确认保留 false）；验证：`close-on-click-modal|destroy-on-close` 共 12 处（11 `false` + 1 `destroy-on-close`），与判据一致

## 3. 规格与速查同步

- [x] 3.1 新增 `specs/frontend-l5-overlay/spec.md` 的两条 ADDED 需求（关闭策略按输入性、store 不依赖 UI 组件，共 4 场景）；验证：`openspec validate --strict` 通过
- [x] 3.2 更新 `frontend/AGENTS.md` L5 速查：③ 写明关闭策略与 `destroy-on-close` 判据、⑤ 补两条判据、⑥ 更新判据与移除两项已知缺口；验证：速查与 spec 一致

## 4. 门禁与归档

- [x] 4.1 `cd frontend && npm run typecheck`；验证：5 个改动文件零错误（`TOTAL_ERRORS=34` 为既有无关错误，`MY_FILES_ERRORS=0`）
- [x] 4.2 用 `vue-frontend-check` 过 5 个改动文件；验证：calibration §7 强制扫描已执行，**新增行零违规**（唯一命中 `EvaluatorTab.vue:460` 的裸 px `padding` 为未改动的上下文行，同行的 `gap:14px→var(--app-space-md)` 属 2026-09-14 L3 间距收敛）
- [x] 4.3 归档（经 `openspec-archive-change`）；验证：`openspec/specs/frontend-l5-overlay/spec.md` 含 8 条需求，变更进入 archive
