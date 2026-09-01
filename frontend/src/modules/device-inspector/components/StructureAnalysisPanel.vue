<script setup>
/** 结构分析面板 — 纯规则分区结果展示（6 层分区树 + 元素档案表）。
 *  展示组件，不碰 HTTP；元素名称可内联重命名（回写 store → 保存时作为 alias 落库）。
 */
import { ref, computed, nextTick } from 'vue'
import { useElementStore, mediaUrl } from '../store'
import { IconEdit } from '@/shared/icons'
import EmptyState from '@/shared/components/patterns/EmptyState.vue'

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
        <el-table
          :data="activeElements"
          size="small"
          height="100%"
          row-key="_idx"
          @row-click="onRowClick"
          :row-class-name="({ row }) => (isRowSelected(row) ? 'sap-row--selected' : '')"
        >
          <el-table-column width="66" label="缩略图">
            <template #default="{ row }">
              <div v-if="row.thumbnail_path" class="sap-thumb-wrap" role="button" tabindex="0"
                @click.stop="openEnlarge(row)"
                @keydown.enter.prevent="openEnlarge(row)"
                @keydown.space.prevent="openEnlarge(row)">
                <img :src="mediaUrl(row.thumbnail_path)" class="sap-thumb" />
              </div>
              <span v-else class="sap-thumb-empty">—</span>
            </template>
          </el-table-column>
          <el-table-column label="元素名称" min-width="120">
            <template #default="{ row }">
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
          </el-table-column>
          <el-table-column label="标识" min-width="140" show-overflow-tooltip>
            <template #default="{ row }">{{ elLabel(row) }}</template>
          </el-table-column>
          <el-table-column label="元素" min-width="120" show-overflow-tooltip>
            <template #default="{ row }">{{ row.resource_id || '—' }}</template>
          </el-table-column>
          <el-table-column label="指标" width="150">
            <template #default="{ row }">
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
          </el-table-column>
          <el-table-column label="XPath" min-width="200" show-overflow-tooltip>
            <template #default="{ row }">{{ bestXPath(row) || '—' }}</template>
          </el-table-column>
          <el-table-column label="bounds" width="150" show-overflow-tooltip>
            <template #default="{ row }">{{ row.bounds || '—' }}</template>
          </el-table-column>
        </el-table>
      </section>
    </div>

    <EmptyState v-else text="暂无结构数据" hint="点击工具栏「结构分析」生成页面分区" />

    <!-- 缩略图放大浮层 -->
    <Teleport to="body">
      <div v-if="enlargeVisible && enlargeRow" class="sap-enlarge-mask" @click="closeEnlarge">
        <div class="sap-enlarge" @click.stop>
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
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.sap { height: 100%; min-height: 0; display: flex; flex-direction: column; overflow: hidden; }

.sap-webview-hint {
  flex-shrink: 0;
  margin-bottom: 10px;
  padding: 8px 12px;
  font-size: var(--app-size-xs);
  font-weight: 700;
  color: var(--app-footer-yellow-text);
  background: var(--app-highlight, #FFE066);
  border: 2px solid var(--app-ink, #2d2d2d);
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
  padding: 8px;
  background: var(--app-bg-card);
  border: 2px solid var(--app-ink, #2d2d2d);
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
  gap: 8px;
  padding: 6px 8px;
  font-size: var(--app-size-xs);
  border-radius: 4px;
  cursor: pointer;
}

.sap-section:hover { background: var(--app-highlight, #FFE066); }
.sap-section--active {
  background: var(--app-highlight, #FFE066);
  font-weight: 700;
}

.sap-section-count {
  font-size: var(--app-size-xs);
  color: var(--app-text-secondary);
  font-weight: 700;
}

.sap-table { min-height: 0; min-width: 0; overflow: hidden; }

.sap-tag { margin-right: 4px; }

:deep(.sap-row--selected) { background: rgba(167, 139, 250, 0.18); }

/* ── 缩略图 ── */
.sap-thumb-wrap { position: relative; display: inline-flex; cursor: zoom-in; }
.sap-thumb {
  width: 48px; height: 48px; object-fit: contain;
  border: 2px solid var(--app-ink, #2d2d2d); border-radius: 4px; display: block;
}
.sap-thumb-empty { color: var(--app-text-secondary); }

/* ── 元素名称内联编辑 ── */
.sap-name-cell {
  display: inline-flex; align-items: center; gap: 4px;
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
  border: 2px solid var(--app-ink, #2d2d2d); border-radius: 4px;
  background: var(--app-bg-card); color: var(--app-ink, #2d2d2d);
}

/* ── 放大浮层 ── */
.sap-enlarge-mask {
  position: fixed; inset: 0; z-index: 2000;
  background: rgba(0, 0, 0, 0.45);
  display: flex; align-items: center; justify-content: center;
}
.sap-enlarge {
  display: flex; gap: 16px; align-items: flex-start;
  background: var(--app-bg-card, #fff);
  border: 3px solid var(--app-ink, #2d2d2d);
  border-radius: 6px 10px 6px 10px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
  padding: 16px;
  max-width: 90vw;
}
.sap-enlarge-img {
  width: 240px; height: 240px; object-fit: contain;
  border: 2px solid var(--app-ink, #2d2d2d); border-radius: 4px;
  background: var(--doodle-bg, #faf5ee);
}
.sap-enlarge-detail {
  display: flex; flex-direction: column; gap: 6px;
  font-size: var(--app-size-xs);
  min-width: 220px; max-width: 320px;
}
.sap-enlarge-field {
  display: flex; gap: 8px; align-items: baseline;
  word-break: break-all;
}
.sap-enlarge-field span {
  flex-shrink: 0; width: 64px; font-weight: 700; color: var(--app-text-secondary);
}
</style>
