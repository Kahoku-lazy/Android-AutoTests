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

const route = useRoute()
const router = useRouter()
const store = useElementStore()
const screenshotRef = ref(null)
const screenRefreshing = ref(false)

const activeTab = ref('discovery')
const tabs = [
  { key: 'discovery', label: '🔍 设备发现' },
  { key: 'manage', label: '📋 元素管理' },
]

const pageMeta = computed(() =>
  activeTab.value === 'manage'
    ? {
        title: '元素管理 Element Manager',
        subtitle: '按页面组织元素库，维护 XPath、别名、测试点等定位信息',
      }
    : {
        title: '元素定位 Element Locator',
        subtitle: '连接设备、Dump UI、生成 XPath 候选并保存到元素管理',
      },
)

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
      mark="🎯"
    />

    <AppTabs :items="tabs" v-model="activeTab" :leaf-animation="true" :shadow="true" class="locator-tabs">
      <template #discovery>
        <div v-show="activeTab === 'discovery'" class="doc-body">
          <section class="doc-section locator-section">
            <!-- Toolbar -->
            <div class="toolbar">
              <DeviceSelector />
              <el-divider direction="vertical" />
              <el-button class="wb-btn"
                :icon="'Refresh'"
                :loading="screenRefreshing"
                :disabled="!store.isConnected || !store.isDeviceOnline"
                @click="refreshScreen"
              >
                刷新屏幕
              </el-button>
              <el-button class="wb-btn"
                type="primary"
                :loading="store.loading"
                :disabled="!store.isConnected || !store.isDeviceOnline"
                @click="doDump"
              >
                {{ store.loading ? 'Dumping...' : 'Dump UI' }}
              </el-button>
              <span v-if="store.pageId" class="info">
                {{ filteredElements.length }}/{{ store.elements.length }} 元素
              </span>
              <span v-if="store.error" class="error">{{ store.error }}</span>
            </div>

            <!-- Filter bar (visible after dump) -->
            <div v-if="store.pageId" class="filter-bar">
              <el-radio-group v-model="filterMode" size="small">
                <el-radio-button v-for="f in FILTER_OPTIONS" :key="f.value" :value="f.value">
                  {{ f.label }}
                </el-radio-button>
              </el-radio-group>
              <el-input
                v-model="searchText"
                size="small"
                placeholder="搜索 text / resource-id / class..."
                :allow-clear="true"
                style="width:260px"
              />
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
        <div v-show="activeTab === 'manage'">
          <ElementManager />
        </div>
      </template>
    </AppTabs>
  </div>
</template>

<style scoped>
.doc-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
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
  gap: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
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
  gap: 16px;
  margin-bottom: 16px;
  flex-shrink: 0;
  flex-wrap: wrap;
}

.filter-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
  flex-shrink: 0;
  flex-wrap: wrap;
  padding: 14px 18px;
  background: var(--ac-cream-deep, #f5ede0);
  border: 1px solid var(--ac-border, rgba(139, 115, 85, 0.16));
  border-radius: var(--ac-radius-sm, 10px);
}

.info { font-size: 14px; color: var(--app-text-secondary, #7A8B73); white-space: nowrap; }
.error { font-size: 14px; color: #e74c3c; white-space: nowrap; }

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
</style>
