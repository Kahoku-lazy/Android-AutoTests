<script setup>
import { ref, computed, watch, nextTick, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { animate } from 'animejs'
import { formatApiError } from '@/shared/api-client'
import { apiGetScreenshot } from '../api'
import { apiGetPages, apiCreatePage, apiBatchAddElementsToPage } from '@/modules/element-locator/api'
import { useElementStore } from '../store'
import { bus } from '@/shared/event-bus'
import { IconRefresh, IconSave, IconDevice, IconScan } from '@/shared/icons'

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
    const { data } = await apiGetScreenshot()
    if (data.status && data.image) {
      // Use data URL directly — browser decodes natively
      const url = `data:image/${data.format || 'jpeg'};base64,${data.image}`
      thumbnailUrl.value = url
      loadImageDims(url)
      return true
    }
  } catch (e) { console.error(e); }
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
    if (!result?.status) ElMessage.error('Dump 失败')
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
  const list = store.filteredElements
  if (checkedIds.value.size === list.length) {
    checkedIds.value = new Set()
  } else {
    checkedIds.value = new Set(list.map(e => e._idx ?? e.__uid))
  }
}

const allChecked = computed(() =>
  store.filteredElements.length > 0 && checkedIds.value.size === store.filteredElements.length
)

const checkedCount = computed(() => checkedIds.value.size)

function getElId(el) {
  return el._idx ?? el.__uid
}

// ── Unique XPath for display: pick single count===1 locator, ID → Text priority ──
const XPATH_PRIORITY = ['resource-id', 'text', 'content-desc', 'class', 'index', 'combined', 'resource-id (any)', 'text (any)']

function uniqueXPath(el) {
  const xpaths = el.xpaths || []
  const unique = xpaths.filter(x => x.count === 1 && x.xpath)
  if (!unique.length) return ''
  const prio = t => { const i = XPATH_PRIORITY.indexOf(t); return i === -1 ? 999 : i }
  unique.sort((a, b) => prio(a.type) - prio(b.type))
  return unique[0].xpath
}

// ── Row click → select element (same as screen click) ──
function onRowClick(el) {
  store.selectElement(el)
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
    const { data } = await apiGetPages()
    if (data.status) pages.value = data.pages || []
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
      const { data } = await apiCreatePage({
        label: `Page_${new Date().toISOString().slice(0, 10)}`,
        package: pkg,
        activity,
      })
      if (data.status) {
        const page = data.page || {}
        batchSaveForm.value.pageId = page.id
        pages.value.push({ id: page.id, label: page.label || data.label })
      } else {
        ElMessage.error(data.message || '自动创建页面失败')
      }
    } catch (e) {
      ElMessage.error({ message: formatApiError(e, '自动创建页面失败'), duration: 4000, showClose: true })
    }
  }
}

