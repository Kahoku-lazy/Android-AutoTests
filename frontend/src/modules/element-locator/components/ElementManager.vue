<script setup>
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { animate, stagger } from 'animejs'
import {
  apiGetPages, apiCreatePage, apiUpdatePage, apiDeletePage,
  apiGetPageElements, apiAddElementToPage, apiUpdateElement, apiClearAll,
} from '../api.js'
import PageHeader from '@/shared/components/PageHeader.vue'
import { Modal, Button as AnimalButton, Card, Table, Tabs, Input, Switch } from 'animal-island-vue'

const pages = ref([])
const selectedPage = ref(null)
const elements = ref([])
const loading = ref(false)
const editingLabel = ref(null)
const labelInput = ref('')

// ── Dialogs ──
const showCreatePage = ref(false)
const newPageForm = ref({ label: '', package: '', activity: '' })

const showAddElement = ref(false)
const newElForm = ref({ alias: '', xpath: '', class_name: '', text_val: '', resource_id: '', bounds: '', clickable: false })

// ── Selection & Clear dialog ──
const selectedPageIds = reactive(new Set())
const showClearDialog = ref(false)
const clearSelectedOnly = ref(false)

onMounted(() => loadPages())

async function loadPages() {
  loading.value = true
  try {
    const { data } = await apiGetPages()
    if (data.ok) pages.value = data.pages || []
  } catch (_) { /* 加载失败时保持空列表，不打扰用户 */ }
  loading.value = false
  await nextTick()
  animate('.pages-list .page-row', { opacity: [0,1], translateX: [-12,0], delay: stagger(30), duration: 300 })
}

async function selectPage(page) {
  selectedPage.value = page
  elements.value = []
  if (!page) return
  try {
    const { data } = await apiGetPageElements(page.id)
    if (data.ok) elements.value = data.elements || []
  } catch (_) { /* 加载元素失败时保持空列表 */ }
  await nextTick()
  animate('.elements-table tbody tr', {
    opacity: [0, 1],
    translateY: [24, 0],
    scale: [0.96, 1],
    delay: stagger(35, { from: 'center', ease: 'outExpo' }),
    duration: 400,
    easing: 'easeOutCubic',
  })
}

// ── Create page ──
async function doCreatePage() {
  const label = newPageForm.value.label.trim()
  if (!label) return
  // 检查名称唯一
  if (pages.value.some(p => p.label === label)) {
    alert(`页面名称「${label}」已存在，请使用其他名称`)
    return
  }
  try {
    const { data } = await apiCreatePage(newPageForm.value)
    if (data.ok) {
      showCreatePage.value = false
      newPageForm.value = { label: '', package: '', activity: '' }
      await loadPages()
    } else {
      alert(data.error || '创建失败')
    }
  } catch (e) {
    alert(e?.response?.data?.error || '创建页面失败，请检查网络连接')
  }
}

// ── Add element ──
function openAddElement() {
  // Pre-fill info from current device
  newElForm.value = { alias: '', xpath: '', class_name: '', text_val: '', resource_id: '', bounds: '', clickable: false }
  showAddElement.value = true
}

async function doAddElement() {
  if (!newElForm.value.alias.trim()) return
  try {
    const { data } = await apiAddElementToPage(selectedPage.value.id, newElForm.value)
    if (data.ok) {
      showAddElement.value = false
      await selectPage(selectedPage.value)  // refresh elements
    }
  } catch (e) {
    alert(e?.response?.data?.error || '添加元素失败，请检查网络连接')
  }
}

// ── Page label edit ──
function startEditLabel(page) {
  editingLabel.value = page.id
  labelInput.value = page.label
  nextTick(() => { const inp = document.querySelector('.label-input'); if (inp) inp.focus() })
}
async function saveLabel(page) {
  const label = labelInput.value.trim()
  if (!label) return
  // 检查名称唯一（排除自身）
  if (pages.value.some(p => p.id !== page.id && p.label === label)) {
    alert(`页面名称「${label}」已存在，请使用其他名称`)
    return
  }
  try {
    const { data } = await apiUpdatePage(page.id, label)
    if (data.ok) {
      page.label = label
      if (selectedPage.value?.id === page.id) selectedPage.value.label = page.label
    } else {
      alert(data.error || '重命名失败')
    }
  } catch (e) {
    alert(e?.response?.data?.error || '重命名失败，请检查网络连接')
  }
  editingLabel.value = null
}
function cancelEdit() { editingLabel.value = null }

