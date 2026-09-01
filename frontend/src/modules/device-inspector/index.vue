<script setup>
/** Device Inspector — v1.7 快照化：一键 dump/OCR 获取 → 快照落库回看 → 筛减导入元素定位 → 页面回看。 */
import { onMounted, computed } from 'vue'
import { useElementStore } from './store'
import CaptureForm from './components/CaptureForm.vue'
import ScreenshotView from './components/ScreenshotView.vue'
import PageElementsPanel from './components/PageElementsPanel.vue'
import StructureAnalysisPanel from './components/StructureAnalysisPanel.vue'
import SnapshotListDrawer from './components/SnapshotListDrawer.vue'
import SaveToElementsDialog from './components/SaveToElementsDialog.vue'
import SavedPagePicker from './components/SavedPagePicker.vue'
import WorkbenchHeader from '@/shared/components/WorkbenchHeader.vue'
import ErrorState from '@/shared/components/patterns/ErrorState.vue'
import FilterTabs from '@/shared/components/FilterTabs.vue'
import { IconClock, IconLayers, IconSave } from '@/shared/icons'

const store = useElementStore()

/** 结构视图下左侧截图展示全量元素（分区表展示全量，行选中高亮需与全量对齐） */
const screenshotElements = computed(() =>
  store.viewMode === 'structure' ? store.elements : store.filteredElements
)

const filterOptions = [
  { key: 'all', label: '全部' },
  { key: 'clickable', label: '可点击' },
  { key: 'text', label: '有文本' },
  { key: 'rid', label: '有 Resource ID' },
  { key: 'clickable_text', label: '可点击+文本' },
  { key: 'clickable_no_text', label: '可点击无文本' },
  { key: 'input', label: '输入框' },
  { key: 'scrollable', label: '可滚动' },
]

onMounted(async () => {
  await store.fetchDevices()
  await store.fetchSnapshots()
})

function onElementClick(el) {
  store.selectElement(el)
}

function onOcrClick(ocr) {
  store.selectOcr(ocr)
}
</script>

<template>
  <div class="doc-page wb-shell">
    <WorkbenchHeader
      title="设备检查器 Device Inspector"
      subtitle="选择设备一键获取页面元素与 OCR 快照，回看、筛减并保存到元素管理"
      icon="crosshair"
      icon-gradient="linear-gradient(135deg,#C9B6F2,#a78bfa)"
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
            data-testid="saved-page-btn"
            @click="store.pickerVisible = true"
          >
            <IconLayers :size="14" />已保存页面
          </button>
          <button
            class="action-btn"
            :disabled="!store.snapshot"
            data-testid="save-to-elements-btn"
            @click="store.saveDialogVisible = true"
          >
            <IconSave :size="14" />保存到元素定位
          </button>
          <button
            v-if="store.viewMode === 'elements'"
            class="action-btn"
            :disabled="!store.snapshot?.snapshot_id || store.analyzing"
            data-testid="analyze-btn"
            @click="store.analyzeSnapshot()"
          >
            <IconLayers :size="14" />{{ store.analyzing ? '分析中...' : '结构分析' }}
          </button>
          <button
            v-else
            class="action-btn"
            data-testid="back-elements-btn"
            @click="store.viewMode = 'elements'"
          >
            <IconLayers :size="14" />返回元素列表
          </button>
          <span v-if="store.elements.length" class="info">{{ store.filteredElements.length }}/{{ store.elements.length }} 元素</span>
          <ErrorState v-if="store.error" :message="store.error" @retry="store.clearError()" />
        </div>

        <!-- 数据筛选栏（合并表格：筛选作用于元素，搜索两类都生效） -->
        <div v-if="store.snapshot" class="filter-bar">
          <FilterTabs :tabs="filterOptions" v-model="store.filterMode" />
          <el-input
            v-model="store.searchText"
            size="small"
            placeholder="搜索 text / resource-id / class..."
            :allow-clear="true"
            class="filter-search"
          />
        </div>

        <!-- 工作区：左截图右表格 -->
        <div class="workspace">
          <section class="col col-phone">
            <ScreenshotView
              :screen-w="store.snapshot?.screen_w || 1440"
              :screen-h="store.snapshot?.screen_h || 3040"
              :elements="screenshotElements"
              :selected="store.selected"
              :ocr-results="store.ocrTexts"
              :selected-ocr="store.selectedOcr"
              :screenshot-path="store.snapshot?.screenshot_path || ''"
              @click-element="onElementClick"
              @click-ocr="onOcrClick"
            />
          </section>
          <section class="col col-elements">
            <PageElementsPanel
              v-if="store.viewMode === 'elements'"
              :rows="store.filteredRows"
              :selected="store.selected"
              :selected-ocr="store.selectedOcr"
              @select="onElementClick"
              @select-ocr="onOcrClick"
            />
            <StructureAnalysisPanel
              v-else
              :sections="store.analysis?.sections || []"
              :elements="store.analysis?.elements || []"
              :is-webview="store.analysis?.is_webview || false"
              :selected="store.selected"
              @select="onElementClick"
            />
          </section>
        </div>
      </section>
    </div>

    <footer class="inspector-footer">
      <span><IconClock :size="14" />就绪</span>
      <span><IconLayers :size="14" />{{ store.elements.length }} 元素 · {{ store.ocrTexts.length }} OCR</span>
      <span v-if="store.snapshot?.serial">{{ store.snapshot.serial }} · {{ store.snapshot.package || '—' }}</span>
    </footer>

    <SnapshotListDrawer />
    <SaveToElementsDialog />
    <SavedPagePicker />
  </div>
