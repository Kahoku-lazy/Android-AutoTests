<script setup>
/** 结构分析面板 — 纯规则分区结果展示（6 层分区树 + 元素档案表）。
 *  展示组件，不碰 HTTP；元素名称可内联重命名（回写 store → 保存时作为 alias 落库）。
 */
import { ref, computed, nextTick } from 'vue'
import { useElementStore, mediaUrl } from '../store'
import { IconEdit } from '@/shared/icons'
import EmptyState from '@/shared/components/patterns/EmptyState.vue'
import AppTable from '@/shared/components/AppTable.vue'

const store = useElementStore()

const props = defineProps({
  sections: { type: Array, default: () => [] },
  elements: { type: Array, default: () => [] },
  isWebview: { type: Boolean, default: false },
  selected: { type: Object, default: null },
})
const emit = defineEmits(['select'])

const activeRole = ref(null)

// ── 行选中联动（左侧截图高亮，_idx 与快照元素同源同序）──
const enlargeVisible = ref(false)
const enlargeRow = ref(null)

// ── 元素名称内联重命名 ──
const editingIdx = ref(null)
const editDraft = ref('')
let nameInputEl = null
function setNameInputRef(el) { nameInputEl = el }

const activeElements = computed(() =>
  activeRole.value
    ? props.elements.filter(e => e.role === activeRole.value)
    : props.elements
)

/** 元素档案表列定义（缩略图 / 名称 / 标识 / 元素 / 指标 / XPath / bounds） */
const ELEMENT_COLUMNS = [
  { dataIndex: 'thumbnail', width: 66, label: '缩略图', showOverflowTooltip: false },
  { dataIndex: 'name', minWidth: 120, label: '元素名称', showOverflowTooltip: false },
  { dataIndex: 'label', minWidth: 140, label: '标识' },
  { dataIndex: 'resource_id', minWidth: 120, label: '元素' },
  { dataIndex: 'metrics', width: 150, label: '指标', showOverflowTooltip: false },
  { dataIndex: 'xpath', minWidth: 200, label: 'XPath' },
  { dataIndex: 'bounds', width: 150, label: 'bounds' },
]

function selectSection(section) {
  activeRole.value = activeRole.value === section.role ? null : section.role
}

function onRowClick(row) {
  emit('select', row)
}

function isRowSelected(row) {
  return props.selected && row._idx != null && row._idx === props.selected._idx
}

function shortClass(name) {
  return (name || '').split('.').pop()
}

/** 元素标识：text > content_desc > resource_id > class 短名 */
function elLabel(e) {
  return e.text || e.content_desc || e.resource_id || shortClass(e.class_name) || '—'
}

/** 元素名称：自定义名优先，否则元素 text（空则空，可点击重命名） */
function nameValue(row) {
  return store.nameOverrides[row._idx] ?? (row.text || '')
}

function startEdit(row) {
  editingIdx.value = row._idx
  editDraft.value = nameValue(row)
  nextTick(() => {
    if (nameInputEl) { nameInputEl.focus(); nameInputEl.select() }
  })
}

function commitName(row) {
  if (editingIdx.value !== row._idx) return
  store.setElementName(row._idx, editDraft.value)
  editingIdx.value = null
}

function openEnlarge(row) {
  if (!row.thumbnail_path) return
  enlargeRow.value = row
  enlargeVisible.value = true
}

function closeEnlarge() {
  enlargeVisible.value = false
  enlargeRow.value = null
}

function roleName(role) {
  const s = props.sections.find(s => s.role === role)
  return s?.name || role || '—'
}

// 唯一定位候选优先级（与 PageElementsPanel 口径一致）
const XPATH_PRIORITY = ['resource-id', 'text', 'content-desc', 'class', 'combined']

function bestXPath(e) {
  const xpaths = e.xpaths || []
  const unique = xpaths.filter(x => x.count === 1 && x.xpath)
  const pool = unique.length ? unique : xpaths
  if (!pool.length) return ''
  const prio = t => { const i = XPATH_PRIORITY.indexOf(t); return i === -1 ? 999 : i }
  return [...pool].sort((a, b) => prio(a.type) - prio(b.type))[0].xpath
}

const METRIC_TAG = { 可点击: 'success', 可滚动: 'info', 可勾选: 'warning' }
</script>

