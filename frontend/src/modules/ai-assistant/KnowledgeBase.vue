<script setup>

import AppCard from "@/shared/components/AppCard.vue";
import AppTable from "@/shared/components/AppTable.vue";
import KpiCard from "@/shared/components/KpiCard.vue";
import ErrorState from "@/shared/components/patterns/ErrorState.vue";
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getKnowledgeStatus, getKnowledgeDocuments, reindexKnowledge } from './api/toolbox'

const status = ref({})
const documents = ref([])
const loading = ref(false)
const loadError = ref("")
const reindexing = ref(false)
const activeFilter = ref('all')

const filters = computed(() => [
  { key: 'all', label: `全部 (${documents.value.length})` },
  { key: 'project_doc', label: `项目文档 (${documents.value.filter(d => d.type === 'project_doc').length})` },
  { key: 'reference', label: `参考 (${documents.value.filter(d => d.type === 'reference').length})` },
  { key: 'manual', label: `手动 (${documents.value.filter(d => d.type === 'manual').length})` },
])

const filteredDocs = computed(() => {
  if (activeFilter.value === 'all') return documents.value
  return documents.value.filter(d => d.type === activeFilter.value)
})

const columns = [
  // 来源列只设 minWidth，其余空间由它吃掉，表格才能铺满
  { title: '来源', dataIndex: 'source', minWidth: 280, showOverflowTooltip: true },
  { title: '类型', dataIndex: 'type', width: 160 },
  { title: '大小', dataIndex: 'size', width: 120, align: 'right' },
]

function formatType(type) {
  const map = { project_doc: '📄 项目文档', reference: '📖 参考', manual: '✏️ 手动', generated: '🤖 自动' }
  return map[type] || type
}

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

async function fetchStatus() {
  try {
    const { ok, data } = await getKnowledgeStatus()
    if (ok) status.value = data
  } catch { /* ignore */ }
}

async function fetchDocuments() {
  loading.value = true
  try {
    const { ok, data } = await getKnowledgeDocuments()
    if (ok) documents.value = data.documents || []
  } catch (e) {
    loadError.value = "加载文档列表失败"
  } finally { loading.value = false }
}

async function loadAll() {
  loadError.value = ""
  await Promise.all([fetchStatus(), fetchDocuments()])
}

async function reindex() {
  reindexing.value = true
  try {
    const { ok, data, error } = await reindexKnowledge()
    if (ok) {
      ElMessage.success('索引重建已开始，请稍后刷新')
      setTimeout(() => { fetchStatus(); fetchDocuments() }, 3000)
    } else {
      ElMessage.error(error || '索引重建失败')
    }
  } catch (e) {
    ElMessage.error('索引重建请求失败')
  } finally { reindexing.value = false }
}

onMounted(() => { loadAll() })
</script>

<template>
  <div class="kb-view">
    <ErrorState v-if="loadError" :message="loadError" @retry="loadAll" />
    <!-- 状态卡片 -->
    <AppCard color="app-blue">
      <div class="kpi-row">
        <KpiCard :value="status.doc_count ?? '—'" label="已索引文档" color="var(--c-ai)" shape="diamond" />
        <KpiCard :value="`${status.db_size_mb ?? '—'} MB`" label="数据库大小" color="var(--c-case)" shape="triangle" />
        <KpiCard :value="status.reindex?.last_indexed || '从未'" label="最后索引时间" color="var(--c-workflow)" shape="square">
          <span style="font-size:var(--app-size-xs);color:var(--app-text-secondary)">YYYY-MM-DD HH:mm</span>
        </KpiCard>
        <KpiCard :value="status.reindex?.running ? '重建中' : '就绪'" label="状态" :color="status.reindex?.running ? 'var(--c-runner)' : 'var(--c-device)'" shape="circle" />
      </div>
      <div class="kb-actions">
        <el-button type="primary" :loading="reindexing" @click="reindex">
          {{ reindexing ? '重建中…' : '🔄 重建索引' }}
        </el-button>
        <span class="kb-hint">扫描 dev_docs/ 下所有 .md 文件并向量化索引</span>
      </div>
    </AppCard>

    <!-- 文档列表 -->
    <AppCard color="brown" class="kb-table-card">
      <div class="kb-filters">
        <button
          v-for="tab in filters"
          :key="tab.key"
          :class="['kb-filter-btn', { active: activeFilter === tab.key }]"
          @click="activeFilter = tab.key"
        >{{ tab.label }}</button>
      </div>
      <div class="kb-table-wrap">
        <AppTable
          :columns="columns"
          :data-source="filteredDocs"
          row-key="id"
          :loading="loading"
          table-layout="fixed"
          empty-text="暂无文档，请先点击「重建索引」"
        >
          <template #cell-source="{ record }">
            <span class="kb-doc-source">{{ record.source }}</span>
          </template>
          <template #cell-type="{ record }">
            <span>{{ formatType(record.type) }}</span>
          </template>
          <template #cell-size="{ record }">
            <span>{{ formatSize(record.size) }}</span>
          </template>
        </AppTable>
      </div>
    </AppCard>
  </div>
</template>

<style scoped>
.kb-view {
  flex: 1;
  min-height: 0;
  min-width: 0;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 0;
}
.kb-view > :first-child {
  flex-shrink: 0;
}
.kpi-row { display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:16px }
@media (max-width: 768px) { .kpi-row { grid-template-columns: repeat(2, 1fr); } }
.kb-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}
.kb-hint {
  font-size: var(--app-size-sm);
  color: var(--app-ink-muted);
}
.kb-table-card {
  flex: 1;
  min-height: 0;
  min-width: 0;
  width: 100%;
  display: flex;
  flex-direction: column;
  margin-top: 0;
}
.kb-table-card :deep(.el-card__body) {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  padding: 20px 24px;
  overflow: hidden;
}
.kb-table-wrap {
  flex: 1;
  min-height: 0;
  min-width: 0;
  width: 100%;
  overflow: auto;
}
.kb-table-wrap :deep(.ac-table),
.kb-table-wrap :deep(.el-table),
.kb-table-wrap :deep(.el-table__inner-wrapper),
.kb-table-wrap :deep(.el-table__header-wrapper),
.kb-table-wrap :deep(.el-table__body-wrapper),
.kb-table-wrap :deep(.el-table__header),
.kb-table-wrap :deep(.el-table__body) {
  width: 100% !important;
}
.kb-table-wrap :deep(.el-table .cell) {
  line-height: 1.45;
  padding: 8px 12px;
}
.kb-doc-source {
  font-family: var(--app-font-mono);
  font-size: var(--app-size-sm);
  color: var(--app-text, #3D4A3B);
  display: block;
  width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.kb-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 14px;
}
.kb-filter-btn {
  padding: 6px 16px;
  border: none;
  border-radius: 8px;
  background: rgba(121, 79, 39, 0.05);
  font-size: var(--app-size-sm);
  font-weight: 700;
  color: var(--app-ink-muted);
  cursor: pointer;
  font-family: inherit;
}
.kb-filter-btn:hover { color: var(--app-text, #3D4A3B); }
.kb-filter-btn.active {
  background: var(--app-text, #3D4A3B);
  color: var(--app-bg-card);
}
@media (max-width: 700px) {
  .kpi-row { grid-template-columns: repeat(2, 1fr); }
}
</style>
