<script setup>
import { ref, computed } from 'vue'
import { useElementStore, mediaUrl } from '../store'
import EmptyState from '@/shared/components/patterns/EmptyState.vue'
import AppTable from '@/shared/components/AppTable.vue'

const store = useElementStore()

const props = defineProps({
  rows: { type: Array, default: () => [] },
  selected: { type: Object, default: null },
  selectedOcr: { type: Object, default: null },
})
const emit = defineEmits(['select', 'select-ocr'])

const enlargeVisible = ref(false)
const enlargeRow = ref(null)
const enlargeKind = ref('dump') // 放大浮层聚焦：dump | ocr

const allChecked = computed(() =>
  props.rows.length > 0 && store.checkedIds.size === props.rows.length
)

function toggleAll() {
  if (allChecked.value) {
    store.checkedIds = new Set()
  } else {
    store.checkedIds = new Set(props.rows.map(r => r._rowKey))
  }
}

/** 元素表列定义：dump / OCR 两级分组 + 选择列（列名即插槽名） */
const ELEMENT_COLUMNS = [
  { key: '_select', width: 40, label: '', showOverflowTooltip: false },
  {
    key: 'dump',
    label: 'dump',
    children: [
      { key: 'dump_thumb', width: 66, label: '缩略图', showOverflowTooltip: false },
      { key: 'dump_text', minWidth: 110, label: 'text' },
      { key: 'resource_id', minWidth: 150, label: 'resource-id' },
      { key: 'dump_xpath', minWidth: 180, label: 'XPath' },
      { key: 'dump_bounds', width: 140, label: '坐标', showOverflowTooltip: false },
    ],
  },
  {
    key: 'ocr',
    label: 'OCR',
    children: [
      { key: 'ocr_thumb', width: 66, label: '缩略图', showOverflowTooltip: false },
      { key: 'ocr_text', minWidth: 110, label: '文字' },
      { key: 'ocr_bounds', width: 140, label: '坐标', showOverflowTooltip: false },
      { key: 'ocr_confidence', width: 80, label: '置信度', showOverflowTooltip: false },
    ],
  },
]

function onRowClick(row) {
  if (row._kind === 'ocr') emit('select-ocr', row)
  else emit('select', row)
}

function isRowSelected(row) {
  if (row._kind === 'ocr') return props.selectedOcr && row._rowKey === `o${props.selectedOcr._idx ?? props.selectedOcr.__uid}`
  return props.selected && row._rowKey === `d${props.selected._idx ?? props.selected.__uid}`
}

/** 行内 dump 侧取值（纯 OCR 行为空） */
function dumpText(row) { return row._kind === 'dump' ? row.text || '' : '' }
function dumpThumb(row) { return row._kind === 'dump' ? row.thumbnail_path || '' : '' }
function dumpXPath(row) { return row._kind === 'dump' ? uniqueXPath(row) : '' }
function dumpBounds(row) { return row._kind === 'dump' ? rowBounds(row) : '' }

/** 行内 OCR 侧取值（纯 dump 行为空） */
function ocrText(row) {
  if (row._kind === 'ocr') return row.text || ''
  return row._ocrMatched ? row.ocr_text || '' : ''
}
function ocrThumb(row) {
  if (row._kind === 'ocr') return row.thumbnail_path || ''
  return row._ocrMatched ? row.ocr_thumbnail_path || '' : ''
}
function ocrConfidence(row) {
  if (row._kind === 'ocr') return row.confidence
  return row._ocrMatched ? row.ocr_confidence : null
}
function ocrBounds(row) {
  if (row._kind === 'ocr' || row._ocrMatched) return rowBounds(row)
  return ''
}

function openEnlarge(row, kind) {
  if (kind === 'dump' && !dumpThumb(row)) return
  if (kind === 'ocr' && !ocrThumb(row)) return
  enlargeRow.value = row
  enlargeKind.value = kind
  enlargeVisible.value = true
}

function closeEnlarge() {
  enlargeVisible.value = false
  enlargeRow.value = null
}

