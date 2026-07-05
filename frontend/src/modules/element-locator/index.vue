<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { animate } from 'animejs'
import { bus } from '@/shared/event-bus.js'
import client from '@/shared/api-client.js'
import { useElementStore } from './store.js'
import { Tabs, Select as AnimalSelect, Input } from 'animal-island-vue'
import DeviceSelector from './components/DeviceSelector.vue'
import ScreenshotView from './components/ScreenshotView.vue'
import XPathCandidatePanel from './components/XPathCandidatePanel.vue'
import ElementDetailPanel from './components/ElementDetailPanel.vue'
import PageHeader from '@/shared/components/PageHeader.vue'
import ElementManager from './components/ElementManager.vue'

const route = useRoute()
const router = useRouter()
const store = useElementStore()

const activeTab = ref('discovery')
const tabs = [
  { key: 'discovery', label: '🔍 设备发现' },
  { key: 'manage', label: '📋 元素管理' },
]

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
  const { serial, autoStart } = route.query

  // Device list + optional activate in parallel where possible
  await store.fetchDevices()
  if (serial) {
    await store.activateDevice(serial)
  } else if (!store.currentDevice?.screen_w) {
    // Non-blocking: WS device_changed will also supply dimensions
    store.fetchCurrentDevice()
  }

  if (autoStart === '1' && store.currentSerial) {
    nextTick(() => store.doDump())
  }

  // Periodic device list refresh (30s)
  devicePollTimer = setInterval(async () => {
    await store.fetchDevices()
    // Check if current device went offline
    if (!store.isDeviceOnline && store.currentSerial) {
      store.error = `设备 ${store.currentSerial} 已离线`
    }
  }, 30000)
})

onUnmounted(() => {
  if (devicePollTimer) { clearInterval(devicePollTimer); devicePollTimer = null }
})

// ── Dump ──

async function doDump() {
  if (!store.currentSerial) {
    store.error = '请先选择设备'
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
</script>

<template>
  <div class="doc-page">
    <PageHeader
      title="元素定位 Element Locator"
      subtitle="连接设备、Dump UI、生成 XPath 候选并保存到元素管理"
      color="app-yellow"
    />

    <Tabs :items="tabs" v-model="activeTab" :leaf-animation="true" :shadow="true">
      <template #discovery>
        <div class="doc-body">
          <section class="doc-section locator-section">
            <!-- Toolbar -->
            <div class="toolbar">
              <DeviceSelector />
              <el-divider direction="vertical" />
              <el-button
                type="primary"
                :loading="store.loading"
                :disabled="!store.currentSerial || !store.isDeviceOnline"
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
              <Input
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
                  :screen-w="store.screenW"
                  :screen-h="store.screenH"
                  :elements="filteredElements"
                  :selected="store.selected"
                  @click-element="onElementClick"
                  @do-action="doAction"
                  @device-changed="onDeviceChanged"
                />
              </section>
              <section class="col col-xpath">
                <XPathCandidatePanel
                  :element="store.selected"
                  @add-step="onAddStep"
                  @do-action="doAction"
                />
              </section>
              <section class="col col-detail">
                <ElementDetailPanel :element="store.selected" />
              </section>
            </div>
          </section>
        </div>
      </template>

      <template #manage>
        <ElementManager />
      </template>
    </Tabs>
  </div>
</template>

<style scoped>
.doc-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: calc(100vh - 0px);
}
.locator-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding: 16px 20px 20px;
}
.toolbar {
  display: flex; align-items: center; gap: 12px;
  margin-bottom: 10px; flex-shrink: 0; flex-wrap: wrap;
}
.filter-bar {
  display: flex; align-items: center; gap: 12px;
  margin-bottom: 14px; flex-shrink: 0; flex-wrap: wrap;
  padding: 10px 14px;
  background: var(--animal-bg-color-secondary, #f0e8d8);
  border-radius: 10px;
}
.info { font-size: 14px; color: var(--text-secondary); white-space: nowrap; }
.error { font-size: 14px; color: #e74c3c; white-space: nowrap; }
.workspace {
  flex: 1;
  display: grid;
  grid-template-columns: minmax(260px, 1fr) minmax(360px, 2fr) minmax(260px, 1fr);
  gap: 16px;
  min-height: 480px;
}
.col {
  min-height: 0;
  min-width: 0;
  display: flex;
  flex-direction: column;
}
.col-phone {
  max-width: 420px;
  height: 100%;
}
</style>
