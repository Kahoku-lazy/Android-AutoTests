<script setup lang="ts">
/**
 * 页面元素工作台：左侧截图矩形 + 右侧表格，双向高亮联动。
 */
import { computed, nextTick, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { TableInstance } from 'element-plus'
import EmptyState from '@/shared/components/patterns/EmptyState.vue'
import { formatApiError } from '@/shared/api-client'
import { apiPageItems, apiUpdateElement } from '../api'
import PageScreenshotOverlay from './PageScreenshotOverlay.vue'

export interface PageElementRow {
  id: number
  alias: string
  text_val: string
  resource_id: string
  bounds: string
  x: number
  y: number
  width: number
  height: number
  is_test_point: boolean
  clickable: boolean
  class_name: string
  _first_xpath: string
}

const props = defineProps<{
  pageId: number
}>()

const loading = ref(false)
const error = ref('')
const pageElements = ref<PageElementRow[]>([])
const screenshotPath = ref('')
const elementFilter = ref<'all' | 'clickable' | 'text' | 'testpoint'>('all')
const selectedId = ref<number | null>(null)
const tableRef = ref<TableInstance>()

const elementCount = computed(() => pageElements.value.length)

function xpathItemToString(item: unknown): string {
  if (item == null) return ''
  if (typeof item === 'string') return item
  if (typeof item === 'object') {
    const obj = item as Record<string, unknown>
    for (const key of ['xpath', 'path', 'value', 'expr']) {
      if (typeof obj[key] === 'string' && obj[key]) return obj[key] as string
    }
  }
  return ''
}

function firstXpath(raw: unknown): string {
  if (raw == null) return ''
  if (Array.isArray(raw)) return xpathItemToString(raw[0])
  if (typeof raw === 'object') return xpathItemToString(raw)
  if (typeof raw !== 'string') return ''
  const text = raw.trim()
  if (!text) return ''
  try {
    const parsed = JSON.parse(text)
    if (Array.isArray(parsed)) return xpathItemToString(parsed[0])
    return xpathItemToString(parsed) || text
  } catch {
    return text
  }
}

function mapPageElements(list: Record<string, unknown>[]): PageElementRow[] {
  return list.map((e) => ({
    id: Number(e.id),
    alias: String(e.alias || ''),
    text_val: String(e.text_val || ''),
    resource_id: String(e.resource_id || ''),
    bounds: String(e.bounds || ''),
    x: Number(e.x) || 0,
    y: Number(e.y) || 0,
    width: Number(e.width) || 0,
    height: Number(e.height) || 0,
    is_test_point: Boolean(e.is_test_point),
    clickable: Boolean(e.clickable),
    class_name: String(e.class_name || ''),
    _first_xpath: firstXpath(e.xpath_candidates),
  }))
}

async function loadElements() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await apiPageItems(props.pageId, elementFilter.value, 500)
    const payload = data as {
      status?: boolean
      elements?: Record<string, unknown>[]
      screenshot_path?: string
      message?: string
    }
    if (payload.status) {
      pageElements.value = mapPageElements(payload.elements || [])
      screenshotPath.value = String(payload.screenshot_path || '')
      if (
        selectedId.value != null &&
        !pageElements.value.some((row) => row.id === selectedId.value)
      ) {
        selectedId.value = null
      }
    } else {
      error.value = payload.message || '页面元素加载失败'
      pageElements.value = []
      screenshotPath.value = ''
    }
  } catch (e: unknown) {
    error.value = formatApiError(e as never, '加载失败')
    pageElements.value = []
    screenshotPath.value = ''
  } finally {
    loading.value = false
  }
}

watch(
  () => [props.pageId, elementFilter.value] as const,
  () => {
    selectedId.value = null
    void loadElements()
  },
  { immediate: true },
)

function rowClassName({ row }: { row: PageElementRow }) {
  return row.id === selectedId.value ? 'page-row--active' : ''
}

async function scrollRowIntoView(id: number) {
  await nextTick()
  const root = tableRef.value?.$el as HTMLElement | undefined
  if (!root) return
  const tr = root.querySelector(
    `.el-table__body tr[data-row-key="${id}"]`,
  ) as HTMLElement | null
  tr?.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
}

async function selectElement(id: number, source: 'table' | 'shot') {
  selectedId.value = id
  const row = pageElements.value.find((item) => item.id === id)
  if (row) tableRef.value?.setCurrentRow(row)
  if (source === 'shot') await scrollRowIntoView(id)
}

function onRowClick(row: PageElementRow) {
  void selectElement(row.id, 'table')
}

function onShotSelect(id: number) {
  void selectElement(id, 'shot')
}

async function updatePageElement(
  row: PageElementRow,
  field: 'alias' | 'is_test_point',
  value: string | boolean,
) {
  try {
    const { data } = await apiUpdateElement(row.id, { [field]: value })
    if (!(data as { status?: boolean }).status) {
      ElMessage.error((data as { message?: string }).message || '更新失败')
      return
    }
    const src = pageElements.value.find((x) => x.id === row.id)
    if (!src) return
    if (field === 'alias') src.alias = String(value)
    if (field === 'is_test_point') src.is_test_point = Boolean(value)
  } catch (e: unknown) {
    ElMessage.error(formatApiError(e as never, '更新失败'))
  }
}

