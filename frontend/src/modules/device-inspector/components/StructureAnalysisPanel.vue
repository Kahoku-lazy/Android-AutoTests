<script setup>
/** 结构分析面板 — 分组列表 + 元素档案表（两级分组展示）。
 *  展示组件，不碰 HTTP：左栏为固定五项分组（无复位项，已选分组不可清空）；
 *  元素名称可内联重命名（回写 store → 保存时作为 alias 落库）；
 *  选择列的勾选集合写回 store.checkedIds，作为「保存到元素定位」的筛减范围。
 *  主定位一律取后端 primary，页面不再自行从候选里挑选。
 */
import { ref, computed, nextTick, shallowRef, toRef, watch, watchPostEffect } from 'vue'
import { useElementStore } from '../store'
import {
  DEFAULT_PAGE_SIZE,
  ELEMENT_COLUMN_WIDTHS,
  EMPTY_TEXT,
  FROZEN_COLUMN_COUNT,
  PAGE_SIZE_OPTIONS,
  TABLE_MIN_WIDTH_PX,
} from '../constants'
import { usePagination } from '@/shared/composables/usePagination'
import { useTableDragScroll } from '@/shared/composables/useTableDragScroll'
import { mediaUrl } from '@/shared/helpers/mediaUrl'
import { IconEdit } from '@/shared/icons'
import EmptyState from '@/shared/components/patterns/EmptyState.vue'
import AppTable from '@/shared/components/AppTable.vue'

const store = useElementStore()

const props = defineProps({
  groups: { type: Array, default: () => [] },
  activeGroupId: { type: String, default: '' },
  elements: { type: Array, default: () => [] },
  selected: { type: Object, default: null },
})
const emit = defineEmits(['select', 'update:activeGroupId'])

/** 切分组：只上抛选择，复位与请求由父层/store 决定 */
function selectGroup(group) {
  if (!group?.id || group.id === props.activeGroupId) return
  emit('update:activeGroupId', group.id)
}

// ── 行选中联动：仅双击数据格写入选中（截图红框）；单击名称只重命名 ──
const enlargeVisible = ref(false)
const enlargeRow = ref(null)
/** 缩略图文件已失效（404）的行键：回落 — 占位，不留浏览器破图 */
const brokenThumbs = ref(new Set())
const enlargeBroken = ref(false)

function markThumbBroken(row) {
  const key = row?._rowKey
  if (key == null) return
  const next = new Set(brokenThumbs.value)
  next.add(key)
  brokenThumbs.value = next
}

// ── 元素名称内联重命名 ──
const editingIdx = ref(null)
const editDraft = ref('')
let nameInputEl = null
function setNameInputRef(el) { nameInputEl = el }

// ── 分页（每页固定 14 行；用共享 composable，不自建 totalPages/goPage）──
const { currentPage, totalPages, pagedItems, goPage } = usePagination(toRef(props, 'elements'), {
  pageSize: DEFAULT_PAGE_SIZE,
  options: PAGE_SIZE_OPTIONS,
})

/** 共享 composable 不会在结果集变小时回第 1 页，这里补上（切分组 / 换快照） */
watch([() => props.activeGroupId, () => props.elements], () => goPage(1))

// ── 横向滚动与首列冻结 ──
// 横向滚动由 el-table 自身承载（表头由 EP 同步、前 N 列由 EP fixed 冻结）；
// 拖拽平移作用在 el-table 的横向滚动容器上，而非外层（外层只是定高容器）。
const tableBodyRef = ref(null)  // 纯 JS 文件：不得写 TS 泛型
/** EP 的横向滚动实际落在 body-wrapper 内的 .el-scrollbar__wrap 上（body-wrapper 自身 overflow:hidden）。
 *  该元素只在有数据时渲染，故在 DOM 更新后再解析（watchPostEffect），而不是一次性计算。 */
const panTarget = shallowRef(null)  // 注意：本文件是纯 JS（无 lang="ts"），不得写 TS 泛型
watchPostEffect(() => {
  const hasRows = props.elements.length > 0
  panTarget.value = hasRows
    ? tableBodyRef.value?.querySelector('.el-scrollbar__wrap') ?? null
    : null
})
const { onTablePointerDown } = useTableDragScroll(panTarget)
/** 表格最小宽来自列宽常量（列宽合计），样式里不写字面量 */
const tableStyle = { '--insp-table-min-width': `${TABLE_MIN_WIDTH_PX}px` }

// ── 选择列（勾选 = 保存到元素定位的筛减范围；行键用 store 补的 _rowKey）──
const allChecked = computed(() =>
  pagedItems.value.length > 0 &&
  pagedItems.value.every(e => store.checkedIds.has(e._rowKey))
)