// ── Page selection ──
function togglePageSelection(pageId) {
  if (selectedPageIds.has(pageId)) {
    selectedPageIds.delete(pageId)
  } else {
    selectedPageIds.add(pageId)
  }
}
function isPageSelected(pageId) { return selectedPageIds.has(pageId) }

// ── Clear dialog ──
function openClearDialog() {
  clearSelectedOnly.value = selectedPageIds.size > 0
  showClearDialog.value = true
}

async function doClearPages() {
  showClearDialog.value = false
  if (clearSelectedOnly.value && selectedPageIds.size > 0) {
    for (const id of [...selectedPageIds]) {
      await apiDeletePage(id)
    }
    selectedPageIds.clear()
  } else {
    await apiClearAll()
  }
  // 如果当前选中的页面被删了，清空右侧面板
  if (selectedPage.value && !clearSelectedOnly.value) {
    selectedPage.value = null; elements.value = []
  }
  await loadPages()
}

async function deletePage(page) {
  if (!confirm(`确定删除「${page.label || 'Page #' + page.id}」？`)) return
  await apiDeletePage(page.id)
  if (selectedPage.value?.id === page.id) { selectedPage.value = null; elements.value = [] }
  await loadPages()
}

async function updateEl(el, field, value) {
  await apiUpdateElement(el.id, { [field]: value })
  el[field] = value
}

