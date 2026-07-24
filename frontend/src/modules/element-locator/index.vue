<script setup>

import AppTabs from "@/shared/components/AppTabs.vue";
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { animate } from 'animejs'
import { bus } from '@/shared/event-bus.js'
import client from '@/shared/api-client.js'
import { useElementStore } from './store.js'
import DeviceSelector from './components/DeviceSelector.vue'
import ScreenshotView from './components/ScreenshotView.vue'
import XPathCandidatePanel from './components/XPathCandidatePanel.vue'
import PageElementsPanel from './components/PageElementsPanel.vue'
import WorkbenchHeader from '@/shared/components/WorkbenchHeader.vue'
import ElementManager from './components/ElementManager.vue'
import WebElementManager from './components/WebElementManager.vue'
import ApiEndpointManager from './components/ApiEndpointManager.vue'

const route = useRoute()
const router = useRouter()
const store = useElementStore()
const screenshotRef = ref(null)
const screenRefreshing = ref(false)

const activeTab = ref('discovery')
const tabs = [
  { key: 'discovery', label: '🔍 设备元素获取' },
  { key: 'manage', label: '📋 Android元素管理' },
  { key: 'web', label: '🌐 Web端元素' },
  { key: 'api', label: '📡 API接口' },
]

const pageMeta = computed(() => {
  if (activeTab.value === 'manage') {
    return {
      title: 'Android元素管理 Android Element Manager',
      subtitle: '按页面组织元素库，维护 XPath、别名、测试点等定位信息',
    }
  }
  if (activeTab.value === 'web') {
    return {
      title: 'Web端元素管理 Web Element Manager',
      subtitle: '手动管理 Web 页面元素，支持 CSS/XPath/ID 等 12 种定位方式',
    }
  }
  if (activeTab.value === 'api') {
    return {
      title: 'API接口管理 API Endpoint Manager',
      subtitle: '管理 REST API 接口定义，配置请求体/响应体 JSON Schema',
    }
  }
  return {
    title: '元素定位 Element Locator',
    subtitle: '连接设备、Dump UI、生成 XPath 候选并保存到元素管理',
  }
})

let devicePollTimer = null
const wsDeviceSerial = ref('')
const filterMode = ref('all')

