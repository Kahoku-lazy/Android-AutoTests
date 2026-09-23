<script setup>
/** Device Inspector — 一键 Dump 获取 → 快照落库回看 → 按五分组查看全量元素 → 图上按分组圈选。 */
import { onMounted, computed } from 'vue'
import { useElementStore } from './store'
import { KEY_DISABLED_MESSAGE, NO_SELECTION_MESSAGE } from './constants'
import CaptureForm from './components/CaptureForm.vue'
import ScreenshotView from './components/ScreenshotView.vue'
import StructureAnalysisPanel from './components/StructureAnalysisPanel.vue'
import SnapshotListDrawer from './components/SnapshotListDrawer.vue'
import SaveToElementsDialog from './components/SaveToElementsDialog.vue'
import WorkbenchHeader from '@/shared/components/WorkbenchHeader.vue'
import ErrorState from '@/shared/components/patterns/ErrorState.vue'
import { IconClock, IconLayers, IconSave } from '@/shared/icons'

const store = useElementStore()

/** 历史快照没有全量节点索引（降级为保留集）时如实提示，避免用户以为元素变少了 */
const isLegacySource = computed(() => store.layerSource === 'legacy')

/** 页脚序列号来自快照列表（分层响应不含 serial，不为此加后端字段） */
const snapshotSerial = computed(
  () => store.snapshots.find(s => s.id === store.snapshot?.snapshot_id)?.serial || ''
)

onMounted(async () => {
  await store.fetchDevices()
  await store.fetchSnapshots()
})

/** 「保存到元素定位」的可用前提：当前展示的是自有快照（有 snapshot_id） */
const canSaveToElements = computed(() => !!store.snapshot?.snapshot_id)

function onElementClick(el) {
  store.selectElement(el)
}

/**
 * 「保存到元素定位」：无快照时按键灰底并提示原因；未勾选任何元素时只提示、
 * 不打开弹窗、不发请求（弹窗内确认保存时 store 会再做一次同一校验）。
 */
function onSaveToElementsClick() {
  if (!canSaveToElements.value) {
    store.notifyKeyUnavailable()
    return
  }
  if (store.checkedCount === 0) {
    store.notify(NO_SELECTION_MESSAGE)
    return
  }
  store.saveDialogVisible = true
}
</script>

<template>
  <div class="doc-page doc-page--fixed wb-shell inspector-workbench">
    <WorkbenchHeader
      title="设备检查器"
      subtitle="选择设备一键获取页面元素快照，回看、筛减并保存到元素管理"
      icon="crosshair"
      icon-gradient="linear-gradient(135deg,var(--app-status-purple),var(--c-element))"
    />

    <div class="doc-body">
      <section class="inspector-section">
        <!-- 获取表单 + 历史/保存入口 -->
        <div class="toolbar">
          <CaptureForm @capture="store.capture()" />
          <button
            class="action-btn"
            data-testid="snapshot-list-btn"
            @click="store.drawerVisible = true"
          >
            <IconClock :size="14" />历史快照
          </button>
          <button
            class="action-btn"
            :class="{ 'action-btn--unavailable': !canSaveToElements }"
            :aria-disabled="canSaveToElements ? 'false' : 'true'"
            data-testid="save-to-elements-btn"
            :title="canSaveToElements ? '' : KEY_DISABLED_MESSAGE"
            @click="onSaveToElementsClick"
          >
            <IconSave :size="14" />保存到元素定位
          </button>
          <span v-if="store.snapshot" class="info">{{ store.groupElements.length }} 元素</span>
          <span v-if="isLegacySource" class="info" data-testid="legacy-source-hint">
            历史快照无全量索引：当前为该快照的保留集，不含被展示裁剪丢弃的元素
          </span>
          <ErrorState v-if="store.error" :message="store.error.message" @retry="store.retry()" />
        </div>

        <!-- 工作区两栏：分组选择 + 当前分组元素表格（左，由结构面板承载） · 手机屏幕（右，按当前分组圈选） -->
        <div class="workspace">
          <section class="col col-structure">
            <StructureAnalysisPanel
              :groups="store.groupBadges"
              v-model:active-group-id="store.activeGroupId"
              :elements="store.groupElements"
              :selected="store.selected"
              @select="onElementClick"
            />
          </section>
          <section class="col col-phone">
            <ScreenshotView
              :screen-w="store.snapshot?.screen_w"
              :screen-h="store.snapshot?.screen_h"
              :elements="store.groupElements"
              :group-color="store.activeGroup.color"
              :selected="store.selected"
              :screenshot-path="store.snapshot?.screenshot_path || ''"
              @click-element="onElementClick"
            />
          </section>
        </div>
      </section>
    </div>

    <footer class="inspector-footer">
      <span><IconClock :size="14" />就绪</span>
      <span><IconLayers :size="14" />{{ store.elements.length }} 元素</span>
      <span v-if="snapshotSerial || store.snapshot?.package">{{ snapshotSerial || '—' }} · {{ store.snapshot?.package || '—' }}</span>
    </footer>

    <SnapshotListDrawer />
    <SaveToElementsDialog />
  </div>
