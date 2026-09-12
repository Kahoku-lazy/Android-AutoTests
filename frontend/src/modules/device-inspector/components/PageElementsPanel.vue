<script setup>
import { ref, computed } from 'vue'
import { useElementStore, mediaUrl } from '../store'
import EmptyState from '@/shared/components/patterns/EmptyState.vue'

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

/** 表头分组着色（dump 蓝 / OCR 紫） */
function headerCellStyle({ column }) {
  if (column.label === 'dump') return { background: '#e8f4fd', color: '#409eff', fontWeight: 700 }
  if (column.label === 'OCR') return { background: '#f3efff', color: '#a78bfa', fontWeight: 700 }
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
    <el-table
      v-if="rows.length"
      :data="rows"
      size="small"
      height="100%"
      row-key="_rowKey"
      :header-cell-style="headerCellStyle"
      @row-click="onRowClick"
      :row-class-name="({ row }) => (isRowSelected(row) ? 'pep-row--selected' : '')"
    >
      <el-table-column width="40">
        <template #header>
          <el-checkbox :model-value="allChecked" @change="toggleAll" />
        </template>
        <template #default="{ row }">
          <el-checkbox
            :model-value="store.checkedIds.has(row._rowKey)"
            @change="() => store.toggleCheck(row)"
            @click.stop
          />
        </template>
      </el-table-column>

      <!-- dump 组列 -->
      <el-table-column label="dump">
        <el-table-column width="66" label="缩略图">
          <template #default="{ row }">
            <div v-if="dumpThumb(row)" class="pep-thumb-wrap" role="button" tabindex="0"
              @click.stop="openEnlarge(row, 'dump')"
              @keydown.enter.prevent="openEnlarge(row, 'dump')"
              @keydown.space.prevent="openEnlarge(row, 'dump')">
              <img :src="mediaUrl(dumpThumb(row))" class="pep-thumb" />
              <span class="pep-badge pep-badge--dump">dump</span>
            </div>
            <span v-else class="pep-thumb-pep--empty">—</span>
          </template>
        </el-table-column>
        <el-table-column label="text" min-width="110" show-overflow-tooltip>
          <template #default="{ row }">{{ dumpText(row) || '—' }}</template>
        </el-table-column>
        <el-table-column label="resource-id" min-width="150" show-overflow-tooltip>
          <template #default="{ row }">{{ row.resource_id || '—' }}</template>
        </el-table-column>
        <el-table-column label="XPath" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">{{ dumpXPath(row) || '—' }}</template>
        </el-table-column>
        <el-table-column label="坐标" width="140">
          <template #default="{ row }">{{ dumpBounds(row) || '—' }}</template>
        </el-table-column>
      </el-table-column>

      <!-- OCR 组列 -->
      <el-table-column label="OCR">
        <el-table-column width="66" label="缩略图">
          <template #default="{ row }">
            <div v-if="ocrThumb(row)" class="pep-thumb-wrap" role="button" tabindex="0"
              @click.stop="openEnlarge(row, 'ocr')"
              @keydown.enter.prevent="openEnlarge(row, 'ocr')"
              @keydown.space.prevent="openEnlarge(row, 'ocr')">
              <img :src="mediaUrl(ocrThumb(row))" class="pep-thumb" />
              <span class="pep-badge pep-badge--ocr">ocr</span>
            </div>
            <span v-else class="pep-thumb-pep--empty">—</span>
          </template>
        </el-table-column>
        <el-table-column label="文字" min-width="110" show-overflow-tooltip>
          <template #default="{ row }">{{ ocrText(row) || '—' }}</template>
        </el-table-column>
        <el-table-column label="坐标" width="140">
          <template #default="{ row }">{{ ocrBounds(row) || '—' }}</template>
        </el-table-column>
        <el-table-column label="置信度" width="80">
          <template #default="{ row }">
            {{ ocrConfidence(row) != null ? (ocrConfidence(row) * 100).toFixed(1) + '%' : '—' }}
          </template>
        </el-table-column>
      </el-table-column>
    </el-table>
    <EmptyState v-else text="暂无数据" hint="获取 Dump/OCR 快照后显示页面数据" />

    <!-- 缩略图放大浮层（按 dump/ocr 聚焦渲染） -->
    <Teleport to="body">
      <div v-if="enlargeVisible && enlargeRow" class="pep-enlarge-mask" @click="closeEnlarge">
        <div class="pep-enlarge" @click.stop>
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
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.pep { height: 100%; min-height: 0; overflow: hidden; }
.pep-thumb-wrap { position: relative; display: inline-flex; cursor: zoom-in; }
.pep-thumb { width: 48px; height: 48px; object-fit: contain; border: 2px solid var(--app-ink, #2d2d2d); border-radius: 4px; display: block; }
.pep-badge {
  position: absolute; left: 0; bottom: 0;
  font-size: var(--app-size-xs); font-weight: 700; line-height: 1;
  padding: 2px var(--app-space-xs); border-radius: 0 4px 0 0;
  color: #fff;
}
.pep-badge--dump { background: #409eff; }
.pep-badge--ocr { background: #a78bfa; }
.pep-thumb-pep--empty { color: var(--app-text-secondary); }
:deep(.pep-row--selected) { background: rgba(167, 139, 250, 0.18); }

/* ── 放大浮层 ── */
.pep-enlarge-mask {
  position: fixed; inset: 0; z-index: 2000;
  background: rgba(0, 0, 0, 0.45);
  display: flex; align-items: center; justify-content: center;
}
.pep-enlarge {
  display: flex; gap: var(--app-space-md); align-items: flex-start;
  background: var(--app-bg-card, #fff);
  border: 3px solid var(--app-ink, #2d2d2d);
  border-radius: 6px 10px 6px 10px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
  padding: var(--app-space-md);
  max-width: 90vw;
}
.pep-enlarge-img {
  width: 240px; height: 240px; object-fit: contain;
  border: 2px solid var(--app-ink, #2d2d2d); border-radius: 4px;
  background: var(--doodle-bg, #faf5ee);
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