/** 全选只作用于当前页所示行（跨页勾选由 store.checkedIds 全量持有，不被清空） */
function toggleAll() {
  const next = new Set(store.checkedIds)
  if (allChecked.value) {
    pagedItems.value.forEach(e => next.delete(e._rowKey))
  } else {
    pagedItems.value.forEach(e => next.add(e._rowKey))
  }
  store.checkedIds = next
}

/** 元素档案表列定义（前 FROZEN_COLUMN_COUNT 列为冻结列，必须是显式宽度以保证冻结偏移确定）。
 *  列顺序与列宽的唯一登记处：constants.ts。 */
const W = ELEMENT_COLUMN_WIDTHS
const COLUMN_SPECS = [
  { dataIndex: '_select', width: W.select, label: '', showOverflowTooltip: false },
  { dataIndex: 'thumbnail', width: W.thumbnail, label: '缩略图', showOverflowTooltip: false },
  { dataIndex: 'name', width: W.name, label: '元素名称', showOverflowTooltip: false },
  { dataIndex: 'seq', minWidth: W.seq, label: '序号' },
  { dataIndex: 'className', minWidth: W.className, label: '类名' },
  { dataIndex: 'resourceId', minWidth: W.resourceId, label: '资源标识' },
  { dataIndex: 'text', minWidth: W.text, label: '文本' },
  { dataIndex: 'contentDesc', minWidth: W.contentDesc, label: '描述' },
  { dataIndex: 'coords', minWidth: W.coords, label: '坐标', showOverflowTooltip: false },
  { dataIndex: 'depth', minWidth: W.depth, label: '层级' },
  { dataIndex: 'indexAttr', minWidth: W.indexAttr, label: '父内序号' },
  { dataIndex: 'kind', minWidth: W.kind, label: '细类' },
  { dataIndex: 'kept', minWidth: W.kept, label: '保留', showOverflowTooltip: false },
  { dataIndex: 'flags', minWidth: W.flags, label: '交互标志', showOverflowTooltip: false },
  { dataIndex: 'xpath', minWidth: W.xpath, label: '主定位' },
]
const ELEMENT_COLUMNS = COLUMN_SPECS.map((col, index) =>
  index < FROZEN_COLUMN_COUNT ? { ...col, fixed: 'left' } : col
)

/** 左键双击数据格才在手机画面填淡红。名称只重命名，勾选和缩略图不改画面。 */
const ROW_DBLCLICK_SKIP = new Set(['name', '_select', 'thumbnail'])

function onRowDblClick(row, column) {
  if (ROW_DBLCLICK_SKIP.has(column?.property)) return
  emit('select', row)
}

function isRowSelected(row) {
  return props.selected && row._idx != null && row._idx === props.selected._idx
}

/** 元素名称：当次自定义名 → 已存别名 → 元素 text → 资源标识（口径与保存侧 alias 一致） */
function nameValue(row) {
  return store.nameOverrides[row._idx] || row.alias || row.text || row.resource_id || '—'
}

/** 快照来源缺失（无 snapshot_id）时无处回写，名称格只读展示 */
const canRename = computed(() => !!store.snapshot?.snapshot_id)