</template>

<style scoped>
/* 页根纸面由 L0 壳层承担；本页不画不透明 --paper，避免盖住 PaperDoodles */

.inspector-workbench .doc-body {
  flex: 1;
  min-height: 0;
  width: 100%;
  max-width: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.inspector-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  width: 100%;
  box-sizing: border-box;
  padding: var(--app-space-lg);
  overflow: hidden;
}

.toolbar {
  display: flex;
  align-items: center;
  gap: var(--insp-gap-row);
  margin-bottom: var(--app-space-md);
  flex-shrink: 0;
  flex-wrap: wrap;
}

.info { font-size: var(--app-size-sm); color: var(--app-text-secondary); white-space: nowrap; }

.workspace {
  flex: 1;
  min-height: 0;
  width: 100%;
  display: grid;
  /* 三栏视觉顺序：页面分区 → 元素表格（二者在结构面板内并排） → 手机屏幕 */
  grid-template-columns: minmax(0, 2.4fr) minmax(0, 1fr);
  gap: var(--app-space-lg);
  overflow: hidden;
}

.col {
  min-height: 0;
  min-width: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
  flex: 1 1 0;
}

/* 结构面板自带内部滚动（分区列滚动、表格定高），外层不再叠加滚动条 */
.col-structure { overflow: hidden; }

@media (max-width: 1200px) {
  .workspace {
    grid-template-columns: 1fr;
    grid-template-rows: minmax(320px, 1fr) minmax(280px, auto);
    overflow-y: auto;
  }
}

.inspector-footer {
  display: flex; align-items: center; justify-content: center; gap: var(--app-space-lg);
  padding: var(--insp-pad-footer); background: var(--app-highlight);
  border-top: 2.5px solid var(--ink);
  font-size: var(--app-size-sm); font-weight: 700;
  color: var(--app-footer-yellow-text); font-family: var(--app-font-display);
  flex-shrink: 0;
}
.inspector-footer span { display: flex; align-items: center; gap: var(--app-space-xs); font-size: var(--app-size-sm); }

/* ═══════════════════════════════════════════
   硬边按键皮肤（作用域：本页）

   几何基准 = 侧栏底部「退出」按钮，与设备管理页 .device-workbench 同源：
   2px 墨色实边 + 2px 近直角 + 2px 偏移硬阴影；hover 左上位移 1px、阴影增至 3px。
   工具条按键底色按「可用性」分配：可用 = 天蓝 var(--c-workflow)，不可用 = 灰 var(--color-ink-79)；
   两种底色都用墨色文字（对比度 ≥ 4.5:1）。不可用键不用原生 disabled（它不派发 click，
   无法弹出原因提示），由 aria-disabled + click 守卫承担，故灰底必须撤掉位移阴影以免像可用态。
   弹窗「保存」等 EP 按键沿用各自语义底色（柠黄）。
   text / link 型图标按键（快照删除）被正向排除，保持无底无边的图标形态。
   弹窗与抽屉不传送到 body，DOM 仍在页面根之内，故 :deep() 可达。
   共享件 ErrorState / DoodleBtn 与全局主题不变 —— 皮肤只由本页作用域承担。
   ═══════════════════════════════════════════ */

/* 原生工具条按键：布局（唯一定义处，CaptureForm 不再声明） */
.inspector-workbench :deep(.action-btn) {
  display: inline-flex; align-items: center; gap: var(--app-space-xs);
  font-size: var(--app-size-xs); padding: var(--app-space-xs) 12px;
  cursor: pointer; font-family: inherit; white-space: nowrap; flex-shrink: 0;
}

