## 1. .el-drawer 全局皮肤

- [x] 1.1 在 `frontend/src/style.css` 的 `.el-dialog` 皮肤之后新增 `.el-drawer` 皮肤（`border-radius: 6px 10px 6px 10px !important` + `border: 2.5px solid var(--ink) !important` + `overflow: hidden`），与 `.el-dialog` 逐条对齐；验证：`rg -n "\.el-drawer" frontend/src` 由 0 变为 1 且命中 `style.css`
- [x] 1.2 确认未引入新颜色 / 新令牌与模块私有抽屉皮肤；验证：`rg -n "\.el-drawer" frontend/src` 只命中 `style.css`，模块 `<style scoped>` 无抽屉边框 / 圆角覆写

## 2. 可见性绑定收敛（B 类 3 处）

- [x] 2.1 `device-inspector/components/SavedPagePicker.vue`：`:model-value="store.pickerVisible"` + `@update:model-value="(v) => (store.pickerVisible = v)"` → `v-model="store.pickerVisible"`；验证：`:model-value` 与写回 handler 同时消失，其余属性不变
- [x] 2.2 `device-inspector/components/SaveToElementsDialog.vue`：同构改为 `v-model="store.saveDialogVisible"`；验证：同上
- [x] 2.3 `device-inspector/components/SnapshotListDrawer.vue`（el-drawer）：同构改为 `v-model="store.drawerVisible"`；验证：同上
- [x] 2.4 确认 C 类 3 处与 D 类 5 处**未被改动**；验证：`rg -n "creatingKind === 'folder'|enlargeVisible|:model-value=\"visible\"" frontend/src` 命中数与改动前一致

## 3. 规格与速查同步

- [x] 3.1 新增 `specs/frontend-l5-overlay/spec.md` 的两条 ADDED 需求：「Overlay visibility binding follows state ownership」（3 场景）与「Blocking overlay skins are symmetric」（2 场景）；验证：`openspec validate --strict` 通过
- [x] 3.2 更新 `frontend/AGENTS.md` L5 速查：§② 全局皮肤行补 `.el-drawer`、§③ 写明绑定口径（按状态归属三类）、§⑤ 补两条判据、§⑥ 更新 `rg -n "\.el-drawer"` 判据与移除该已知缺口；验证：速查与 spec 无冲突

## 4. 门禁与归档

- [x] 4.1 `cd frontend && npm run typecheck`；验证：全仓 34 个既有错误，三个改动 vue 文件零错误
- [x] 4.2 用 `vue-frontend-check` 过改动文件；验证：字号裸 px 与禁项扫描在改动文件上均为 0 处
- [x] 4.3 归档（经 `openspec-archive-change`）；验证：`openspec/specs/frontend-l5-overlay/spec.md` 含 6 条需求，变更进入 archive