const FILTER_OPTIONS = [
  { value: 'all', label: '全部' },
  { value: 'clickable', label: '可点击' },
  { value: 'text', label: '有文本' },
  { value: 'rid', label: '有 Resource ID' },
  { value: 'clickable_text', label: '可点击+文本' },
  { value: 'clickable_no_text', label: '可点击无文本' },
  { value: 'input', label: '输入框' },
  { value: 'scrollable', label: '可滚动' },
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
  // Just load the device list — no auto-connect. User must manually select and connect.
  await store.fetchDevices()

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
  // Auto-disconnect on page leave
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
  if (result?.ok) {
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

// ── Action ──

async function doAction(action, x, y, text) {
  let ok
  if (action === 'input' && text) {
    ok = await client.post('/elements/action', { action: 'input', text, x, y, clear_first: true }).then(r => r.data.ok).catch(() => false)
  } else {
    ok = await store.doAction(action, x, y)
  }
  if (!ok) {
    await nextTick()
    animate('.error', { translateX: [0,-5,5,-3,3,0], duration: 400 })
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

// Keep tab state alive: force overlay redraw when switching back to discovery
watch(activeTab, async (tab) => {
  if (tab === 'discovery') {
    await nextTick()
    requestAnimationFrame(() => {
      screenshotRef.value?.redraw()
    })
  }
})
</script>

<template>
  <div class="doc-page wb-shell">
    <WorkbenchHeader
      :title="pageMeta.title"
      :subtitle="pageMeta.subtitle"
      icon="crosshair"
      icon-gradient="linear-gradient(135deg,#C9B6F2,#a78bfa)"
    />

    <AppTabs :items="tabs" v-model="activeTab" :leaf-animation="true" :shadow="true" class="locator-tabs">
      <template #discovery>
        <div v-show="activeTab === 'discovery'" class="doc-body">
          <section class="doc-section locator-section">
            <!-- Device bar + action buttons -->
            <div class="toolbar">
              <DeviceSelector />
              <button class="locator-action-btn" :disabled="!store.isConnected || !store.isDeviceOnline" @click="refreshScreen">↻ 刷新屏幕</button>
              <button class="locator-action-btn locator-action-btn--primary" :disabled="!store.isConnected || !store.isDeviceOnline" @click="doDump">{{ store.loading ? 'Dumping...' : '⚡ Dump UI' }}</button>
              <span v-if="store.pageId" class="info">{{ filteredElements.length }}/{{ store.elements.length }} 元素</span>
              <span v-if="store.error" class="error">{{ store.error }}</span>
            </div>

            <!-- Filter bar: custom Paper-style tabs -->
            <div v-if="store.pageId" class="filter-bar">
              <button v-for="f in FILTER_OPTIONS" :key="f.value" class="filter-tab" :class="{ active: filterMode === f.value }" @click="filterMode = f.value">{{ f.label }}</button>
              <el-input v-model="searchText" size="small" placeholder="搜索 text / resource-id / class..." :allow-clear="true" class="filter-search" />
            </div>

            <!-- Workspace: 三栏 1:2:1 — 手机屏幕 | XPath 候选 | 详情 -->
            <div class="workspace">
              <section class="col col-phone">
                <ScreenshotView
                  ref="screenshotRef"
                  :active="store.isConnected && activeTab === 'discovery'"
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
      </template>

      <template #manage>
        <div v-show="activeTab === 'manage'" class="doc-body">
          <ElementManager />
        </div>
      </template>

      <template #web>
        <div v-show="activeTab === 'web'" class="doc-body">
          <WebElementManager />
        </div>
      </template>

      <template #api>
        <div v-show="activeTab === 'api'" class="doc-body">
          <ApiEndpointManager />
        </div>
      </template>
    </AppTabs>
    <footer class="locator-footer">
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

.locator-tabs {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  margin-top: 12px;
}

.doc-page :deep(.locator-tabs.el-tabs) {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.doc-page :deep(.locator-tabs.el-tabs > .el-tabs__content) {
  flex: 1;
  min-height: 0;
  width: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  padding-top: 8px;
}
.doc-page :deep(.locator-tabs.el-tabs > .el-tabs__content > .el-tab-pane) {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.doc-page :deep(.locator-tabs.el-tabs > .el-tabs__header) {
  margin: 0 0 8px;
  width: 100%;
}
.doc-page :deep(.locator-tabs .el-tabs__nav-wrap),
.doc-page :deep(.locator-tabs .el-tabs__nav-scroll) {
  width: 100%;
}
.doc-page :deep(.locator-tabs .el-tabs__nav) {
  display: flex;
  width: 100%;
  box-sizing: border-box;
  border-radius: var(--app-radius-md);
}
.doc-page :deep(.locator-tabs .el-tabs__item) {
  flex: 1;
  width: auto;
  max-width: none;
  justify-content: center;
  text-align: center;
  height: 40px;
  padding: 0 12px;
  border-radius: var(--app-radius-sm);
}

.doc-page :deep(.locator-tabs.el-tabs > .el-tabs__content > .el-tab-pane) {
  flex: 1;
  min-height: 0;
  width: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.doc-page :deep(.locator-tabs.el-tabs > .el-tabs__content > .el-tab-pane > .doc-body) {
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

.locator-section {
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
  background: #fff;
  border: 3px solid var(--doodle-ink, #2d2d2d);
  border-radius: 6px 10px 6px 10px; box-shadow: 2px 2px 0 rgba(0,0,0,0.04);
}

.info { font-size: var(--app-size-sm); color: var(--app-text-secondary, #7A8B73); white-space: nowrap; }
.error { font-size: var(--app-size-sm); color: var(--el-color-danger, #FFB5A7); white-space: nowrap; }

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

.locator-footer { display:flex;align-items:center;justify-content:center;gap:24px;padding:10px 20px;background:var(--app-highlight,#FFE066);border-top:2.5px solid var(--app-ink,#2d2d2d);font-size:var(--app-size-sm);font-weight:700;color:#5a4e20;font-family:'Patrick Hand',cursive;flex-shrink:0; }
.locator-footer span{display:flex;align-items:center;gap:4px;font-size:var(--app-size-sm);}

/* Paper × Polaroid — 覆盖 AppTabs 玻璃态 */
.locator-tabs :deep(.el-tabs__nav) {
  gap: 0 !important; padding: 0 !important;
  border-radius: 0 !important;
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
}
.locator-tabs :deep(.el-tabs__item) {
  height: 36px !important; padding: 0 20px !important;
  border-radius: 4px 8px 0 0 !important;
  color: var(--app-ink-muted, #999) !important;
  font-weight: 700 !important; font-size: var(--app-size-sm) !important;
  border: 2px solid transparent !important;
  background: transparent !important;
}
.locator-tabs :deep(.el-tabs__item:hover) {
  color: var(--app-ink, #2d2d2d) !important;
  background: rgba(0,0,0,0.03) !important;
}
.locator-tabs :deep(.el-tabs__item.is-active) {
  color: var(--app-ink, #2d2d2d) !important;
  background: #fff !important;
  border-color: var(--app-ink, #2d2d2d) !important;
  border-bottom-color: #fff !important;
}
.locator-tabs :deep(.el-tabs__active-bar) {
  display: none !important;
}
.locator-tabs :deep(.el-tabs__header) {
  border-bottom: 2px solid var(--app-ink, #2d2d2d) !important;
  margin-bottom: 0 !important;
}
</style>