/** 表头分组着色（dump 用模块色 / OCR 用元素色；色值一律走令牌，见 frontend-l0-design-tokens） */
function headerCellStyle({ column }) {
  if (column.label === 'dump') return { background: 'var(--app-page-active-bg)', color: 'var(--c-device)', fontWeight: 700 }
  if (column.label === 'OCR') return { background: 'var(--app-icon-purple-bg)', color: 'var(--c-element)', fontWeight: 700 }
  return {}
}

// ── 唯一定位展示：count=1 候选，ID → Text 优先（PRD C-05）──
const XPATH_PRIORITY = ['resource-id', 'text', 'content-desc', 'class', 'index', 'combined', 'resource-id (any)', 'text (any)']

function uniqueXPath(el) {
  const xpaths = el.xpaths || []
  const unique = xpaths.filter(x => x.count === 1 && x.xpath)
  if (!unique.length) return ''
  const prio = t => { const i = XPATH_PRIORITY.indexOf(t); return i === -1 ? 999 : i }
  unique.sort((a, b) => prio(a.type) - prio(b.type))
  return unique[0].xpath
}

/** 坐标统一展示：bounds 四角格式（dump 与 OCR 口径一致） */
function rowBounds(row) {
  if (row.bounds) return row.bounds
  return `[${row.x},${row.y}][${(row.x || 0) + (row.width || 0)},${(row.y || 0) + (row.height || 0)}]`
}
</script>

<template>
  <div class="pep">
    <AppTable
      v-if="rows.length"
      :columns="ELEMENT_COLUMNS"
      :data-source="rows"
      row-key="_rowKey"
      size="small"
      height="100%"
      :header-cell-style="headerCellStyle"
      @row-click="onRowClick"
      :row-class-name="({ row }) => (isRowSelected(row) ? 'pep-row--selected' : '')"
    >
      <template #header-_select>
        <el-checkbox :model-value="allChecked" @change="toggleAll" />
      </template>
      <template #cell-_select="{ row }">
        <el-checkbox
          :model-value="store.checkedIds.has(row._rowKey)"
          @change="() => store.toggleCheck(row)"
          @click.stop
        />
      </template>

      <template #cell-dump_thumb="{ row }">
        <div v-if="dumpThumb(row)" class="pep-thumb-wrap" role="button" tabindex="0"
          @click.stop="openEnlarge(row, 'dump')"
          @keydown.enter.prevent="openEnlarge(row, 'dump')"
          @keydown.space.prevent="openEnlarge(row, 'dump')">
          <img :src="mediaUrl(dumpThumb(row))" class="pep-thumb" />
          <span class="pep-badge pep-badge--dump">dump</span>
        </div>
        <span v-else class="pep-thumb-pep--empty">—</span>
      </template>
      <template #cell-dump_text="{ row }">{{ dumpText(row) || '—' }}</template>
      <template #cell-resource_id="{ row }">{{ row.resource_id || '—' }}</template>
      <template #cell-dump_xpath="{ row }">{{ dumpXPath(row) || '—' }}</template>
      <template #cell-dump_bounds="{ row }">{{ dumpBounds(row) || '—' }}</template>

      <template #cell-ocr_thumb="{ row }">
        <div v-if="ocrThumb(row)" class="pep-thumb-wrap" role="button" tabindex="0"
          @click.stop="openEnlarge(row, 'ocr')"
          @keydown.enter.prevent="openEnlarge(row, 'ocr')"
          @keydown.space.prevent="openEnlarge(row, 'ocr')">
          <img :src="mediaUrl(ocrThumb(row))" class="pep-thumb" />
          <span class="pep-badge pep-badge--ocr">ocr</span>
        </div>
        <span v-else class="pep-thumb-pep--empty">—</span>
      </template>
      <template #cell-ocr_text="{ row }">{{ ocrText(row) || '—' }}</template>
      <template #cell-ocr_bounds="{ row }">{{ ocrBounds(row) || '—' }}</template>
      <template #cell-ocr_confidence="{ row }">
        {{ ocrConfidence(row) != null ? (ocrConfidence(row) * 100).toFixed(1) + '%' : '—' }}
      </template>
    </AppTable>
    <EmptyState v-else text="暂无数据" hint="获取 Dump/OCR 快照后显示页面数据" />

    <!-- 缩略图放大预览（覆盖层统一走 EP，见 frontend/AGENTS.md「L5 覆盖层」） -->
    <el-dialog
      :model-value="enlargeVisible"
      title="缩略图预览"
      width="auto"
      @update:model-value="(v) => { if (!v) closeEnlarge() }"
    >
      <div v-if="enlargeRow" class="pep-enlarge">
        <img
          v-if="enlargeKind === 'dump'"
          :src="mediaUrl(dumpThumb(enlargeRow))"
          class="pep-enlarge-img"
        />
        <img
          v-else
          :src="mediaUrl(ocrThumb(enlargeRow))"
          class="pep-enlarge-img"
        />
        <div class="pep-enlarge-detail">
          <template v-if="enlargeKind === 'dump'">
            <div class="pep-enlarge-field"><span>Class</span>{{ enlargeRow.class_name || '—' }}</div>
            <div class="pep-enlarge-field"><span>Text</span>{{ enlargeRow.text || '—' }}</div>
            <div class="pep-enlarge-field"><span>ID</span>{{ enlargeRow.resource_id || '—' }}</div>
            <div class="pep-enlarge-field"><span>Desc</span>{{ enlargeRow.content_desc || '—' }}</div>
            <div class="pep-enlarge-field"><span>Bounds</span>{{ enlargeRow.bounds || '—' }}</div>
            <div class="pep-enlarge-field"><span>Clickable</span>{{ enlargeRow.clickable ? '是' : '否' }}</div>
          </template>
          <template v-else>
            <div class="pep-enlarge-field"><span>文字</span>{{ ocrText(enlargeRow) || '—' }}</div>
            <div class="pep-enlarge-field"><span>置信度</span>{{ ocrConfidence(enlargeRow) != null ? (ocrConfidence(enlargeRow) * 100).toFixed(1) + '%' : '—' }}</div>
            <div class="pep-enlarge-field"><span>Bounds</span>{{ rowBounds(enlargeRow) }}</div>
          </template>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<style scoped>
