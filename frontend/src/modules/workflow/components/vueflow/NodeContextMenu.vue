<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import type { CatalogPage, ApiEndpointRef } from '@/modules/workflow/data/pageCatalog'
import { fetchCatalogPages, fetchApiEndpoints } from '@/modules/workflow/data/pageCatalog'

const props = defineProps<{
  show: boolean
  x: number
  y: number
  nodeId: string
  nodeLabel: string
  nodeType?: string
  canLinkPage?: boolean
  linkedPageId?: string
  linkedPageName?: string
}>()

const emit = defineEmits<{
  close: []
  linkPage: [page: CatalogPage]
  linkApi: [endpoint: ApiEndpointRef]
  resyncPage: []
  deleteNode: []
}>()

const mode = ref<'menu' | 'link' | 'api'>('menu')
const apiEndpoints = ref<ApiEndpointRef[]>([])
const apiSearch = ref('')
const pickerDomain = ref<'android' | 'web'>('android')
const pages = ref<CatalogPage[]>([])
const catalogError = ref('')
const loading = ref(false)
const search = ref('')
const menuRef = ref<HTMLDivElement | null>(null)

async function loadPages() {
  loading.value = true
  catalogError.value = ''
  try {
    const res = await fetchCatalogPages()
    pages.value = res.pages
    source.value = res.source
    if (res.error) catalogError.value = res.error
  } finally {
    loading.value = false
  }
}

watch(
  () => props.show,
  (v) => {
    if (v) {
      mode.value = 'menu'
      search.value = ''
      setTimeout(() => document.addEventListener('click', onOutside), 0)
    } else {
      document.removeEventListener('click', onOutside)
    }
  }
)

function onOutside(e: MouseEvent) {
  if (menuRef.value && !menuRef.value.contains(e.target as Node)) {
    emit('close')
  }
}

function openLink(domain: 'android' | 'web') {
  pickerDomain.value = domain
  mode.value = 'link'
  search.value = ''
  loadPages()
}

function selectPage(page: CatalogPage) {
  emit('linkPage', page)
  emit('close')
}

async function openApiPicker() {
  mode.value = 'api'
  loading.value = true
  try { apiEndpoints.value = await fetchApiEndpoints() } catch { apiEndpoints.value = [] }
  loading.value = false
}

function selectApi(ep: ApiEndpointRef) {
  emit('linkApi', ep)
  emit('close')
}

function apiFiltered() {
  const q = apiSearch.value.trim().toLowerCase()
  if (!q) return apiEndpoints.value
  return apiEndpoints.value.filter(e =>
    e.name.toLowerCase().includes(q) || e.url.toLowerCase().includes(q) || e.method.toLowerCase().includes(q)
  )
}

function doDelete() {
  if (!confirm(`确定删除节点「${props.nodeLabel}」？相关连线也会删除。`)) return
  emit('deleteNode')
  emit('close')
}

function doResync() {
  emit('resyncPage')
  emit('close')
}

const filtered = () => {
  const q = search.value.trim().toLowerCase()
  let list = pages.value.filter(p => p.domain === pickerDomain.value)
  if (q) list = list.filter(p =>
    p.name.toLowerCase().includes(q) || (p.description || '').toLowerCase().includes(q)
  )
  return list
}

onMounted(() => {
  if (props.show) loadPages()
})
</script>

