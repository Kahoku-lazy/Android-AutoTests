<script setup>
import { ref, computed, watch, nextTick, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { animate } from 'animejs'
import client, { formatApiError } from '@/shared/api-client.js'
import { useElementStore } from '../store.js'
import { bus } from '@/shared/event-bus.js'

const store = useElementStore()

// ── Static thumbnail screenshot (captured at dump time, NOT live stream) ──
const thumbnailUrl = ref('')
const thumbnailLoading = ref(false)
const imgNaturalW = ref(0)
const imgNaturalH = ref(0)

/** Load image dimensions from a url */
function loadImageDims(url) {
  const img = new Image()
  img.onload = () => {
    imgNaturalW.value = img.naturalWidth
    imgNaturalH.value = img.naturalHeight
  }
  img.src = url
}

/** Fetch one-frame screenshot and store for thumbnails */
async function captureThumbnailScreenshot() {
  try {
    const { data } = await client.get('/elements/screenshot')
    if (data.ok && data.image) {
      // Use data URL directly — browser decodes natively
      const url = `data:image/${data.format || 'jpeg'};base64,${data.image}`
      thumbnailUrl.value = url
      loadImageDims(url)
      return true
    }
  } catch (_) { /* ignore */ }
  return false
}

// Auto-capture thumbnail screenshot when a new dump arrives (toolbar or refresh)
watch(() => store.lastDump, async (dump) => {
  if (dump) await captureThumbnailScreenshot()
})

// ── Refresh elements (re-dump) ──
const refreshLoading = ref(false)

async function refreshElements() {
  if (!store.isConnected) {
    ElMessage.warning('请先连接设备')
    return
  }
  refreshLoading.value = true
  try {
    await captureThumbnailScreenshot()
    const result = await store.doDump()
    if (!result?.ok) ElMessage.error('Dump 失败')
  } catch (e) {
    ElMessage.error('刷新失败')
  } finally {
    refreshLoading.value = false
  }
}

onUnmounted(() => {
  thumbnailUrl.value = ''
})

// ── Selection state ──
const checkedIds = ref(new Set())

function toggleCheck(el) {
  const id = el._idx ?? el.__uid
  const next = new Set(checkedIds.value)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  checkedIds.value = next
}

function toggleAll() {
  if (checkedIds.value.size === store.elements.length) {
    checkedIds.value = new Set()
  } else {
    checkedIds.value = new Set(store.elements.map(e => e._idx ?? e.__uid))
  }
}

const allChecked = computed(() =>
  store.elements.length > 0 && checkedIds.value.size === store.elements.length
)

const checkedCount = computed(() => checkedIds.value.size)

function getElId(el) {
  return el._idx ?? el.__uid
}

// ── Row click → select element (same as screen click) ──
function onRowClick(el) {
  store.selectElement(el)
  nextTick(() => {
    animate('.col-xpath', { opacity: [0.85, 1], duration: 300, ease: 'outCubic' })
  })
}

// ── Thumbnail: proportional fit in fixed container ──
const THUMB_SIZE = 48
const THUMB_PAD = 2

function thumbStyle(el) {
  if (!thumbnailUrl.value || !imgNaturalW.value || !imgNaturalH.value || !store.screenW) return {}
  const w = Math.max(el.width || 1, 1)
  const h = Math.max(el.height || 1, 1)
  const scaleX = imgNaturalW.value / store.screenW
  const scaleY = imgNaturalH.value / store.screenH
  const ew = w * scaleX
  const eh = h * scaleY
  const ex = el.x * scaleX
  const ey = el.y * scaleY
  // Fit element proportionally within container
  const inner = THUMB_SIZE - 2 * THUMB_PAD
  const fit = Math.min(inner / ew, inner / eh)
  const bgW = imgNaturalW.value * fit
  const bgH = imgNaturalH.value * fit
  const cx = ex + ew / 2
  const cy = ey + eh / 2
  return {
    width: `${THUMB_SIZE}px`,
    height: `${THUMB_SIZE}px`,
    backgroundImage: `url(${thumbnailUrl.value})`,
    backgroundSize: `${Math.round(bgW)}px ${Math.round(bgH)}px`,
    backgroundPosition: `${Math.round(-(cx * fit - THUMB_SIZE / 2))}px ${Math.round(-(cy * fit - THUMB_SIZE / 2))}px`,
  }
}

// ── Click thumbnail to enlarge ──
const enlargeVisible = ref(false)
const enlargeEl = ref(null)
const ENLARGE_SIZE = 240

function openEnlarge(el) {
  enlargeEl.value = el
  enlargeVisible.value = true
}

function enlargeStyle(el) {
  if (!thumbnailUrl.value || !imgNaturalW.value || !store.screenW) return {}
  const w = Math.max(el.width || 1, 1)
  const h = Math.max(el.height || 1, 1)
  const scaleX = imgNaturalW.value / store.screenW
  const scaleY = imgNaturalH.value / store.screenH
  const ew = w * scaleX; const eh = h * scaleY
  const ex = el.x * scaleX; const ey = el.y * scaleY
  const fit = Math.min(ENLARGE_SIZE / ew, ENLARGE_SIZE / eh)
  const bgW = imgNaturalW.value * fit; const bgH = imgNaturalH.value * fit
  const cx = ex + ew / 2; const cy = ey + eh / 2
  return {
    width: `${ENLARGE_SIZE}px`,
    height: `${ENLARGE_SIZE}px`,
    backgroundImage: `url(${thumbnailUrl.value})`,
    backgroundSize: `${Math.round(bgW)}px ${Math.round(bgH)}px`,
    backgroundPosition: `${Math.round(-(cx * fit - ENLARGE_SIZE / 2))}px ${Math.round(-(cy * fit - ENLARGE_SIZE / 2))}px`,
  }
}

// ── Batch save dialog ──
const batchSaveVisible = ref(false)
const pagesLoading = ref(false)
const saving = ref(false)
const pages = ref([])
const batchSaveForm = ref({ pageId: null, strategy: 'resource-id' })

const STRATEGY_OPTIONS = [
  { value: 'resource-id', label: 'resource-id' },
  { value: 'text', label: 'text' },
  { value: 'content-desc', label: 'content-desc' },
  { value: 'class', label: 'class' },
  { value: 'combined', label: 'resource-id + text' },
  { value: 'resource-id (any)', label: 'resource-id (任意 class)' },
  { value: 'text (any)', label: 'text (任意 class)' },
]

function pageLabel(p) {
  return p.label || `Page #${p.id}`
}

async function openBatchSave() {
  if (checkedIds.value.size === 0) {
    ElMessage.warning('请先勾选要保存的元素')
    return
  }
  // Show dialog immediately, then load pages asynchronously
  batchSaveVisible.value = true
  batchSaveForm.value = {
    pageId: null,
    strategy: 'resource-id',
  }
  pagesLoading.value = true
  try {
    const { data } = await client.get('/elements/pages')
    if (data.ok) pages.value = data.pages || []
  } catch (e) {
    ElMessage.error({ message: formatApiError(e, '加载页面列表失败'), duration: 4000, showClose: true })
  } finally {
    pagesLoading.value = false
  }
  // Set default page after loading
  batchSaveForm.value.pageId = pages.value.find(p => !p.is_folder)?.id || null
  if (!batchSaveForm.value.pageId) {
    try {
      const pkg = store.lastDump?.package || store.currentDevice?.package || ''
      const activity = store.lastDump?.activity || ''
      const { data } = await client.post('/elements/pages/create', {
        label: `Page_${new Date().toISOString().slice(0, 10)}`,
        package: pkg,
        activity,
      })
      if (data.ok) {
        const page = data.page || {}
        batchSaveForm.value.pageId = page.id
        pages.value.push({ id: page.id, label: page.label || data.label })
      } else {
        ElMessage.error(data.error || '自动创建页面失败')
      }
    } catch (e) {
      ElMessage.error({ message: formatApiError(e, '自动创建页面失败'), duration: 4000, showClose: true })
    }
  }
}

function getCheckedElements() {
  const idSet = checkedIds.value
  return store.elements.filter(el => idSet.has(getElId(el)))
}

function pickXPath(el, strategy) {
  const xpaths = el.xpaths || []
  const match = xpaths.find(x => x.type === strategy && x.count === 1)
  if (match) return match
  // Fallback: same type even if count > 1
  const fallback = xpaths.find(x => x.type === strategy)
  return fallback || null
}

async function doBatchSave() {
  if (!batchSaveForm.value.pageId) { ElMessage.warning('请先选择目标页面'); return }
  const checked = getCheckedElements()
  if (!checked.length) { ElMessage.warning('没有勾选的元素'); return }

  saving.value = true
  const strategy = batchSaveForm.value.strategy
  const items = []
  const skipped = []

  for (const el of checked) {
    const xp = pickXPath(el, strategy)
    if (!xp) {
      skipped.push(el.text || el.resource_id || el.class_name || `bounds=${el.bounds}`)
      continue
    }
    items.push({
      alias: el.text || el.resource_id?.split('/').pop() || `element_${el._idx}`,
      xpath: xp.xpath,
      xpath_type: xp.type,
      xpath_count: xp.count,
      xpath_candidates: el.xpaths || [],
      class_name: el.class_name || '',
      text_val: el.text || '',
      resource_id: el.resource_id || '',
      bounds: el.bounds || '',
      clickable: el.clickable || false,
      content_desc: el.content_desc || '',
    })
  }

  if (!items.length) {
    saving.value = false
    ElMessage.warning(`没有元素可保存：${skipped.length} 个元素缺少「${strategy}」定位策略`)
    return
  }

  try {
    const { data } = await client.post(`/elements/pages/${batchSaveForm.value.pageId}/elements/batch`, {
      elements: items,
      strategy,
    })
    if (data.ok) {
      let msg = `已保存 ${data.saved} 个元素`
      if (data.updated) msg += `（${data.updated} 个已更新）`
      if (data.skipped) msg += `，${data.skipped} 个跳过`
      if (skipped.length) msg += `，${skipped.length} 个缺少策略`
      ElMessage.success({ message: msg, duration: 4000 })
      batchSaveVisible.value = false
      checkedIds.value = new Set()
      // Notify element manager to refresh its table
      bus.emit('elements-saved', { pageId: batchSaveForm.value.pageId })
    } else {
      ElMessage.error(data.error || '批量保存失败')
    }
  } catch (e) {
    ElMessage.error({ message: formatApiError(e, '批量保存失败'), duration: 5000, showClose: true })
  } finally {
    saving.value = false
  }
}

// ── Idle animation ──
const emptyIconRef = ref(null)
const emptyTitleRef = ref(null)
let emptyAnime = []

function startEmptyAnim() {
  stopEmptyAnim()
  nextTick(() => {
    if (emptyIconRef.value) {
      emptyAnime.push(animate(emptyIconRef.value, {
        translateY: [-6, 6], duration: 2800, loop: true, ease: 'inOutSine', direction: 'alternate',
      }))
    }
    if (emptyTitleRef.value) {
      emptyAnime.push(animate(emptyTitleRef.value, {
        opacity: [0.5, 1], duration: 2800, loop: true, ease: 'inOutSine', direction: 'alternate',
      }))
    }
  })
}
function stopEmptyAnim() {
  emptyAnime.forEach(inst => { try { inst.pause() } catch (_) {} })
  emptyAnime = []
}

watch(() => store.elements, (arr) => {
  if (arr.length) stopEmptyAnim()
  else nextTick(() => startEmptyAnim())
}, { immediate: true })

onUnmounted(() => stopEmptyAnim())
</script>

<template>
  <div class="panel">
    <!-- Header -->
    <div class="pe-header">
      <h3>页面元素</h3>
      <span v-if="store.elements.length" class="pe-count">{{ store.elements.length }} 个</span>
    </div>

    <!-- Toolbar -->
    <div v-if="store.elements.length" class="pe-toolbar">
      <button
        class="pe-refresh-btn"
        :disabled="refreshLoading || !store.isConnected"
        @click="refreshElements"
      >{{ refreshLoading ? '⏳ 刷新中...' : '🔄 刷新元素' }}</button>
      <label class="pe-check-all">
        <input type="checkbox" :checked="allChecked" @change="toggleAll" />
        <span>全选</span>
      </label>
      <span v-if="checkedCount" class="pe-checked-count">已选 {{ checkedCount }} 项</span>
      <button
        class="pe-batch-btn"
        :disabled="checkedCount === 0"
        @click="openBatchSave"
      >💾 批量保存</button>
    </div>

    <!-- Element list -->
    <div v-if="!store.elements.length" class="empty">
      <span ref="emptyIconRef" class="empty-icon">📱</span>
      <p ref="emptyTitleRef" class="empty-text">Dump UI 后显示页面元素</p>
    </div>
    <div v-else class="pe-list">
      <div
        v-for="el in store.elements"
        :key="getElId(el)"
        class="pe-row"
        :class="{
          'pe-row--selected': store.selected && getElId(store.selected) === getElId(el),
          'pe-row--checked': checkedIds.has(getElId(el)),
        }"
        @click="onRowClick(el)"
      >
        <input
          type="checkbox"
          class="pe-checkbox"
          :checked="checkedIds.has(getElId(el))"
          @click.stop
          @change="toggleCheck(el)"
        />
        <!-- Thumbnail -->
        <div class="pe-cell pe-cell--thumb">
          <div
            v-if="thumbnailUrl && el.width > 0"
            class="pe-thumb"
            :style="thumbStyle(el)"
            :title="`${el.class_name || ''} [${el.bounds || ''}] — 点击放大`"
            @click.stop="openEnlarge(el)"
          />
          <span v-else class="pe-thumb-placeholder">📱</span>
        </div>
        <!-- Text -->
        <div class="pe-cell pe-cell--text" :title="el.text || el.content_desc || ''">
          <span v-if="el.text" class="pe-text">{{ el.text }}</span>
          <span v-else-if="el.content_desc" class="pe-text pe-text--desc">{{ el.content_desc }}</span>
          <span v-else class="pe-text--none">—</span>
        </div>
        <!-- Bounds -->
        <div class="pe-cell pe-cell--bounds">
          <code class="pe-code">{{ el.bounds || '—' }}</code>
        </div>
        <!-- Clickable -->
        <div class="pe-cell pe-cell--clickable">
          <span v-if="el.clickable" class="pe-badge pe-badge--yes">✓</span>
          <span v-else class="pe-badge pe-badge--no">—</span>
        </div>
      </div>
    </div>

    <!-- Batch save dialog -->
    <el-dialog
      v-model="batchSaveVisible"
      title="批量保存到元素管理"
      width="460px"
      :close-on-click-modal="false"
      @close="batchSaveVisible = false"
    >
      <div class="form-grid">
        <label class="form-label required">目标页面</label>
        <el-select
          v-model="batchSaveForm.pageId"
          placeholder="选择页面"
          :disabled="pagesLoading"
          filterable
          style="width:100%"
        >
          <el-option
            v-for="p in pages"
            :key="p.id"
            :label="pageLabel(p)"
            :value="p.id"
            :disabled="p.is_folder"
          />
        </el-select>
        <label class="form-label required">定位策略</label>
        <el-select
          v-model="batchSaveForm.strategy"
          placeholder="选择定位策略"
          style="width:100%"
        >
          <el-option
            v-for="s in STRATEGY_OPTIONS"
            :key="s.value"
            :label="s.label"
            :value="s.value"
          />
        </el-select>
        <div class="form-hint">
          将为每个勾选元素自动匹配所选策略的 XPath（优先选匹配数=1），匹配不到则跳过。
        </div>
      </div>
      <template #footer>
        <el-button @click="batchSaveVisible = false">取消</el-button>
        <el-button type="primary" :disabled="saving || pagesLoading" @click="doBatchSave">
          {{ saving ? `保存中...` : `保存 ${checkedCount} 个元素` }}
        </el-button>
      </template>
    </el-dialog>

    <!-- Enlarge thumbnail overlay -->
    <div v-if="enlargeVisible" class="enlarge-overlay" @click="enlargeVisible = false">
      <div class="enlarge-card" @click.stop>
        <div
          v-if="enlargeEl && thumbnailUrl"
          class="enlarge-img"
          :style="enlargeStyle(enlargeEl)"
        />
        <div v-if="enlargeEl" class="enlarge-info">
          <p><strong>Class:</strong> {{ enlargeEl.class_name || '—' }}</p>
          <p v-if="enlargeEl.text"><strong>Text:</strong> {{ enlargeEl.text }}</p>
          <p v-if="enlargeEl.resource_id"><strong>ID:</strong> {{ enlargeEl.resource_id }}</p>
          <p v-if="enlargeEl.content_desc"><strong>Desc:</strong> {{ enlargeEl.content_desc }}</p>
          <p><strong>Bounds:</strong> {{ enlargeEl.bounds || '—' }}</p>
          <p><strong>Clickable:</strong> {{ enlargeEl.clickable ? '✓' : '✗' }}</p>
        </div>
        <button class="enlarge-close" @click="enlargeVisible = false">关闭</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.panel {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: var(--glass-bg);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-radius: 20px;
  border: 1px solid var(--glass-border);
  padding: 16px;
  box-shadow: var(--shadow);
  overflow: hidden;
}
.pe-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  flex-shrink: 0;
}
.pe-header h3 {
  font-size: 14px;
  color: var(--app-text, #3D4A3B);
  margin: 0;
}
.pe-count {
  font-size: 12px;
  color: var(--app-text-secondary, #7A8B73);
  background: rgba(139,115,85,0.08);
  padding: 1px 8px;
  border-radius: 10px;
}

/* Toolbar */
.pe-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
  flex-shrink: 0;
  padding: 6px 10px;
  background: rgba(139,115,85,0.05);
  border-radius: 8px;
}
.pe-refresh-btn {
  padding: 4px 10px;
  font-size: 12px;
  border: 1px solid var(--glass-border);
  border-radius: 6px;
  background: var(--glass-bg);
  color: var(--app-text, #3D4A3B);
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}
.pe-refresh-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.pe-refresh-btn:not(:disabled):hover {
  border-color: var(--app-purple, #b39ef3);
  color: var(--app-purple, #b39ef3);
}
.pe-check-all {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--app-text, #3D4A3B);
  cursor: pointer;
  user-select: none;
}
.pe-checked-count {
  font-size: 12px;
  color: var(--app-text-secondary, #7A8B73);
}
.pe-batch-btn {
  margin-left: auto;
  padding: 4px 12px;
  font-size: 12px;
  border: 1px solid var(--glass-border);
  border-radius: 6px;
  background: var(--glass-bg);
  color: var(--app-text, #3D4A3B);
  cursor: pointer;
  transition: all 0.2s;
}
.pe-batch-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.pe-batch-btn:not(:disabled):hover {
  border-color: var(--app-teal, #19c8b9);
  color: var(--app-teal, #19c8b9);
}

/* Empty */
.empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: var(--app-text-secondary, #7A8B73);
  font-size: 13px;
}
.empty-icon { font-size: 32px; opacity: 0.55; }
.empty-text { margin: 0; font-size: 13px; font-weight: 500; color: #725d42; }

/* Element list */
.pe-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
}
.pe-row {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 6px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s;
  border: 1px solid transparent;
}
.pe-row:hover {
  background: rgba(139,115,85,0.06);
}
.pe-row--selected {
  background: rgba(25,200,185,0.1);
  border-color: var(--app-teal, #19c8b9);
}
.pe-row--checked {
  background: rgba(139,115,85,0.04);
}

.pe-checkbox {
  flex-shrink: 0;
  cursor: pointer;
  accent-color: var(--app-teal, #19c8b9);
}

/* Cells */
.pe-cell {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  min-width: 0;
}
.pe-cell--thumb {
  width: 56px;
  justify-content: center;
}
.pe-thumb {
  border-radius: 4px;
  border: 1px solid rgba(139,115,85,0.18);
  background-repeat: no-repeat;
  flex-shrink: 0;
  cursor: zoom-in;
  transition: transform 0.15s;
}
.pe-thumb:hover {
  transform: scale(1.1);
  border-color: var(--app-teal, #19c8b9);
  z-index: 1;
}
.pe-thumb-placeholder {
  font-size: 18px;
  opacity: 0.4;
  width: 36px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.pe-cell--text {
  flex: 1;
  min-width: 0;
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.pe-text { color: var(--app-text, #3D4A3B); }
.pe-text--desc { color: var(--app-text-secondary, #7A8B73); font-style: italic; }
.pe-text--none { color: #ccc; }
.pe-cell--bounds {
  width: 110px;
  font-size: 11px;
  overflow: hidden;
}
.pe-code {
  font-size: 10px;
  color: var(--app-text-secondary, #7A8B73);
  background: rgba(139,115,85,0.06);
  padding: 1px 5px;
  border-radius: 3px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}
.pe-cell--clickable {
  width: 32px;
  justify-content: center;
}
.pe-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 4px;
}
.pe-badge--yes {
  color: #6fba2c;
  background: rgba(111,186,44,0.12);
}
.pe-badge--no {
  color: #ccc;
}

/* Form */
.form-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.form-label {
  font-size: 13px;
  color: var(--text-secondary, #988B7A);
  font-weight: 500;
  user-select: none;
}
.form-label.required::before {
  content: '* ';
  color: #e8998a;
}
.form-hint {
  font-size: 12px;
  color: var(--app-text-secondary, #7A8B73);
  line-height: 1.5;
  background: rgba(139,115,85,0.05);
  padding: 8px 10px;
  border-radius: 6px;
}

/* Enlarge overlay */
.enlarge-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: rgba(0,0,0,0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(4px);
}
.enlarge-card {
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  max-width: 90vw;
  max-height: 90vh;
  box-shadow: 0 8px 40px rgba(0,0,0,0.2);
}
.enlarge-img {
  border-radius: 8px;
  border: 2px solid rgba(139,115,85,0.2);
  background-repeat: no-repeat;
  flex-shrink: 0;
}
.enlarge-info {
  font-size: 13px;
  line-height: 1.7;
  color: var(--app-text-secondary, #7A8B73);
  text-align: left;
  width: 100%;
}
.enlarge-info p {
  margin: 2px 0;
}
.enlarge-info strong {
  color: var(--app-text, #3D4A3B);
}
.enlarge-close {
  padding: 6px 24px;
  border: 1px solid var(--glass-border);
  border-radius: 8px;
  background: var(--glass-bg);
  color: var(--app-text, #3D4A3B);
  cursor: pointer;
  font-size: 14px;
}
</style>