<template>
  <div class="sap">
    <div v-if="isWebview" class="sap-webview-hint">
      纯 WebView 页面 — 原生层级无业务元素，页面内容需切 Web context 获取
    </div>

    <div v-if="sections.length" class="sap-body">
      <!-- 左：分区树 -->
      <aside class="sap-sections">
        <div class="sap-sections-title">页面分区</div>
        <div
          v-for="s in sections"
          :key="s.role"
          class="sap-section"
          :class="{ 'sap-section--active': s.role === activeRole }"
          role="button"
          tabindex="0"
          @click="selectSection(s)"
          @keydown.enter.prevent="selectSection(s)"
          @keydown.space.prevent="selectSection(s)"
        >
          <span class="sap-section-name">{{ s.name }}</span>
          <span class="sap-section-count">{{ s.element_count }}</span>
        </div>
      </aside>

      <!-- 右：元素档案表 -->
      <section class="sap-table">
        <AppTable
          :columns="ELEMENT_COLUMNS"
          :data-source="activeElements"
          row-key="_idx"
          size="small"
          height="100%"
          :row-class-name="({ row }) => (isRowSelected(row) ? 'sap-row--selected' : '')"
          @row-click="onRowClick"
        >
          <template #cell-thumbnail="{ row }">
            <div v-if="row.thumbnail_path" class="sap-thumb-wrap" role="button" tabindex="0"
              @click.stop="openEnlarge(row)"
              @keydown.enter.prevent="openEnlarge(row)"
              @keydown.space.prevent="openEnlarge(row)">
              <img :src="mediaUrl(row.thumbnail_path)" class="sap-thumb" />
            </div>
            <span v-else class="sap-thumb-empty">—</span>
          </template>
          <template #cell-name="{ row }">
            <input
              v-if="editingIdx === row._idx"
              :ref="setNameInputRef"
              v-model="editDraft"
              class="sap-name-input"
              @click.stop
              @keydown.enter.prevent="commitName(row)"
              @blur="commitName(row)"
            />
            <div v-else class="sap-name-cell" role="button" tabindex="0"
              @click.stop="startEdit(row)"
              @keydown.enter.prevent="startEdit(row)">
              <span class="sap-name-text" :class="{ 'sap-name--empty': !nameValue(row) }">
                {{ nameValue(row) || '点击命名' }}
              </span>
              <IconEdit :size="12" class="sap-name-icon" />
            </div>
          </template>
          <template #cell-label="{ row }">{{ elLabel(row) }}</template>
          <template #cell-resource_id="{ row }">{{ row.resource_id || '—' }}</template>
          <template #cell-metrics="{ row }">
            <template v-if="(row.metrics || []).length">
              <el-tag
                v-for="m in row.metrics"
                :key="m"
                size="small"
                :type="METRIC_TAG[m] || 'info'"
                class="sap-tag"
              >{{ m }}</el-tag>
            </template>
            <span v-else>—</span>
          </template>
          <template #cell-xpath="{ row }">{{ bestXPath(row) || '—' }}</template>
          <template #cell-bounds="{ row }">{{ row.bounds || '—' }}</template>
        </AppTable>
      </section>
    </div>

    <EmptyState v-else text="暂无结构数据" hint="点击工具栏「结构分析」生成页面分区" />

    <!-- 缩略图放大预览（覆盖层统一走 EP，见 frontend/AGENTS.md「L5 覆盖层」） -->
    <el-dialog
      :model-value="enlargeVisible"
      title="缩略图预览"
      width="auto"
      @update:model-value="(v) => { if (!v) closeEnlarge() }"
    >
      <div v-if="enlargeRow" class="sap-enlarge">
        <img :src="mediaUrl(enlargeRow.thumbnail_path)" class="sap-enlarge-img" />
        <div class="sap-enlarge-detail">
          <div class="sap-enlarge-field"><span>名称</span>{{ nameValue(enlargeRow) || '—' }}</div>
          <div class="sap-enlarge-field"><span>Class</span>{{ enlargeRow.class_name || '—' }}</div>
          <div class="sap-enlarge-field"><span>ID</span>{{ enlargeRow.resource_id || '—' }}</div>
          <div class="sap-enlarge-field"><span>Desc</span>{{ enlargeRow.content_desc || '—' }}</div>
          <div class="sap-enlarge-field"><span>Bounds</span>{{ enlargeRow.bounds || '—' }}</div>
          <div class="sap-enlarge-field"><span>分区</span>{{ roleName(enlargeRow.role) }}</div>
          <div class="sap-enlarge-field">
            <span>指标</span>{{ (enlargeRow.metrics || []).join(' · ') || '—' }}
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<style scoped>
.sap {
  /* 本组件私有色值登记：选中行元素色淡底与放大预览落影（消费者都在本根类之内） */
  --sap-row-selected-bg: var(--color-indigo-76-a18) /* -> --color-indigo-76-a18 */;  /* 表格选中行的元素色淡底 */
  --sap-enlarge-shadow-color: var(--color-ink-05-a30) /* -> --color-ink-05-a30 */;   /* 放大预览面板的落影 */
  height: 100%; min-height: 0; display: flex; flex-direction: column; overflow: hidden;
}