<template>
  <Teleport to="body">
    <div
      v-if="show"
      ref="menuRef"
      class="node-menu"
      :style="{ left: x + 'px', top: y + 'px' }"
      @click.stop
    >
      <!-- Root menu -->
      <template v-if="mode === 'menu'">
        <div class="menu-title">{{ nodeLabel }}</div>
        <div v-if="linkedPageName" class="menu-hint">已关联: {{ linkedPageName }}</div>

        <!-- Page node: Android / Web -->
        <template v-if="nodeType !== 'ApiNode' && canLinkPage !== false">
          <button class="menu-item" @click="openLink('android')"><span>📱</span> 关联 Android 页面…</button>
          <button class="menu-item" @click="openLink('web')"><span>🌐</span> 关联 Web 页面…</button>
        </template>

        <!-- API node: link API endpoint -->
        <template v-if="nodeType === 'ApiNode'">
          <button class="menu-item" @click="openApiPicker"><span>📡</span> 关联 API 接口…</button>
        </template>

        <button v-if="linkedPageId" class="menu-item" @click="doResync"><span>🔄</span> 刷新元素目录</button>
        <button class="menu-item danger" @click="doDelete"><span>🗑</span> 删除节点</button>
      </template>

      <!-- API endpoint picker -->
      <template v-else-if="mode === 'api'">
        <div class="menu-header">
          <button class="back" @click="mode = 'menu'">←</button>
          <span>选择 API 接口</span>
        </div>
        <input v-model="apiSearch" class="search" placeholder="搜索接口…" autofocus @keydown.escape="$emit('close')" />
        <div v-if="loading" class="empty">加载中…</div>
        <div v-else class="list">
          <button v-for="ep in apiFiltered()" :key="ep.id" class="page-item" @click="selectApi(ep)">
            <div class="page-name">{{ ep.name }}</div>
            <div class="page-meta">
              <span :style="'display:inline-block;padding:1px 6px;border-radius:4px;font-size:9px;font-weight:700;color:#fff;background:' + (ep.method === 'GET' ? '#6fba2c' : ep.method === 'POST' ? '#889df0' : '#8b7355')">{{ ep.method }}</span>
              {{ ep.url }}
            </div>
          </button>
          <div v-if="!apiFiltered().length" class="empty">无 API 接口，请先在元素定位中添加</div>
        </div>
      </template>

      <!-- Link page picker -->
      <template v-else>
        <div class="menu-header">
          <button class="back" @click="mode = 'menu'">←</button>
          <span>选择 {{ pickerDomain === 'android' ? 'Android' : 'Web' }} 页面</span>
        </div>
        <input
          v-model="search"
          class="search"
          placeholder="搜索页面…"
          autofocus
          @keydown.escape="$emit('close')"
        />
        <div v-if="catalogError" class="empty">API 提示: {{ catalogError }}</div>
        <div v-if="loading" class="empty">加载中…</div>
        <div v-else class="list">
          <button
            v-for="p in filtered()"
            :key="p.id"
            class="page-item"
            :class="{ active: p.id === linkedPageId }"
            @click="selectPage(p)"
          >
            <div class="page-name">{{ p.name }}<span v-if="p.id === linkedPageId" class="badge">当前</span></div>
            <div class="page-meta">{{ p.elements.length }} 个元素 · {{ p.description || p.package || '—' }}</div>
          </button>
          <div v-if="!filtered().length" class="empty">无匹配页面</div>
        </div>
      </template>
    </div>
  </Teleport>
</template>

<style scoped>
.node-menu {
  position: fixed;
  z-index: 400;
  width: 280px;
  max-height: 380px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: #fff;
  border: 1px solid var(--doodle-ink, #2d2d2d);
  border-radius: 16px;
  box-shadow: var(--app-shadow-lg);
  padding: 8px;
  font-family: var(--ac-font, system-ui, sans-serif);
}
.menu-title {
  font-size: 13px;
  font-weight: 800;
  color: var(--app-text);
  padding: 6px 8px 2px;
}
.menu-hint {
  font-size: 10px;
  color: var(--app-green-deep);
  font-weight: 700;
  padding: 0 8px 8px;
}
.menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 10px 12px;
  border: none;
  border-radius: 12px;
  background: transparent;
  color: var(--ac-ink-muted, #5c4a35);
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  text-align: left;
  font-family: inherit;
}
.menu-item:hover {
  background: rgba(162,210,255,0.16);
  color: var(--app-green-deep);
}
.menu-item.danger:hover {
  background: rgba(232, 95, 95, 0.12);
  color: #c44a4a;
}
.menu-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 6px 8px;
  font-size: 13px;
  font-weight: 800;
  color: var(--app-text);
}
.back {
  border: 1.5px solid var(--doodle-ink, #2d2d2d);
  background: #fff;
  color: var(--ac-ink-muted, #5c4a35);
  border-radius: 10px;
  width: 28px;
  height: 28px;
  cursor: pointer;
  font-weight: 700;
}
.search {
  margin: 0 4px 6px;
  padding: 8px 10px;
  border: 1.5px solid var(--doodle-ink, #2d2d2d);
  border-radius: 12px;
  background: #fff;
  color: var(--app-text);
  font-size: 12px;
  outline: none;
  font-family: inherit;
}
.search:focus { border-color: var(--app-blue); }
.source-tag {
  font-size: 10px;
  color: var(--app-text-secondary);
  font-weight: 600;
  padding: 0 8px 6px;
}
.list {
  overflow-y: auto;
  max-height: 260px;
}
.page-item {
  width: 100%;
  text-align: left;
  padding: 10px 12px;
  border: none;
  border-radius: 12px;
  background: transparent;
  color: var(--app-text);
  cursor: pointer;
  font-family: inherit;
}
.page-item:hover { background: rgba(162,210,255,0.12); }
.page-item.active { background: rgba(162,210,255,0.18); }
.page-name {
  font-size: 13px;
  font-weight: 800;
  display: flex;
  align-items: center;
  gap: 6px;
}
.badge {
  font-size: 9px;
  color: #fff;
  background: var(--app-green-deep);
  border-radius: 6px;
  padding: 1px 6px;
  font-weight: 700;
}
.page-meta {
  font-size: 10px;
  color: var(--app-text-secondary);
  margin-top: 3px;
  font-weight: 600;
}
.empty {
  padding: 18px;
  text-align: center;
  font-size: 12px;
  color: var(--app-text-secondary);
}
</style>
