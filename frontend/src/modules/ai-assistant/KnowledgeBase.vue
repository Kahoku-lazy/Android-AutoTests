<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Card, Button, Table } from 'animal-island-vue'
import client from '@/shared/api-client.js'

const status = ref({})
const documents = ref([])
const loading = ref(false)
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
  { title: '来源', dataIndex: 'source', width: '50%' },
  { title: '类型', dataIndex: 'type', width: '20%' },
  { title: '大小', dataIndex: 'size', width: '15%' },
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
    const { data } = await client.get('/ai/knowledge/status')
    if (data.ok) status.value = data.data
  } catch { /* ignore */ }
}

async function fetchDocuments() {
  loading.value = true
  try {
    const { data } = await client.get('/ai/knowledge/documents')
    if (data.ok) documents.value = data.data.documents || []
  } catch (e) {
    ElMessage.error('加载文档列表失败')
  } finally { loading.value = false }
}

async function reindex() {
  reindexing.value = true
  try {
    const { data } = await client.post('/ai/knowledge/reindex')
    if (data.ok) {
      ElMessage.success('索引重建已开始，请稍后刷新')
      setTimeout(() => { fetchStatus(); fetchDocuments() }, 3000)
    } else {
      ElMessage.error(data.error || '索引重建失败')
    }
  } catch (e) {
    ElMessage.error('索引重建请求失败')
  } finally { reindexing.value = false }
}

onMounted(() => {
  fetchStatus()
  fetchDocuments()
})
</script>

<template>
  <div class="kb-view">
    <!-- 状态卡片 -->
    <Card color="app-blue" pattern="app-blue">
      <div class="kb-stats">
        <div class="kb-stat">
          <span class="kb-stat__num">{{ status.doc_count ?? '—' }}</span>
          <span class="kb-stat__label">已索引文档</span>
        </div>
        <div class="kb-stat">
          <span class="kb-stat__num">{{ status.db_size_mb ?? '—' }} MB</span>
          <span class="kb-stat__label">数据库大小</span>
        </div>
        <div class="kb-stat">
          <span class="kb-stat__num">{{ status.reindex?.last_indexed || '从未' }}</span>
          <span class="kb-stat__label">最后索引时间</span>
        </div>
        <div class="kb-stat">
          <span class="kb-stat__num" :style="{ color: status.reindex?.running ? '#f8a6b2' : '#6fba2c' }">
            {{ status.reindex?.running ? '⏳ 重建中' : '✅ 就绪' }}
          </span>
          <span class="kb-stat__label">状态</span>
        </div>
      </div>
      <div class="kb-actions">
        <Button type="primary" :loading="reindexing" @click="reindex">
          {{ reindexing ? '重建中…' : '🔄 重建索引' }}
        </Button>
        <span class="kb-hint">扫描 dev_docs/ 下所有 .md 文件并向量化索引</span>
      </div>
    </Card>

    <!-- 文档列表 -->
    <Card color="brown" pattern="brown" style="margin-top: 16px; padding: 20px 24px;">
      <div class="kb-filters">
        <button
          v-for="tab in filters"
          :key="tab.key"
          :class="['kb-filter-btn', { active: activeFilter === tab.key }]"
          @click="activeFilter = tab.key"
        >{{ tab.label }}</button>
      </div>
      <Table
        :columns="columns"
        :data-source="filteredDocs"
        row-key="id"
        :loading="loading"
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
      </Table>
    </Card>
  </div>
</template>

<style scoped>
.kb-view { padding: 0; }
.kb-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}
.kb-stat {
  text-align: center;
  padding: 12px 8px;
  background: rgba(136, 157, 240, 0.06);
  border-radius: 12px;
}
.kb-stat__num {
  display: block;
  font-size: 22px;
  font-weight: 800;
  color: var(--animal-text-color);
}
.kb-stat__label {
  display: block;
  font-size: 12px;
  color: var(--animal-text-color-secondary);
  margin-top: 4px;
}
.kb-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}
.kb-hint {
  font-size: 13px;
  color: var(--animal-text-color-secondary);
}
.kb-doc-source {
  font-family: monospace;
  font-size: 12px;
  color: var(--animal-text-color);
}
.kb-filters {
  display: flex;
  gap: 6px;
  margin-bottom: 14px;
}
.kb-filter-btn {
  padding: 6px 16px;
  border: none;
  border-radius: 8px;
  background: rgba(121, 79, 39, 0.05);
  font-size: 13px;
  font-weight: 700;
  color: var(--animal-text-color-secondary);
  cursor: pointer;
  font-family: inherit;
}
.kb-filter-btn:hover { color: var(--animal-text-color); }
.kb-filter-btn.active {
  background: var(--animal-text-color);
  color: #fff;
}
@media (max-width: 700px) {
  .kb-stats { grid-template-columns: repeat(2, 1fr); }
}
</style>