.sap-webview-hint {
  flex-shrink: 0;
  margin-bottom: 10px;
  padding: var(--app-space-sm) 12px;
  font-size: var(--app-size-xs);
  font-weight: 700;
  color: var(--app-footer-yellow-text);
  background: var(--app-highlight);
  border: 2px solid var(--ink);
  border-radius: 4px 8px 4px 8px;
}

.sap-body {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: minmax(0, 0.8fr) minmax(0, 2fr);
  gap: 12px;
  overflow: hidden;
}

.sap-sections {
  min-height: 0;
  overflow-y: auto;
  padding: var(--app-space-sm);
  background: var(--app-bg-card);
  border: 2px solid var(--ink);
  border-radius: 6px 10px 6px 10px;
}

.sap-sections-title {
  font-size: var(--app-size-xs);
  font-weight: 700;
  color: var(--app-text-secondary);
  margin-bottom: 6px;
}

.sap-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--app-space-sm);
  padding: 6px var(--app-space-sm);
  font-size: var(--app-size-xs);
  border-radius: 4px;
  cursor: pointer;
}

.sap-section:hover { background: var(--app-highlight); }
.sap-section--active {
  background: var(--app-highlight);
  font-weight: 700;
}

.sap-section-count {
  font-size: var(--app-size-xs);
  color: var(--app-text-secondary);
  font-weight: 700;
}

.sap-table { min-height: 0; min-width: 0; overflow: hidden; }

.sap-tag { margin-right: var(--app-space-xs); }

:deep(.sap-row--selected) { background: var(--sap-row-selected-bg); }

/* ── 缩略图 ── */
.sap-thumb-wrap { position: relative; display: inline-flex; cursor: zoom-in; }
.sap-thumb {
  width: 48px; height: 48px; object-fit: contain;
  border: 2px solid var(--ink); border-radius: 4px; display: block;
}
.sap-thumb-empty { color: var(--app-text-secondary); }

/* ── 元素名称内联编辑 ── */
.sap-name-cell {
  display: inline-flex; align-items: center; gap: var(--app-space-xs);
  max-width: 100%; cursor: text; min-width: 0;
}
.sap-name-text {
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  font-size: var(--app-size-xs);
}
.sap-name--empty { color: var(--app-text-secondary); font-style: italic; }
.sap-name-icon { flex-shrink: 0; color: var(--app-text-secondary); opacity: 0; transition: opacity 0.12s; }
.sap-name-cell:hover .sap-name-icon { opacity: 1; }
.sap-name-input {
  width: 100%; box-sizing: border-box;
  font-size: var(--app-size-xs); font-family: inherit;
  padding: 2px 6px;
  border: 2px solid var(--ink); border-radius: 4px;
  background: var(--app-bg-card); color: var(--ink);
}

/* ── 放大浮层 ── */
/* ── 放大预览内容（外壳由 el-dialog 提供） ── */
.sap-enlarge {
  display: flex; gap: var(--app-space-md); align-items: flex-start;
  background: var(--app-bg-card);
  border: 3px solid var(--ink);
  border-radius: 6px 10px 6px 10px;
  box-shadow: 0 8px 32px var(--sap-enlarge-shadow-color);
  padding: var(--app-space-md);
  max-width: 90vw;
}
.sap-enlarge-img {
  width: 240px; height: 240px; object-fit: contain;
  border: 2px solid var(--ink); border-radius: 4px;
  background: var(--paper);
}
.sap-enlarge-detail {
  display: flex; flex-direction: column; gap: 6px;
  font-size: var(--app-size-xs);
  min-width: 220px; max-width: 320px;
}
.sap-enlarge-field {
  display: flex; gap: var(--app-space-sm); align-items: baseline;
  word-break: break-all;
}
.sap-enlarge-field span {
  flex-shrink: 0; width: 64px; font-weight: 700; color: var(--app-text-secondary);
}
</style>
