<script setup>
/** Device Inspector — live device interaction: connect, dump UI, view XPath, save to element manager. */

import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { animate } from 'animejs'
import { bus } from '@/shared/event-bus'
import { useElementStore } from './store'
import { apiInput } from './api'
import DeviceSelector from './components/DeviceSelector.vue'
import ScreenshotView from './components/ScreenshotView.vue'
import XPathCandidatePanel from './components/XPathCandidatePanel.vue'
import PageElementsPanel from './components/PageElementsPanel.vue'
import WorkbenchHeader from '@/shared/components/WorkbenchHeader.vue'
import ErrorState from '@/shared/components/patterns/ErrorState.vue'
import FilterTabs from '@/shared/components/FilterTabs.vue'

const store = useElementStore()
const screenshotRef = ref(null)
const screenRefreshing = ref(false)

let devicePollTimer = null
const wsDeviceSerial = ref('')
const filterMode = ref('all')

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

const searchText = ref('')

const filteredElements = computed(() => {
  let els = store.actionable || []
  // Filter by mode
  switch (filterMode.value) {
    case 'clickable':       els = els.filter(e => e.clickable); break
    case 'text':            els = els.filter(e => e.text); break
    case 'rid':             els = els.filter(e => e.resource_id); break
    case 'clickable_text':  els = els.filter(e => e.clickable && e.text); break
    case 'clickable_no_text': els = els.filter(e => e.clickable && !e.text); break
    case 'input':           els = els.filter(e => e.class_name?.toLowerCase().includes('edit')); break
    case 'scrollable':      els = els.filter(e => e.scrollable); break
  }
  // Filter by search text
  if (searchText.value.trim()) {
    const q = searchText.value.trim().toLowerCase()
    els = els.filter(e =>
      (e.text || '').toLowerCase().includes(q) ||
      (e.resource_id || '').toLowerCase().includes(q) ||
      (e.content_desc || '').toLowerCase().includes(q) ||
      (e.class_name || '').toLowerCase().includes(q)
    )
  }
  return els
})

onMounted(async () => {
  try {
    await store.fetchDevices()
  } catch (e) {
    store.message = '加载设备列表失败，请检查网络连接'
    console.error(e)
  }
  // Periodic device list refresh (30s)
  devicePollTimer = setInterval(async () => {
    await store.fetchDevices()
    if (!store.isDeviceOnline && store.currentSerial) {
      store.message = `设备 ${store.currentSerial} 已离线`
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
    store.message = '请先选择设备并点击"连接"'
    return
  }
  if (!store.isDeviceOnline) {
    store.message = `设备 ${store.currentSerial} 已离线`
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
    store.message = '请先选择设备并点击"连接"'
    return
  }
  if (!store.isDeviceOnline) {
    store.message = `设备 ${store.currentSerial} 已离线`
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

// ── Action ──

async function doAction(action, x, y, text) {
  let ok
  if (action === 'input' && text) {
    ok = await apiInput(text, x, y, true).then(r => r.data.status).catch(() => false)
  } else {
    ok = await store.doAction(action, x, y)
  }
  if (!ok) {
    await nextTick()
    animate('.message', { translateX: [0,-5,5,-3,3,0], duration: 400 })
  }
}

// ── Element selection ──

function onElementClick(el) {
  store.selectElement(el)
  nextTick(() => {
    animate('.col-xpath', { opacity: [0.85, 1], duration: 300, ease: 'outCubic' })
  })
}

function onAddStep(xp) {
  const xpathSnippet = (xp.xpath || '').length > 50 ? xp.xpath.slice(0, 47) + '...' : xp.xpath
  bus.emit('add-step-to-case', {
    type: xp.type || 'resource-id',
    xpath: xp.xpath || '',
    description: `${xp.type}: ${xpathSnippet}`,
  })
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
          <button class="action-btn" :disabled="!store.isConnected || !store.isDeviceOnline" @click="refreshScreen">↻ 刷新屏幕</button>
          <button class="action-btn action-btn--primary" :disabled="!store.isConnected || !store.isDeviceOnline" @click="doDump">{{ store.loading ? 'Dumping...' : '⚡ Dump UI' }}</button>
          <span v-if="store.pageId" class="info">{{ filteredElements.length }}/{{ store.elements.length }} 元素</span>
          <ErrorState v-if="store.message" :message="store.message" @retry="() => { store.message = ''; doDump() }" />
        </div>

        <!-- Filter bar -->
        <div v-if="store.pageId" class="filter-bar">
          <FilterTabs :tabs="filterOptions" v-model="filterMode" />
          <el-input v-model="searchText" size="small" placeholder="搜索 text / resource-id / class..." :allow-clear="true" class="filter-search" />
        </div>

        <!-- Workspace: 三栏 1:2:1 — 手机屏幕 | XPath 候选 | 详情 -->
        <div class="workspace">
          <section class="col col-phone">
            <ScreenshotView
              ref="screenshotRef"
              :active="store.isConnected"
              :screen-w="store.screenW"
              :screen-h="store.screenH"
              :elements="filteredElements"
              :selected="store.selected"
              @click-element="onElementClick"
              @do-action="doAction"
              @device-changed="onDeviceChanged"
              @screenshot-update="onScreenshotUpdate"
            />
          </section>
          <section class="col col-xpath">
            <XPathCandidatePanel
              :element="store.selected"
              @add-step="onAddStep"
              @do-action="doAction"
            />
          </section>
          <section class="col col-elements">
            <PageElementsPanel />
          </section>
        </div>
      </section>
    </div>

    <footer class="inspector-footer">
      <span>🕐 就绪</span>
      <span>📡 {{ store.isConnected ? '已连接 '+store.connectedSerial : '未连接设备' }}</span>
      <span>📋 {{ store.actionable?.length || 0 }} 个元素</span>
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

.info { font-size: var(--app-size-sm); color: var(--app-text-secondary, #7A8B73); white-space: nowrap; }
.message { font-size: var(--app-size-sm); color: var(--el-color-danger, #FFB5A7); white-space: nowrap; }

.workspace {
  flex: 1;
  min-height: 420px;
  width: 100%;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1.5fr) minmax(0, 1.35fr);
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
    grid-template-rows: minmax(280px, 1fr) minmax(200px, auto) minmax(160px, auto);
    overflow-y: auto;
  }
}

.inspector-footer { display:flex;align-items:center;justify-content:center;gap:24px;padding:10px 20px;background:var(--app-highlight,#FFE066);border-top:2.5px solid var(--app-ink,#2d2d2d);font-size:var(--app-size-sm);font-weight:700;color:#5a4e20;font-family:'Patrick Hand',cursive;flex-shrink:0; }
.inspector-footer span{display:flex;align-items:center;gap:4px;font-size:var(--app-size-sm);}
</style>