.pep {
  /* 本组件私有色值登记：放大预览的浮动阴影（消费者在本根类之内） */
  --pep-enlarge-shadow-color: var(--color-ink-05-a30) /* -> --color-ink-05-a30 */;  /* 放大预览面板的落影 */
  height: 100%; min-height: 0; overflow: hidden;
}
.pep-thumb-wrap { position: relative; display: inline-flex; cursor: zoom-in; }
.pep-thumb { width: 48px; height: 48px; object-fit: contain; border: 2px solid var(--ink); border-radius: 4px; display: block; }
.pep-badge {
  position: absolute; left: 0; bottom: 0;
  font-size: var(--app-size-xs); font-weight: 700; line-height: 1;
  padding: 2px var(--app-space-xs); border-radius: 0 4px 0 0;
  color: var(--app-text-inverse);
}
.pep-badge--dump { background: var(--c-device); }
.pep-badge--ocr { background: var(--c-element); }
.pep-thumb-pep--empty { color: var(--app-text-secondary); }
:deep(.pep-row--selected) { background: color-mix(in srgb, var(--c-element) 18%, transparent); }

/* ── 放大浮层 ── */
/* ── 放大预览内容（外壳由 el-dialog 提供） ── */
.pep-enlarge {
  display: flex; gap: var(--app-space-md); align-items: flex-start;
  background: var(--app-bg-card);
  border: 3px solid var(--ink);
  border-radius: 6px 10px 6px 10px;
  box-shadow: 0 8px 32px var(--pep-enlarge-shadow-color);
  padding: var(--app-space-md);
  max-width: 90vw;
}
.pep-enlarge-img {
  width: 240px; height: 240px; object-fit: contain;
  border: 2px solid var(--ink); border-radius: 4px;
  background: var(--paper);
}
.pep-enlarge-detail {
  display: flex; flex-direction: column; gap: 6px;
  font-size: var(--app-size-xs);
  min-width: 220px; max-width: 320px;
}
.pep-enlarge-field {
  display: flex; gap: var(--app-space-sm); align-items: baseline;
  word-break: break-all;
}
.pep-enlarge-field span {
  flex-shrink: 0; width: 64px; font-weight: 700; color: var(--app-text-secondary);
}
</style>