function pageLabel(page) { return page.label || `Page #${page.id}` }
function timeAgo(iso) {
  if (!iso) return ''
  const diff = Date.now() - new Date(iso).getTime()
  const m = Math.floor(diff / 60000)
  if (m < 1) return '刚刚'
  if (m < 60) return `${m}分钟前`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h}小时前`
  return new Date(iso).toLocaleDateString('zh-CN')
}

// ── Filter ──
const filterMode = ref('all')
const filterTabs = [
  { key: 'all', label: '全部' },
  { key: 'clickable', label: '可点击' },
  { key: 'aliased', label: '已命名' },
  { key: 'testpoint', label: '测试点' },
]
const filteredElements = computed(() => {
  switch (filterMode.value) {
    case 'clickable': return elements.value.filter(e => e.clickable)
    case 'testpoint': return elements.value.filter(e => e.is_test_point)
    case 'aliased':   return elements.value.filter(e => e.alias)
    default:          return elements.value
  }
})

// ── Table columns（百分比宽度，铺满容器）──
const columns = [
  { title: '名称', dataIndex: 'alias', key: 'alias', width: '12%' },
  { title: 'XPath', dataIndex: 'xpath', key: 'xpath', width: '28%' },
  { title: '类名', dataIndex: 'class_name', key: 'class_name', width: '15%' },
  { title: '文本', dataIndex: 'text_val', key: 'text_val', width: '12%' },
  { title: 'Resource ID', dataIndex: 'resource_id', key: 'resource_id', width: '18%' },
  { title: '可点击', dataIndex: 'clickable', key: 'clickable', width: '7%', align: 'center' },
  { title: '测试点', dataIndex: 'is_test_point', key: 'is_test_point', width: '8%', align: 'center' },
]
</script>

<template>
  <div class="doc-page">
    <PageHeader
      title="元素管理 Element Manager"
      subtitle="按页面组织元素库，维护 XPath、别名、测试点等定位信息"
      color="app-yellow"
    />

    <div class="doc-body">
      <div class="main-layout">
        <!-- Left: Page list -->
        <Card color="brown" pattern="brown" class="pages-card">
          <div class="panel-header">
            <h3 class="panel-title">
              页面列表
              <span class="doc-tag">Pages</span>
            </h3>
            <div class="panel-actions">
              <AnimalButton size="small" type="primary" @click="showCreatePage = true">+ 新建</AnimalButton>
              <AnimalButton size="small" type="primary" danger @click="openClearDialog">清空</AnimalButton>
            </div>
          </div>
          <div class="pages-list">
            <div v-if="loading && !pages.length" class="loading-text">加载中...</div>
            <div v-for="p in pages" :key="p.id"
              :class="['page-row', { active: selectedPage?.id === p.id }]"
              @click="selectPage(p)">
              <div class="page-row-top">
                <input type="checkbox" class="page-checkbox"
                  :checked="isPageSelected(p.id)"
                  @click.stop @change="togglePageSelection(p.id)"
                  title="选中此页面" />
                <span v-if="editingLabel === p.id" class="edit-label" @click.stop>
                  <input v-model="labelInput" class="label-input"
                    @keyup.enter="saveLabel(p)" @keyup.escape="cancelEdit" @blur="saveLabel(p)" />
                </span>
                <strong v-else class="page-name">{{ pageLabel(p) }}</strong>
                <span class="page-actions" @click.stop>
                  <AnimalButton size="small" type="text" @click="startEditLabel(p)">重命名</AnimalButton>
                  <AnimalButton size="small" type="text" danger @click="deletePage(p)">删除</AnimalButton>
                </span>
              </div>
              <div class="page-row-sub">
                <span v-if="p.package" class="page-pkg">{{ p.package }}</span>
                <span class="page-count">{{ p.element_count }} 元素</span>
                <span class="page-time">{{ timeAgo(p.created_at) }}</span>
              </div>
            </div>
            <div v-if="!pages.length && !loading" class="empty-list">暂无页面，点击「+ 新建页面」创建</div>
          </div>
        </Card>

        <!-- Right: Element table -->
        <template v-if="selectedPage">
          <div class="elements-panel">
            <div class="panel-header">
              <h3 class="panel-title">
                {{ pageLabel(selectedPage) }}
                <span class="doc-tag">Elements</span>
              </h3>
              <AnimalButton size="small" type="primary" @click="openAddElement">+ 添加元素</AnimalButton>
            </div>
            <div class="elements-subheader">
              <Tabs
                class="element-tabs"
                :items="filterTabs"
                v-model="filterMode"
                :leaf-animation="true"
                :shadow="true"
              >
                <template v-for="tab in filterTabs" #[tab.key] :key="tab.key">
                  <Card color="brown" pattern="brown" class="table-card">
                    <div class="table-scroll">
                      <Table
                        :columns="columns"
                        :data-source="filteredElements"
                        row-key="id"
                        :striped="true"
                        empty-text="暂无元素"
                        class="elements-table"
                      >
                      <!-- Custom cell: alias (inline edit) -->
                      <template #cell-alias="{ record }">
                        <input
                          class="cell-input"
                          :value="record.alias"
                          placeholder="未命名"
                          @blur="(e) => updateEl(record, 'alias', e.target.value)"
                          @keyup.enter="(e) => { updateEl(record, 'alias', e.target.value); e.target.blur() }"
                        />
                      </template>

                      <!-- Custom cell: xpath -->
                      <template #cell-xpath="{ record }">
                        <span v-if="record.xpath_candidates"
                          class="cell-code"
                          :title="(JSON.parse(record.xpath_candidates)[0] || {}).xpath || ''">
                          {{ (JSON.parse(record.xpath_candidates)[0] || {}).xpath || '—' }}
                        </span>
                        <span v-else class="text-muted">—</span>
                      </template>

                      <!-- Custom cell: text_val -->
                      <template #cell-text_val="{ record }">
                        <span v-if="record.text_val" class="cell-text">{{ record.text_val }}</span>
                        <span v-else class="text-muted">—</span>
                      </template>

                      <!-- Custom cell: resource_id -->
                      <template #cell-resource_id="{ record }">
                        <span v-if="record.resource_id" class="cell-code" :title="record.resource_id">{{ record.resource_id }}</span>
                        <span v-else class="text-muted">—</span>
                      </template>

                      <!-- Custom cell: clickable -->
                      <template #cell-clickable="{ value }">
                        <span :class="['clickable-badge', value ? 'clickable-yes' : 'clickable-no']">
                          {{ value ? '✓ 可点击' : '—' }}
                        </span>
                      </template>

                      <!-- Custom cell: is_test_point -->
                      <template #cell-is_test_point="{ record }">
                        <Switch
                          size="small"
                          :model-value="record.is_test_point"
                          @update:model-value="(val) => updateEl(record, 'is_test_point', val)"
                        />
                      </template>

                      <!-- Empty state -->
                      <template #empty>
                        <div class="table-empty">
                          <span>📋</span>
                          <p>暂无元素</p>
                          <AnimalButton size="small" type="primary" @click="openAddElement">添加第一个元素</AnimalButton>
                        </div>
                      </template>
                    </Table>
                    </div>
                  </Card>
                </template>
              </Tabs>
              <span class="element-count">共 {{ elements.length }} 个元素</span>
            </div>
          </div>
        </template>
        <Card v-else color="brown" pattern="brown" class="empty-card">
          <div class="empty-state">← 选择或创建页面</div>
        </Card>
      </div>
    </div>

    <!-- Create Page Dialog -->
    <Modal v-model:open="showCreatePage" title="新建页面" width="360px" @close="showCreatePage = false" @ok="doCreatePage">
      <div class="form-grid">
        <label class="form-label required">页面名称</label>
        <Input v-model="newPageForm.label" placeholder="如：登录页、首页" size="medium" />
      </div>
      <template #footer>
        <AnimalButton @click="showCreatePage = false">取消</AnimalButton>
        <AnimalButton type="primary" @click="doCreatePage">创建</AnimalButton>
      </template>
    </Modal>

    <!-- Clear Pages Confirm Dialog -->
    <Modal v-model:open="showClearDialog" title="清空页面" width="440px">
      <div class="clear-confirm">
        <p class="clear-warning">⚠️ 此操作将永久删除页面及关联元素，不可恢复。</p>
        <p class="clear-question">
          确定要清空<strong>{{ clearSelectedOnly && selectedPageIds.size > 0 ? `选中的 ${selectedPageIds.size} 个` : '所有' }}</strong>页面吗？
        </p>
        <label class="clear-option" :class="{ disabled: selectedPageIds.size === 0 }">
          <input type="checkbox" v-model="clearSelectedOnly" :disabled="selectedPageIds.size === 0" />
          <span>仅清除选中的页面（已选 {{ selectedPageIds.size }} 个）</span>
        </label>
      </div>
      <template #footer>
        <AnimalButton @click="showClearDialog = false">取消</AnimalButton>
        <AnimalButton type="primary" danger @click="doClearPages">确定清空</AnimalButton>
      </template>
    </Modal>

    <!-- Add Element Dialog -->
    <Modal v-model:open="showAddElement" title="添加元素" width="500px" @close="showAddElement = false" @ok="doAddElement">
      <div class="form-grid">
        <label class="form-label required">元素名称</label>
        <Input v-model="newElForm.alias" placeholder="如：登录按钮、用户名输入框" size="medium" />
        <label class="form-label">XPath</label>
        <Input v-model="newElForm.xpath" placeholder="元素定位 XPath" size="medium" />
        <label class="form-label">类名</label>
        <Input v-model="newElForm.class_name" placeholder="android.widget.Button" size="medium" />
        <label class="form-label">文本</label>
        <Input v-model="newElForm.text_val" placeholder="元素文本内容" size="medium" />
        <label class="form-label">Resource ID</label>
        <Input v-model="newElForm.resource_id" placeholder="com.example:id/btn" size="medium" />
        <label class="form-label">可点击</label>
        <Switch v-model="newElForm.clickable" size="medium" />
      </div>
      <template #footer>
        <AnimalButton @click="showAddElement = false">取消</AnimalButton>
        <AnimalButton type="primary" @click="doAddElement">添加</AnimalButton>
      </template>
    </Modal>
  </div>
</template>

<style scoped>
.doc-page {
  display: flex;
  flex-direction: column;
  min-height: min-content;
  width: 100%;
  min-width: 0;
}
.doc-body {
  flex: 1;
  padding-bottom: 24px;
  width: 100%;
  min-width: 0;
}
.main-layout {
  display: grid;
  grid-template-columns: 300px minmax(0, 1fr);
  gap: 16px;
  align-items: start;
  width: 100%;
}

/* ── Panel header ── */
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  flex-wrap: wrap;
  gap: 8px;
}
.panel-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary, #4A3A28);
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}
.doc-tag {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 8px;
  background: rgba(139, 115, 85, 0.1);
  color: #8b7355;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.panel-actions {
  display: flex;
  gap: 8px;
}
/* 让按钮颜色与 brown 卡片协调 */
.pages-card .panel-actions :deep(.animal-btn--primary:not(.animal-btn--danger)) {
  background: #8b7355;
  border-color: #8b7355;
  color: #fff;
}
.pages-card .panel-actions :deep(.animal-btn--primary:not(.animal-btn--danger):hover) {
  background: #7a6348;
  border-color: #7a6348;
}

/* ── Pages card ── */
.pages-card {
  display: flex;
  flex-direction: column;
  max-height: calc(100vh - 280px);
}
.pages-list {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}
.page-row {
  padding: 10px 12px;
  border-radius: 10px;
  cursor: pointer;
  border: 1px solid transparent;
  margin-bottom: 4px;
  transition: all .2s;
}
/* 相邻页面交替配色 — 3 种淡彩 + 左侧色条，确保相邻行颜色明显不同 */
.page-row { border-left: 3px solid transparent; }
.page-row:nth-child(3n+1) { background: #f0f7f4; border-left-color: #19c8b9; }  /* 青绿条 */
.page-row:nth-child(3n+2) { background: #faf5f0; border-left-color: #f7cd67; }  /* 暖黄条 */
.page-row:nth-child(3n)   { background: #f3f0f9; border-left-color: #b39ef3; }  /* 柔紫条 */
.page-row:hover { background: rgba(139, 115, 85, 0.12); border-color: rgba(139, 115, 85, 0.3); border-left-width: 3px; }
.page-row.active { background: #ddf3ea; border-color: #19c8b9; }
.page-row-top { display: flex; justify-content: space-between; align-items: center; gap: 6px; }
.page-checkbox {
  flex-shrink: 0;
  width: 16px; height: 16px;
  accent-color: var(--accent-blue, #889df0);
  cursor: pointer;
  margin: 0;
}
.page-name { font-size: 14px; color: var(--text-primary); }
.page-actions { display: flex; gap: 2px; opacity: 0; transition: opacity .15s; }
.page-row:hover .page-actions { opacity: 1; }
.page-actions :deep(.animal-btn--danger.animal-btn--text) {
  color: var(--animal-error-color, #e05a5a);
}
.page-actions :deep(.animal-btn--danger.animal-btn--text:hover:not(:disabled)) {
  color: var(--animal-error-color-hover, #e87878);
  background: rgba(224, 90, 90, 0.1);
}
.edit-label { flex: 1; }
.label-input { width: 100%; padding: 4px 8px; border: 1px solid var(--accent-blue); border-radius: 6px; font-size: 13px; background: #fff; color: var(--text-primary); outline: none; }
.page-row-sub { display: flex; gap: 8px; margin-top: 4px; font-size: 11px; color: var(--text-secondary); }
.page-pkg { font-family: monospace; max-width: 140px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.empty-list { text-align: center; color: var(--text-secondary); font-size: 13px; padding: 30px 0; }
.loading-text { text-align: center; color: var(--text-secondary); font-size: 13px; padding: 20px 0; }

/* ── Elements panel ── */
.elements-panel {
  display: flex;
  flex-direction: column;
  min-width: 0;
  gap: 8px;
}
.elements-subheader {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  min-width: 0;
  width: 100%;
  gap: 8px;
}
.element-tabs {
  flex: 1;
  min-width: 0;
  width: 100%;
}
.element-tabs :deep(.animal-tabs) {
  width: 100%;
}
.element-tabs :deep(.animal-tabs__content) {
  padding: 12px 0 0;
  width: 100%;
}
.element-tabs :deep(.animal-tabs__inner) {
  min-height: min-content;
  width: 100%;
}
.element-count {
  font-size: 12px;
  color: var(--text-secondary);
  white-space: nowrap;
  align-self: flex-end;
  padding-top: 0;
}

/* ── Table card ── */
.table-card {
  min-width: 0;
  width: 100%;
  padding: 0 !important;
}
.table-card :deep(.animal-card__content) {
  padding: 0;
  width: 100%;
}

/* ── Table scroll wrapper：极窄屏横向滚动，默认铺满宽度 */
.table-scroll {
  width: 100%;
  overflow-x: auto;
  overflow-y: visible;
  scrollbar-width: thin;
  scrollbar-color: rgba(139, 115, 85, 0.25) transparent;
}
.table-scroll::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
.table-scroll::-webkit-scrollbar-track {
  background: transparent;
}
.table-scroll::-webkit-scrollbar-thumb {
  background: rgba(139, 115, 85, 0.25);
  border-radius: 3px;
}
.table-scroll::-webkit-scrollbar-thumb:hover {
  background: rgba(139, 115, 85, 0.45);
}

/* ── Elements table ── */
.elements-table {
  width: 100%;
}
.elements-table :deep(.animal-table-wrapper) {
  width: 100%;
}
.elements-table :deep(table) {
  width: 100%;
  table-layout: fixed;
  border-collapse: separate;
  border-spacing: 0;
}

/* ── 表头：彩色渐变 ── */
.elements-table :deep(th) {
  font-size: 18px;
  font-weight: 800;
  color: #fff;
  padding: 16px 12px;
  text-align: left;
  text-transform: uppercase;
  letter-spacing: 0.4px;
  position: sticky;
  top: 0;
  z-index: 2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.elements-table :deep(th:nth-child(1)) { background: linear-gradient(135deg, #19c8b9, #15b0a3); border-radius: 10px 0 0 0; }
.elements-table :deep(th:nth-child(2)) { background: linear-gradient(135deg, #9b8fd4, #8275c2); }
.elements-table :deep(th:nth-child(3)) { background: linear-gradient(135deg, #f0a06a, #e88d52); }
.elements-table :deep(th:nth-child(4)) { background: linear-gradient(135deg, #7db84d, #6ba33b); }
.elements-table :deep(th:nth-child(5)) { background: linear-gradient(135deg, #6c93d4, #557ec0); }
.elements-table :deep(th:nth-child(6)) { background: linear-gradient(135deg, #f0c64a, #e0b830); text-align: center; }
.elements-table :deep(th:nth-child(7)) { background: linear-gradient(135deg, #e8879b, #d47085); text-align: center; border-radius: 0 10px 0 0; }

/* ── 单元格 ── */
.elements-table :deep(td) {
  padding: 13px 12px;
  font-size: 14px;
  color: #4A3A28;
  border-bottom: 1px solid rgba(0,0,0,0.04);
  vertical-align: middle;
  transition: all 0.2s ease;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ── 行交替配色（彩色） ── */
.elements-table :deep(tr:nth-child(3n+1) td) { background: rgba(25, 200, 185, 0.03); }
.elements-table :deep(tr:nth-child(3n+2) td) { background: rgba(136, 157, 240, 0.03); }
.elements-table :deep(tr:nth-child(3n) td)   { background: rgba(248, 166, 178, 0.03); }

/* ── 行 hover ── */
.elements-table :deep(tbody tr) {
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.elements-table :deep(tbody tr:hover td) {
  background: rgba(139, 115, 85, 0.06) !important;
  transform: scale(1.002);
}
.elements-table :deep(tbody tr:hover) {
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
  z-index: 1;
  position: relative;
}

/* ── 列专属样式 ── */
/* 名称列 — 青绿色强调 */
.elements-table :deep(td:nth-child(1)) { font-weight: 600; color: #0f8b7e; font-size: 14px; }
/* XPath 列 — 紫色调，等宽字体 */
.elements-table :deep(td:nth-child(2)) {
  font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', 'Consolas', 'SF Mono', monospace;
  font-size: 14px;
  color: #6254a0;
}
/* 类名列 — 橙色调等宽 */
.elements-table :deep(td:nth-child(3)) {
  font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', 'Consolas', 'SF Mono', monospace;
  font-size: 14px;
  color: #b8652e;
}
/* 文本列 — 绿色调 */
.elements-table :deep(td:nth-child(4)) { color: #4a7c2e; font-size: 14px; }
/* Resource ID 列 — 蓝色调等宽 */
.elements-table :deep(td:nth-child(5)) {
  font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', 'Consolas', 'SF Mono', monospace;
  font-size: 14px;
  color: #3b5fa0;
}
/* 可点击列 — 彩色徽章 */
.elements-table :deep(td:nth-child(6)) {
  text-align: center;
  font-size: 14px;
}
/* 测试点列 — 居中 */
.elements-table :deep(td:nth-child(7)) { text-align: center; }

/* ── 可点击徽章 ── */
.clickable-badge {
  display: inline-block;
  padding: 3px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.3px;
}
.clickable-yes {
  background: linear-gradient(135deg, #c8f0e8, #a3e8db);
  color: #0b6b5e;
}
.clickable-no {
  background: rgba(0,0,0,0.04);
  color: #bbb;
}

/* ── 空行提示 ── */
.elements-table :deep(td .text-muted) {
  color: #d0cdc8;
  font-style: italic;
  font-size: 11px;
}

/* ── Inline cell input ── */
.cell-input {
  width: 100%;
  padding: 5px 10px;
  border: 1px solid transparent;
  border-radius: 6px;
  font-size: 14px;
  background: transparent;
  color: #0f8b7e;
  font-weight: 600;
  outline: none;
  transition: border-color .2s;
}
.cell-input:hover { border-color: rgba(25, 200, 185, 0.25); }
.cell-input:focus { border-color: #19c8b9; background: rgba(25, 200, 185, 0.04); }

/* ── Cell code (XPath, class_name, resource_id) ── */
.cell-code {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', 'Consolas', 'SF Mono', monospace;
  font-size: 14px;
  letter-spacing: 0.2px;
}
.cell-text {
  font-size: 14px;
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ── Empty states ── */
.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  font-size: 14px;
  padding: 60px 0;
}
.empty-card {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
}
.table-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 48px 24px;
  color: #988B7A;
}
.table-empty span { font-size: 36px; }
.table-empty p { font-size: 15px; margin: 0; }

/* ── Utility ── */
.mono { font-family: monospace; font-size: 12px; }
.text-muted { color: #ccc; }

/* ── Modal form grid ── */
.form-grid {
  display: grid;
  grid-template-columns: 80px 1fr;
  gap: 14px 10px;
  align-items: center;
}
.form-label {
  text-align: right;
  font-size: 13px;
  color: var(--text-secondary, #988B7A);
  font-weight: 500;
  user-select: none;
}
/* ── Clear dialog ── */
.clear-confirm {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.clear-warning {
  color: #e05a5a;
  font-size: 14px;
  font-weight: 600;
  margin: 0;
  padding: 10px 14px;
  background: rgba(224, 90, 90, 0.06);
  border-radius: 10px;
  border: 1px solid rgba(224, 90, 90, 0.15);
}
.clear-question {
  font-size: 14px;
  color: var(--text-primary, #4A3A28);
  margin: 0;
}
.clear-option {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--text-secondary, #988B7A);
  cursor: pointer;
  user-select: none;
}
.clear-option.disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.clear-option input[type="checkbox"] {
  width: 16px; height: 16px;
  accent-color: var(--accent-blue, #889df0);
  cursor: pointer;
  margin: 0;
}

.form-label.required::before {
  content: '*';
  color: var(--animal-error-color, #e05a5a);
  margin-right: 3px;
}
</style>