</template>

<style scoped>
.doc-page {
  display: flex; flex-direction: column; height: 100%; overflow: hidden;
  background: radial-gradient(circle, var(--app-paper-dot, #d4cdc0) 0.8px, transparent 0.8px);
  background-size: 14px 14px;
  background-color: var(--doodle-bg, #faf5ee);
}

.doc-body {
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
  padding: 24px 28px 28px;
  overflow: hidden;
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
  flex-shrink: 0;
  flex-wrap: wrap;
}

.filter-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
  flex-shrink: 0;
  flex-wrap: wrap;
  padding: 10px 14px;
  background: var(--app-bg-card);
  border: 3px solid var(--doodle-ink, #2d2d2d);
  border-radius: 6px 10px 6px 10px;
  box-shadow: 2px 2px 0 rgba(0, 0, 0, 0.04);
}

.filter-search { width: 260px; }

.info { font-size: var(--app-size-sm); color: var(--app-text-secondary); white-space: nowrap; }

.workspace {
  flex: 1;
  min-height: 0;
  width: 100%;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1.5fr);
  gap: 24px;
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

.col-elements { overflow-y: auto; }

@media (max-width: 1200px) {
  .workspace {
    grid-template-columns: 1fr;
    grid-template-rows: minmax(280px, 1fr) minmax(160px, auto);
    overflow-y: auto;
  }
}

.inspector-footer {
  display: flex; align-items: center; justify-content: center; gap: 24px;
  padding: 10px 20px; background: var(--app-highlight, #FFE066);
  border-top: 2.5px solid var(--app-ink, #2d2d2d);
  font-size: var(--app-size-sm); font-weight: 700;
  color: var(--app-footer-yellow-text); font-family: var(--app-font-display);
  flex-shrink: 0;
}
.inspector-footer span { display: flex; align-items: center; gap: 4px; font-size: var(--app-size-sm); }

.action-btn {
  display: inline-flex; align-items: center; gap: 4px;
  font-size: var(--app-size-xs); font-weight: 700; padding: 4px 12px;
  border: 2px solid var(--app-ink, #2d2d2d); border-radius: 4px 8px 4px 8px;
  background: var(--app-bg-card); color: var(--app-ink, #2d2d2d);
  cursor: pointer; font-family: inherit; transition: all 0.12s; white-space: nowrap; flex-shrink: 0;
}
.action-btn:hover:not(:disabled) { background: var(--app-highlight, #FFE066); }
.action-btn:disabled { opacity: 0.4; cursor: not-allowed; }
</style>
