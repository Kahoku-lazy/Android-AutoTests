<script setup>
/** Device Inspector — live device interaction: connect, dump UI, view XPath, save to element manager. */

import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { animate } from 'animejs'
import { useElementStore } from './store'
import DeviceSelector from './components/DeviceSelector.vue'
import ScreenshotView from './components/ScreenshotView.vue'
import PageElementsPanel from './components/PageElementsPanel.vue'
import WorkbenchHeader from '@/shared/components/WorkbenchHeader.vue'
import ErrorState from '@/shared/components/patterns/ErrorState.vue'
import FilterTabs from '@/shared/components/FilterTabs.vue'
import { IconRefresh, IconZap, IconClock, IconWifi, IconLayers, IconScan } from '@/shared/icons'

const store = useElementStore()
const screenshotRef = ref(null)
const screenRefreshing = ref(false)

let devicePollTimer = null
const wsDeviceSerial = ref('')
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
  try {
    await store.fetchDevices()
  } catch (e) {
    store.error = '加载设备列表失败，请检查网络连接'
    console.error(e)
  }
  // Periodic device list refresh (30s)
  devicePollTimer = setInterval(async () => {
    await store.fetchDevices()
    if (!store.isDeviceOnline && store.currentSerial) {
      store.error = `设备 ${store.currentSerial} 已离线`
    }
  }, 30000)
})

onUnmounted(() => {
  if (devicePollTimer) { clearInterval(devicePollTimer); devicePollTimer = null }
  store.disconnectDevice()
})

// ── Dump ──

async function doDump() {
  if (!store.isConnected) {
    store.error = '请先选择设备并点击"连接"'
    return
  }
  if (!store.isDeviceOnline) {
    store.error = `设备 ${store.currentSerial} 已离线`
    return
  }
  const result = await store.doDump()
  if (result?.status) {
    await nextTick()
    animate('.info', { opacity: [0,1], translateX: [-10,0], duration: 400, ease: 'outCubic' })
  }
}

async function refreshScreen() {
  if (!store.isConnected) {
    store.error = '请先选择设备并点击"连接"'
    return
  }
  if (!store.isDeviceOnline) {
    store.error = `设备 ${store.currentSerial} 已离线`
    return
  }
  screenRefreshing.value = true
  try {
    await screenshotRef.value?.refresh()
    await doDump()
  } finally {
    screenRefreshing.value = false
  }
}

// ── Element selection ──

function onElementClick(el) {
  store.selectElement(el)
}

function onOcrClick(ocr) {
  store.selectOcr(ocr)
}

// ── WebSocket device change ──

function onDeviceChanged(msg) {
  wsDeviceSerial.value = msg.serial
  if (msg.screen_w) store.screenW = msg.screen_w
  if (msg.screen_h) store.screenH = msg.screen_h
}

function onScreenshotUpdate({ url }) {
  store.screenshotUrl = url
}
</script>

<template>
  <div class="doc-page wb-shell">
    <WorkbenchHeader
      title="设备检查器 Device Inspector"
      subtitle="连接设备、Dump UI、生成 XPath 候选并保存到元素管理"
      icon="crosshair"
      icon-gradient="linear-gradient(135deg,#C9B6F2,#a78bfa)"
    />

    <div class="doc-body">
      <section class="inspector-section">
        <!-- Device bar + action buttons -->
        <div class="toolbar">
          <DeviceSelector />
          <button class="action-btn" :disabled="!store.isConnected || !store.isDeviceOnline" @click="refreshScreen"><IconRefresh :size="14" />刷新屏幕</button>
          <button class="action-btn action-btn--primary" :disabled="!store.isConnected || !store.isDeviceOnline" @click="doDump"><IconZap :size="14" />{{ store.loading ? 'Dumping...' : 'Dump UI' }}</button>
          <button class="action-btn" :disabled="store.ocrLoading || !store.isConnected || !store.isDeviceOnline" @click="store.doOcr"><IconScan :size="14" />{{ store.ocrLoading ? '识别中...' : 'OCR 检测' }}</button>
          <span v-if="store.elements.length" class="info">{{ store.filteredElements.length }}/{{ store.elements.length }} 元素</span>
          <ErrorState v-if="store.error" :message="store.error" @retry="() => { store.error = ''; doDump() }" />
        </div>

        <!-- Filter bar -->
        <div v-if="store.elements.length" class="filter-bar">
          <FilterTabs :tabs="filterOptions" v-model="store.filterMode" />
          <el-input v-model="store.searchText" size="small" placeholder="搜索 text / resource-id / class..." :allow-clear="true" class="filter-search" />
        </div>

        <!-- Workspace: 三栏 1:2:1 — 手机屏幕 | XPath 候选 | 详情 -->
        <div class="workspace">
          <section class="col col-phone">
            <ScreenshotView
              ref="screenshotRef"
              :active="store.isConnected"
              :screen-w="store.screenW"
              :screen-h="store.screenH"
              :elements="store.filteredElements"
              :selected="store.selected"
              :ocr-results="store.ocrResults"
              :selected-ocr="store.selectedOcr"
              @click-element="onElementClick"
              @click-ocr="onOcrClick"
              @device-changed="onDeviceChanged"
              @screenshot-update="onScreenshotUpdate"
            />
          </section>
          <section class="col col-elements">
            <PageElementsPanel />
          </section>
        </div>
      </section>
    </div>

    <footer class="inspector-footer">
      <span><IconClock :size="14" />就绪</span>
      <span><IconWifi :size="14" />{{ store.isConnected ? '已连接 '+store.connectedSerial : '未连接设备' }}</span>
      <span><IconLayers :size="14" />{{ store.actionable?.length || 0 }} 个元素</span>
    </footer>
  </div>
</template>

<style scoped>
.doc-page {
  display: flex;flex-direction: column;height: 100%;overflow: hidden;
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
  border-radius: 6px 10px 6px 10px; box-shadow: 2px 2px 0 rgba(0,0,0,0.04);
}

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
}

@media (max-width: 1200px) {
  .workspace {
    grid-template-columns: 1fr;
    grid-template-rows: minmax(280px, 1fr) minmax(160px, auto);
    overflow-y: auto;
  }
}

.inspector-footer { display:flex;align-items:center;justify-content:center;gap:24px;padding:10px 20px;background:var(--app-highlight,#FFE066);border-top:2.5px solid var(--app-ink,#2d2d2d);font-size:var(--app-size-sm);font-weight:700;color: var(--app-footer-yellow-text);font-family:var(--app-font-display);flex-shrink:0; }
.inspector-footer span{display:flex;align-items:center;gap:4px;font-size:var(--app-size-sm);}

.action-btn {
  display: inline-flex; align-items: center; gap: 4px;
  font-size: var(--app-size-xs); font-weight: 700; padding: 4px 12px;
  border: 2px solid var(--app-ink, #2d2d2d); border-radius: 4px 8px 4px 8px;
  background: var(--app-bg-card); color: var(--app-ink, #2d2d2d);
  cursor: pointer; font-family: inherit; transition: all 0.12s; white-space: nowrap; flex-shrink: 0;
}
.action-btn:hover:not(:disabled) { background: var(--app-highlight, #FFE066); }
.action-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.action-btn--primary { background: var(--app-ink, #2d2d2d); color: var(--app-bg-card); }
.action-btn--primary:hover:not(:disabled) { background: var(--app-ink, #2d2d2d); opacity: 0.85; }
</style>