function getCheckedElements() {
  const idSet = checkedIds.value
  return store.filteredElements.filter(el => idSet.has(getElId(el)))
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
    const { data } = await apiBatchAddElementsToPage(batchSaveForm.value.pageId, items, strategy)
    if (data.status) {
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
      ElMessage.error(data.message || '批量保存失败')
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
      <span v-if="store.elements.length && store.activePanelTab === 'elements'" class="pe-count">{{ store.elements.length }} 个</span>
    </div>

    <!-- Tab toggle -->
    <div class="pe-tabs">
      <button class="pe-tab" :class="{ 'pe-tab--active': store.activePanelTab === 'elements' }" @click="store.activePanelTab = 'elements'">元素</button>
      <button class="pe-tab" :class="{ 'pe-tab--active': store.activePanelTab === 'ocr' }" @click="store.activePanelTab = 'ocr'">
        OCR<span v-if="store.ocrResults.length" class="pe-tab-badge">{{ store.ocrResults.length }}</span>
      </button>
    </div>

    <!-- Elements view -->
    <template v-if="store.activePanelTab === 'elements'">
    <!-- Toolbar -->
    <div v-if="store.elements.length" class="pe-toolbar">
      <button
        class="pe-refresh-btn"
        :disabled="refreshLoading || !store.isConnected"
        @click="refreshElements"
      ><IconRefresh :size="14" /> {{ refreshLoading ? '刷新中...' : '刷新元素' }}</button>
      <label class="pe-check-all">
        <input type="checkbox" :checked="allChecked" @change="toggleAll" />
        <span>全选</span>
      </label>
      <span v-if="checkedCount" class="pe-checked-count">已选 {{ checkedCount }} 项</span>
      <button
        class="pe-batch-btn"
        :disabled="checkedCount === 0"
        @click="openBatchSave"
      ><IconSave :size="14" /> 批量保存</button>
    </div>

    <!-- Element list -->
    <div v-if="!store.elements.length" class="empty">
      <span ref="emptyIconRef" class="empty-icon"><IconDevice :size="32" /></span>
      <p ref="emptyTitleRef" class="empty-text">Dump UI 后显示页面元素</p>
    </div>
    <div v-else class="pe-list">
      <div
        v-for="el in store.filteredElements"
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
          <span v-else class="pe-thumb-placeholder"><IconDevice :size="16" /></span>
        </div>
        <!-- Text -->
        <div class="pe-cell pe-cell--text" :title="el.text || el.content_desc || ''">
          <span v-if="el.text" class="pe-text">{{ el.text }}</span>
          <span v-else-if="el.content_desc" class="pe-text pe-text--desc">{{ el.content_desc }}</span>
          <span v-else class="pe-text--none">—</span>
        </div>
        <!-- Resource ID -->
        <div class="pe-cell pe-cell--rid" :title="el.resource_id || ''">
          <code v-if="el.resource_id" class="pe-code">{{ el.resource_id }}</code>
          <span v-else class="pe-text--none">—</span>
        </div>
        <!-- Bounds -->
        <div class="pe-cell pe-cell--bounds">
          <code class="pe-code">{{ el.bounds || '—' }}</code>
        </div>
        <!-- Unique XPath -->
        <div class="pe-cell pe-cell--xpath" :title="uniqueXPath(el)">
          <code v-if="uniqueXPath(el)" class="pe-code pe-code--xpath">{{ uniqueXPath(el) }}</code>
          <span v-else class="pe-text--none">—</span>
        </div>
        <!-- Clickable -->
        <div class="pe-cell pe-cell--clickable">
          <span v-if="el.clickable" class="pe-badge pe-badge--yes">✓</span>
          <span v-else class="pe-badge pe-badge--no">—</span>
        </div>
      </div>
    </div>
    </template>

    <!-- OCR view -->
    <template v-else>
      <div v-if="!store.ocrResults.length" class="empty">
        <span class="empty-icon"><IconScan :size="32" /></span>
        <p class="empty-text">点击工具栏「OCR 检测」后显示识别结果</p>
      </div>
      <div v-else class="pe-list">
        <div
          v-for="(it, i) in store.ocrResults"
          :key="i"
          class="ocr-row"
          :class="{ 'ocr-row--selected': store.selectedOcr === it }"
          @click="store.selectOcr(it)"
        >
          <img
            v-if="it.thumbnail"
            class="ocr-thumb"
            :src="`data:image/${it.thumbnail_format || 'jpeg'};base64,${it.thumbnail}`"
            :alt="it.text || 'ocr'"
          />
          <span v-else class="pe-thumb-placeholder"><IconScan :size="16" /></span>
          <div class="pe-cell pe-cell--text" :title="it.text">
            <span class="pe-text">{{ it.text || '—' }}</span>
          </div>
          <div class="pe-cell pe-cell--confidence">
            <span class="pe-badge pe-badge--yes">{{ (it.confidence * 100).toFixed(1) }}%</span>
          </div>
          <div class="pe-cell pe-cell--bounds">
            <code class="pe-code">[{{ it.x }},{{ it.y }}][{{ it.x + it.width }},{{ it.y + it.height }}]</code>
          </div>
        </div>
      </div>
    </template>

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

<style scoped src="./PageElementsPanel.css"></style>