/* 几何与状态：原生按键与弹窗按键共用 */
.inspector-workbench :deep(.action-btn),
.inspector-workbench :deep(.el-button:not(.is-text):not(.is-link)) {
  border: 2px solid var(--ink) !important;
  border-radius: 2px !important;
  color: var(--ink) !important;
  font-weight: 700 !important;
  box-shadow: 2px 2px 0 0 var(--ink) !important;
  transition:
    transform var(--app-duration-fast) var(--app-ease),
    box-shadow var(--app-duration-fast) var(--app-ease),
    background var(--app-duration-fast) var(--app-ease) !important;
}
.inspector-workbench :deep(.action-btn:not(.action-btn--unavailable):not(:disabled):hover),
.inspector-workbench :deep(.el-button:not(.is-text):not(.is-link):not(:disabled):hover) {
  transform: translate(-1px, -1px) !important;
  box-shadow: 3px 3px 0 0 var(--ink) !important;
}

/* 表纸线型登记（frontend-doodle-sketch-table）：设备管理页与检查器均为实线，
   宽度与颜色仍取共享令牌 --comp-sheet-border，这里只覆写 border-style */
.inspector-workbench :deep(.sketch-sheet) { border-style: solid; }

/* 设备选择框：触发键与下拉浮层都是白底、无阴影。边框仍用墨线。
   浮层默认传送到 body，用 popper-class 才能打到；选项文案由 CaptureForm 的 label 提供。 */
.inspector-workbench :deep(.cap-device .el-select__wrapper),
.inspector-workbench :deep(.cap-device .el-input__wrapper) {
  background: var(--app-bg-input) !important;
  border: 2px solid var(--ink) !important;
  border-radius: 2px !important;
  box-shadow: none !important;
  font-weight: 700 !important;
}
.inspector-workbench :deep(.cap-device .el-select__wrapper.is-focused),
.inspector-workbench :deep(.cap-device .el-select__wrapper.is-hovering),
.inspector-workbench :deep(.cap-device .el-input__wrapper.is-focus) {
  box-shadow: none !important;
}
:global(.cap-device-popper.el-popper) {
  background: var(--app-bg-input) !important;
  box-shadow: none !important;
}

/* 可用按键：统一天蓝底（可点击） —— 布局规则已在前，这里只补底色 */
.inspector-workbench :deep(.action-btn) { background: var(--c-workflow); }

/* 不可用按键（灰键）：灰底 + 撤掉位移阴影 + opacity 保持 1，与可用态仅靠底色区分。
   注意必须带与皮肤同源的 :not() 守卫：否则本规则特异性 (0,3,0) 低于皮肤的 (0,4,0)，
   两条都是 !important 时由特异性裁决，EP 按钮的硬阴影会残留。 */
.inspector-workbench :deep(.action-btn--unavailable),
.inspector-workbench :deep(.el-button.is-disabled:not(.is-text):not(.is-link)),
.inspector-workbench :deep(.el-button:disabled:not(.is-text):not(.is-link)) {
  cursor: not-allowed;
  box-shadow: none !important;
}
.inspector-workbench :deep(.action-btn--unavailable) {
  background: var(--color-ink-79) !important;
  opacity: 1;
}

/* ═══════════════════════════════════════════
   危险实心键（快照抽屉「一键清空」）：几何与 hover 位移沿用上面的硬边皮肤。
   底色取 EP 实心 danger 的深红（--el-color-danger，即 T0 原子 --color-red-46），
   文字改浅色 —— 墨字压深红只有 2.78:1，跌破 4.5:1 门槛（同 device-pool 的先例）。
   参考键（侧栏「退出」）用的是更浅的 --app-marker-red，白字仅 2.92:1，故不照抄其色值。
   ═══════════════════════════════════════════ */
.inspector-workbench :deep(.el-button--danger:not(.is-text):not(.is-link)) {
  background: var(--el-color-danger) !important;
  border-color: var(--ink) !important;
  color: var(--color-white) !important;
}
.inspector-workbench :deep(.el-button--danger:not(.is-text):not(.is-link):not(:disabled):hover) {
  background: var(--el-color-danger) !important;
  border-color: var(--ink) !important;
  color: var(--color-white) !important;
}

/* 危险键不可用：回落到本页灰键口径（灰底 + 墨字 + 撤位移阴影 + opacity 1），
   特异性高于上面的危险规则，避免红底禁用被读成「可点」。 */
.inspector-workbench :deep(.el-button--danger.is-disabled:not(.is-text):not(.is-link)),
.inspector-workbench :deep(.el-button--danger:disabled:not(.is-text):not(.is-link)) {
  background: var(--color-ink-79) !important;
  color: var(--ink) !important;
  box-shadow: none !important;
  opacity: 1;
  cursor: not-allowed;
}
</style>