function startEdit(row) {
  if (!canRename.value) return
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

/** 单击缩略图列：在手机画面上高亮该元素对应的矩形框（点击目标是整格，含无缩略图数据的占位态）。
 *  只改选中，MUST NOT 触发重命名或勾选；该列有缩略图数据时放大预览挂同一格的双击。 */
function onThumbnailClick(row) {
  if (!row) return
  emit('select', row)
}

function openEnlarge(row) {
  if (!row.thumbnail_path) return
  enlargeBroken.value = false
  enlargeRow.value = row
  enlargeVisible.value = true
}

function closeEnlarge() {
  enlargeVisible.value = false
  enlargeRow.value = null
}

/** 交互标志标签：键 → 文案；顺序固定，全为假时不渲染任何标签 */
const FLAG_LABELS = [
  ['clickable', '可点击'],
  ['long_clickable', '可长按'],
  ['scrollable', '可滚动'],
  ['checkable', '可勾选'],
  ['checked', '已勾选'],
  ['enabled', '启用'],
  ['focusable', '可聚焦'],
]
/** 少数标志给语义底色，其余用中性底（沿用原「指标」列的标签配色口径） */
const FLAG_TAG = { 可点击: 'success', 可滚动: 'info', 可勾选: 'warning', 已勾选: 'success' }

function flagLabels(row) {
  const flags = row?.flags || {}
  return FLAG_LABELS.filter(([key]) => flags[key]).map(([, label]) => label)
}

/** 坐标格第二行：中心点（后端给的 cx/cy，整数截断） */
function centerText(row) {
  const coords = row?.coords
  if (!coords) return ''
  return `中心 ${coords.cx}, ${coords.cy}`
}
</script>

<template>
  <div class="sap">
    <!-- 骨架常驻：无数据时左列分组空态、右列表格空态，区域不整块消失 -->
    <div class="sap-body">
      <!-- 左：分组列表（五项固定顺序；不提供复位项，已选分组不可清空） -->
      <aside class="sap-sections">
        <div class="sap-sections-title">元素分组</div>
        <div v-if="!groups.length" class="sap-sections-empty">暂无分组数据</div>
        <template v-else>
          <button
            v-for="g in groups"
            :key="g.id"
            type="button"
            class="sap-chip"
            :class="{ 'sap-chip--on': g.id === activeGroupId }"
            :aria-pressed="g.id === activeGroupId"
            :data-testid="'group-' + g.id"
            @click="selectGroup(g)"
          >
            <span class="sap-chip-name">{{ g.label }}</span>
            <span class="sap-chip-count">{{ g.count }}</span>
          </button>
        </template>
      </aside>

      <!-- 右：元素档案表（常驻；空数据由表内空态承担，分页栏在表纸之上） -->
      <section class="sap-table">
        <div class="sap-pager">
          <span class="sap-page-info">第 {{ currentPage }} / {{ totalPages }} 页 · 共 {{ elements.length }} 条</span>
          <div class="sap-page-nav">
            <el-button
              class="wb-btn"
              size="small"
              :disabled="currentPage <= 1"
              data-testid="page-prev"
              @click="goPage(currentPage - 1)"
            >上一页</el-button>
            <el-button
              class="wb-btn"
              size="small"
              :disabled="currentPage >= totalPages"
              data-testid="page-next"
              @click="goPage(currentPage + 1)"
            >下一页</el-button>
          </div>
        </div>
        <div
          ref="tableBodyRef"
          class="sap-table-body"
          :style="tableStyle"
          data-testid="table-pan"
          :data-pan-ready="panTarget ? 'true' : 'false'"
          @pointerdown="onTablePointerDown"
        >
        <AppTable
          accent="var(--c-element)"
          :striped="true"
          table-layout="fixed"
          :columns="ELEMENT_COLUMNS"
          :data-source="pagedItems"
          row-key="_idx"
          size="small"
          height="100%"
          :row-class-name="({ row }) => (isRowSelected(row) ? 'is-selected' : '')"
          @row-dblclick="onRowDblClick"
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

          <template #cell-thumbnail="{ row }">
            <!-- 定位层铺满整格：单击=在画面上高亮该元素（含该列无缩略图数据的占位态） -->
            <div
              class="sap-thumb-cell"
              role="button"
              tabindex="0"
              data-testid="thumb-locate"
              @click.stop="onThumbnailClick(row)"
              @keydown.enter.prevent="onThumbnailClick(row)"
              @keydown.space.prevent="onThumbnailClick(row)"
            >
              <div v-if="row.thumbnail_path" class="sap-thumb-wrap" role="button" tabindex="0"
                @dblclick.stop="openEnlarge(row)"
                @keydown.enter.prevent="openEnlarge(row)"
                @keydown.space.prevent="openEnlarge(row)">
                <img v-if="!brokenThumbs.has(row._rowKey)" :src="mediaUrl(row.thumbnail_path)"
                  class="sap-thumb" @error="markThumbBroken(row)" />
                <span v-else class="sap-thumb-empty">—</span>
              </div>
              <span v-else class="sap-thumb-empty">—</span>
            </div>
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
            <div v-else class="sap-name-cell" :class="{ 'sap-name-cell--readonly': !canRename }"
              :role="canRename ? 'button' : undefined" :tabindex="canRename ? 0 : undefined"
              @pointerdown.stop
              @click.stop="startEdit(row)"
              @keydown.enter.prevent="startEdit(row)">
              <span class="sap-name-text" :class="{ 'sap-name--empty': !nameValue(row) }">
                {{ nameValue(row) }}
              </span>
              <IconEdit v-if="canRename" :size="12" class="sap-name-icon" />
            </div>
          </template>

          <template #cell-seq="{ row }">{{ row.seq ?? '—' }}</template>
          <template #cell-className="{ row }">{{ row.class_simple || '—' }}</template>
          <template #cell-resourceId="{ row }">{{ row.resource_id || '—' }}</template>
          <template #cell-text="{ row }">{{ row.text || '—' }}</template>
          <template #cell-contentDesc="{ row }">{{ row.content_desc || '—' }}</template>
          <template #cell-coords="{ row }">
            <div class="sap-coords">
              <span>{{ row.coords?.bounds || '—' }}</span>
              <span v-if="centerText(row)" class="sap-coords-center">{{ centerText(row) }}</span>
            </div>
          </template>
          <template #cell-depth="{ row }">{{ row.depth ?? '—' }}</template>
          <template #cell-indexAttr="{ row }">{{ row.index_attr || '—' }}</template>
          <template #cell-kind="{ row }">{{ row.content_kind || '—' }}</template>
          <template #cell-kept="{ row }">
            <span v-if="row.kept_in_snapshot">保留</span>
            <span v-else class="sap-cell-tag">被裁</span>
          </template>
          <template #cell-flags="{ row }">
            <div v-if="flagLabels(row).length" class="sap-flags">
              <el-tag
                v-for="label in flagLabels(row)"
                :key="label"
                size="small"
                :type="FLAG_TAG[label] || 'info'"
                class="sap-tag"
              >{{ label }}</el-tag>
            </div>
            <span v-else>—</span>
          </template>
          <template #cell-xpath="{ row }">
            <div class="sap-xpath">
              <span class="sap-xpath-text">{{ row.primary?.xpath || '—' }}</span>
              <el-tag v-if="row.primary && row.primary.stable === false" size="small" type="warning" class="sap-tag">不稳定</el-tag>
            </div>
          </template>

          <template #empty>
            <EmptyState
              :text="EMPTY_TEXT.noDevice"
              hint="选择设备后点击「获取」，或从快照列表回看"
            />
          </template>
        </AppTable>
        </div>
      </section>
    </div>

    <!-- 缩略图放大预览（覆盖层统一走 EP，见 frontend/AGENTS.md「L5 覆盖层」） -->
    <el-dialog
      :model-value="enlargeVisible"
      title="缩略图预览"
      width="auto"
      @update:model-value="(v) => { if (!v) closeEnlarge() }"
    >
      <div v-if="enlargeRow" class="sap-enlarge">
        <div v-if="enlargeBroken || brokenThumbs.has(enlargeRow._rowKey)" class="sap-enlarge-missing">
          缩略图已失效
        </div>
        <img v-else :src="mediaUrl(enlargeRow.thumbnail_path)" class="sap-enlarge-img"
          @error="enlargeBroken = true" />
        <div class="sap-enlarge-detail">
          <div class="sap-enlarge-field"><span>名称</span>{{ nameValue(enlargeRow) }}</div>
          <div class="sap-enlarge-field"><span>Class</span>{{ enlargeRow.class_name || '—' }}</div>
          <div class="sap-enlarge-field"><span>ID</span>{{ enlargeRow.resource_id || '—' }}</div>
          <div class="sap-enlarge-field"><span>Desc</span>{{ enlargeRow.content_desc || '—' }}</div>
          <div class="sap-enlarge-field"><span>Bounds</span>{{ enlargeRow.coords?.bounds || '—' }}</div>
          <div class="sap-enlarge-field"><span>细类</span>{{ enlargeRow.content_kind || '—' }}</div>
          <div class="sap-enlarge-field">
            <span>交互标志</span>{{ flagLabels(enlargeRow).join(' · ') || '—' }}
          </div>
          <div class="sap-enlarge-field">
            <span>主定位</span>{{ enlargeRow.primary?.xpath || '—' }}
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<style scoped src="./StructureAnalysisPanel.css"></style>

<style scoped>
/* 新增单元格的少量样式；其余皮肤仍由 StructureAnalysisPanel.css 承担（本文件不改它）。
   色值与间距一律取令牌，不写字面量。 */
.sap-coords {
  display: flex;
  flex-direction: column;
  line-height: 1.35;
}

.sap-coords-center {
  font-size: var(--app-size-xs);
  color: var(--app-text-secondary);
}

.sap-flags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--app-space-xs);
}

/* 被裁元素：虚线 + 次要色，与「保留」的默认文字区分 */
.sap-cell-tag {
  display: inline-block;
  padding: 0 var(--app-space-xs);
  font-size: var(--app-size-xs);
  color: var(--app-text-secondary);
  border: 1.5px dashed var(--app-text-secondary);
  border-radius: var(--app-radius-sm);
}

.sap-xpath {
  display: flex;
  align-items: center;
  gap: var(--app-space-xs);
}

.sap-xpath-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>


