<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import type { CatalogPage } from '@/modules/workflow/data/pageCatalog'
import { fetchCatalogPages } from '@/modules/workflow/data/pageCatalog'

const props = defineProps<{
  show: boolean
  x: number
  y: number
  nodeId: string
  nodeLabel: string
  canLinkPage?: boolean
  linkedPageId?: string
  linkedPageName?: string
}>()

const emit = defineEmits<{
  close: []
  linkPage: [page: CatalogPage]
  resyncPage: []
  deleteNode: []
}>()

const mode = ref<'menu' | 'link'>('menu')
const pages = ref<CatalogPage[]>([])
const source = ref<'api' | 'mock'>('mock')
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

function openLink() {
  mode.value = 'link'
  loadPages()
}

function selectPage(page: CatalogPage) {
  emit('linkPage', page)
  emit('close')
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
  if (!q) return pages.value
  return pages.value.filter(
    p => p.name.toLowerCase().includes(q) || (p.description || '').toLowerCase().includes(q)
  )
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
        <button
          v-if="canLinkPage !== false"
          class="menu-item"
          @click="openLink"
        >
          <span>🔗</span> 关联元素管理页面…
        </button>
        <button
          v-if="linkedPageId"
          class="menu-item"
          @click="doResync"
        >
          <span>🔄</span> 刷新元素目录
        </button>
        <div v-else-if="canLinkPage === false" class="menu-hint">该节点不支持关联页面</div>
        <button class="menu-item danger" @click="doDelete">
          <span>🗑</span> 删除节点
        </button>
      </template>

      <!-- Link page picker -->
      <template v-else>
        <div class="menu-header">
          <button class="back" @click="mode = 'menu'">←</button>
          <span>选择要关联的页面</span>
        </div>
        <input
          v-model="search"
          class="search"
          placeholder="搜索页面…"
          autofocus
          @keydown.escape="$emit('close')"
        />
        <div class="source-tag">
          数据源: {{ source === 'api' ? '元素管理 API' : 'Demo Mock' }}
        </div>
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
            <div class="page-name">
              {{ p.name }}
              <span v-if="p.id === linkedPageId" class="badge">当前</span>
            </div>
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
  background: rgba(255,255,255,0.78);
  border: 1px solid var(--app-glass-border);
  border-radius: 16px;
  box-shadow: var(--app-shadow-lg);
  backdrop-filter: blur(var(--app-glass-blur));
  -webkit-backdrop-filter: blur(var(--app-glass-blur));
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
  border: 1.5px solid var(--app-glass-border);
  background: rgba(255,255,255,0.44);
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
  border: 1.5px solid var(--app-glass-border);
  border-radius: 12px;
  background: rgba(255,255,255,0.44);
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