function onAliasChange(row: unknown, value: string) {
  void updatePageElement(row as PageElementRow, 'alias', value)
}

function onTestPointChange(row: unknown, value: string | number | boolean) {
  void updatePageElement(row as PageElementRow, 'is_test_point', Boolean(value))
}

defineExpose({ reload: loadElements })
</script>

<template>
  <div class="page-workbench">
    <div class="page-workbench__toolbar">
      <span class="page-workbench__count">共 {{ elementCount }} 个元素</span>
      <el-radio-group v-model="elementFilter" size="small">
        <el-radio-button value="all">全部</el-radio-button>
        <el-radio-button value="clickable">可点击</el-radio-button>
        <el-radio-button value="text">有文本</el-radio-button>
        <el-radio-button value="testpoint">测试点</el-radio-button>
      </el-radio-group>
    </div>

    <div v-if="loading" class="page-workbench__loading">
      <el-skeleton :rows="6" animated />
    </div>
    <div v-else-if="error" class="page-workbench__error">
      <el-alert :title="error" type="error" show-icon :closable="false" />
      <el-button @click="loadElements">重试</el-button>
    </div>

    <div v-else class="page-workbench__split">
      <aside class="page-workbench__shot">
        <PageScreenshotOverlay
          :screenshot-path="screenshotPath"
          :elements="pageElements"
          :selected-id="selectedId"
          @select="onShotSelect"
        />
      </aside>

      <section class="page-workbench__table">
        <EmptyState
          v-if="!pageElements.length"
          icon="📋"
          text="该页面暂无元素"
          hint="可从设备检查器导入快照"
        />
        <el-table
          v-else
          ref="tableRef"
          :data="pageElements"
          border
          stripe
          height="100%"
          class="page-elements-table"
          row-key="id"
          highlight-current-row
          empty-text="暂无元素"
          :row-class-name="rowClassName"
          @row-click="onRowClick"
        >
          <el-table-column label="别名" min-width="120">
            <template #default="{ row }">
              <el-input
                :model-value="row.alias"
                size="small"
                placeholder="未命名"
                @click.stop
                @change="(v: string) => onAliasChange(row, v)"
              />
            </template>
          </el-table-column>
          <el-table-column prop="text_val" label="文本" min-width="100" show-overflow-tooltip />
          <el-table-column
            prop="resource_id"
            label="resource-id"
            min-width="140"
            show-overflow-tooltip
          />
          <el-table-column label="XPath" min-width="180" show-overflow-tooltip>
            <template #default="{ row }">
              <code v-if="row._first_xpath" class="cell-code">{{ row._first_xpath }}</code>
              <span v-else class="cell-muted">—</span>
            </template>
          </el-table-column>
          <el-table-column prop="bounds" label="坐标" min-width="120" show-overflow-tooltip />
          <el-table-column label="测试点" width="88" align="center">
            <template #default="{ row }">
              <el-switch
                :model-value="row.is_test_point"
                @click.stop
                @change="(v: string | number | boolean) => onTestPointChange(row, v)"
              />
            </template>
          </el-table-column>
        </el-table>
      </section>
    </div>
  </div>
</template>

<style scoped>
.page-workbench {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  gap: var(--app-space-md);
}
.page-workbench__toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--app-space-md);
  flex-wrap: wrap;
  flex-shrink: 0;
}
.page-workbench__count {
  font-size: var(--app-size-sm);
  font-weight: 700;
  color: var(--ink);
}
.page-workbench__loading,
.page-workbench__error {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: var(--app-space-md);
}
.page-workbench__split {
  flex: 1 1 0;
  min-height: 0;
  display: grid;
  grid-template-columns: minmax(280px, 0.85fr) minmax(0, 1.15fr);
  gap: var(--app-space-md);
}
.page-workbench__table,
.page-workbench__shot {
  min-width: 0;
  min-height: 0;
  height: 100%;
  overflow: hidden;
}
.page-elements-table {
  height: 100%;
}
.page-elements-table :deep(.page-row--active > td.el-table__cell) {
  background: color-mix(in srgb, var(--c-element) 18%, var(--paper)) !important;
}
.page-elements-table :deep(.el-table__body tr.current-row > td.el-table__cell) {
  background: color-mix(in srgb, var(--c-element) 18%, var(--paper)) !important;
}
.cell-code {
  font-family: var(--app-font-mono, ui-monospace, monospace);
  font-size: var(--app-size-xs);
  color: var(--ink);
}
.cell-muted {
  color: var(--app-text-secondary);
}

@media (max-width: 1100px) {
  .page-workbench__split {
    grid-template-columns: 1fr;
    /* 窄屏：上截图、下表格 */
    grid-template-rows: minmax(280px, 1.1fr) minmax(240px, 0.9fr);
  }
}
</style>
