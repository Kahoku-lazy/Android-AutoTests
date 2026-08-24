<script setup>

import AppCard from "@/shared/components/AppCard.vue";
import KpiCard from "@/shared/components/KpiCard.vue";
import ErrorState from "@/shared/components/patterns/ErrorState.vue";
import KbTreeView from "./components/KbTreeView.vue";
import { buildKbTree } from "./helpers/kb-tree";
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

/** 按 dev_docs/ 本地目录层级构建折叠树 */
const docTree = computed(() => buildKbTree(filteredDocs.value))

async function fetchStatus() {
  try {
    const data = await getKnowledgeStatus()
    if (data.status) status.value = data.data
  } catch { /* ignore */ }
}

async function fetchDocuments() {
  loading.value = true
  try {
    const data = await getKnowledgeDocuments()
    if (data.status) documents.value = data.data?.documents || []
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
    const data = await reindexKnowledge()
    if (data.status) {
      ElMessage.success('索引重建已开始，请稍后刷新')
      setTimeout(() => { fetchStatus(); fetchDocuments() }, 3000)
    } else {
      ElMessage.error(data.message || '索引重建失败')
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
        <div v-if="loading" class="kb-empty">加载中...</div>
        <div v-else-if="!docTree.length" class="kb-empty">暂无文档，请先点击「重建索引」</div>
        <KbTreeView v-else :nodes="docTree" show-meta />
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
.kb-empty {
  padding: 32px;
  text-align: center;
  color: var(--ai-ink-muted);
  font-size: var(--app-size-sm);
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
