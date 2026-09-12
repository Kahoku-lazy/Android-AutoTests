<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import AppCard from "@/shared/components/AppCard.vue";
import KpiCard from "@/shared/components/KpiCard.vue";
import ErrorState from "@/shared/components/patterns/ErrorState.vue";
import KbTreeView from "./components/KbTreeView.vue";
import KnowledgeImportDialog from "./components/KnowledgeImportDialog.vue";
import KnowledgePreviewDrawer from "./components/KnowledgePreviewDrawer.vue";
import { buildKbTree, type KbTreeNode } from "./helpers/kb-tree";
import {
  getKnowledgeStatus, getKnowledgeDocuments, reindexKnowledge,
  fetchPlatformConfig, updatePlatformConfig,
} from './api/toolbox'

const props = defineProps<{ canManage?: boolean }>()

const status = ref<any>({})
const documents = ref<any[]>([])
const loading = ref(false)
const loadError = ref("")
const reindexing = ref(false)
const activeFilter = ref('all')

// ── 平台唯一智能体的知识库配置 ──
const kbEnabled = ref(false)
const knowledgeSources = ref({})
const showImportDialog = ref(false)
const previewPath = ref('')

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

/** 按 data/rag_datas 相对路径构建折叠树 */
const docTree = computed(() => buildKbTree(filteredDocs.value))

/** 已导入的引用范围（knowledge_sources → 展示项） */
const importedDocs = computed(() => {
  const sources = knowledgeSources.value || {}
  return Object.keys(sources).map(id => {
    if (id.startsWith('dir:')) {
      return { id, dirPath: id.slice(4), type: 'directory', enabled: sources[id] === true }
    }
    const doc = documents.value.find(d => d.id === id)
    return doc ? { ...doc, enabled: sources[id] === true } : null
  }).filter(Boolean)
})

function formatSize(bytes) {
  if (!bytes) return '0 B'
  return bytes < 1024 ? `${bytes} B` : bytes < 1048576 ? `${(bytes / 1024).toFixed(1)} KB` : `${(bytes / 1048576).toFixed(1)} MB`
}

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

async function fetchConfig() {
  try {
    const data = await fetchPlatformConfig()
    if (data.status && data.data) {
      kbEnabled.value = !!data.data.enable_knowledge_base
      knowledgeSources.value = data.data.knowledge_sources || {}
    }
  } catch { /* ignore */ }
}

async function loadAll() {
  loadError.value = ""
  await Promise.all([fetchStatus(), fetchDocuments(), fetchConfig()])
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

// ── 知识库配置写操作（乐观更新 + 失败回滚） ──

function toggleKb(val) {
  const prev = kbEnabled.value
  kbEnabled.value = val
  updatePlatformConfig({ enable_knowledge_base: val }).then((data) => {
    if (!data.status) { kbEnabled.value = prev; ElMessage.error(data.message || '操作失败') }
  }).catch(() => { kbEnabled.value = prev; ElMessage.error('操作失败') })
}

function toggleDocEnabled(id) {
  const sources = { ...knowledgeSources.value }
  sources[id] = !(sources[id] === true)
  knowledgeSources.value = sources
  updatePlatformConfig({ knowledge_sources: sources }).then((data) => {
    if (!data.status) ElMessage.error(data.message || '操作失败')
  }).catch(() => ElMessage.error('操作失败'))
}

function removeDoc(id) {
  const sources = { ...knowledgeSources.value }
  delete sources[id]
  knowledgeSources.value = sources
  updatePlatformConfig({ knowledge_sources: sources }).then((data) => {
    if (!data.status) ElMessage.error(data.message || '操作失败')
  }).catch(() => ElMessage.error('操作失败'))
}

function importDocs(keys: string[]) {
  const sources = { ...knowledgeSources.value }
  for (const id of keys) {
    if (!(id in sources)) sources[id] = true
  }
  knowledgeSources.value = sources
  updatePlatformConfig({ knowledge_sources: sources }).then((data) => {
    if (!data.status) ElMessage.error(data.message || '操作失败')
  }).catch(() => ElMessage.error('操作失败'))
  showImportDialog.value = false
}

function onImported(ids: string[]) {
  importDocs(ids)
  void fetchDocuments()
}

function onOpenFile(node: KbTreeNode) {
  if (node.type === 'file' && node.path) previewPath.value = node.path
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
        <span class="kb-hint">扫描 data/rag_datas 下的 Markdown 并向量化索引</span>
        <div class="kb-switch">
          <span class="kb-switch-label">知识库开关</span>
          <el-switch :model-value="kbEnabled" :disabled="!props.canManage" @update:model-value="toggleKb" />
        </div>
      </div>
      <p class="kb-hint" style="margin:8px 0 0">开启后 AI 回答问题时自动检索「引用范围」内已启用的文档 / 目录。</p>
    </AppCard>

    <!-- 引用范围（平台唯一智能体的知识库文档范围） -->
    <AppCard color="brown">
      <div class="kb-range-head">
        <span class="kb-range-title">引用范围</span>
        <span class="kb-range-count">{{ importedDocs.length }} 项</span>
        <el-button v-if="props.canManage" size="small" type="primary" @click="showImportDialog = true">📥 导入文档</el-button>
      </div>
      <div v-if="!importedDocs.length" class="kb-empty">
        暂未导入文档{{ props.canManage ? '，点击「导入文档」上传到 data/rag_datas' : '' }}
      </div>
      <div v-else class="kb-imported-list">
        <div v-for="doc in importedDocs" :key="doc.id" class="kb-doc-card">
          <div class="kb-doc-card-left">
            <span class="kb-doc-card-name">
              {{ doc.type === 'directory' ? '📁' : '📄' }} {{ doc.type === 'directory' ? doc.dirPath : (doc.source || doc.id) }}
            </span>
            <span class="kb-doc-card-meta">
              {{ doc.type === 'directory' ? '目录引用（动态包含其下全部文件）' : `${doc.type} · ${formatSize(doc.size)}` }}
            </span>
          </div>
          <div class="kb-doc-card-right">
            <span :class="['kb-doc-toggle', { on: doc.enabled }]"
                  role="button" tabindex="0"
                  :title="doc.enabled ? '已启用索引' : '已禁用索引'"
                  @click="props.canManage && toggleDocEnabled(doc.id)"
                  @keydown.enter.prevent="props.canManage && toggleDocEnabled(doc.id)"
                  @keydown.space.prevent="props.canManage && toggleDocEnabled(doc.id)">
              {{ doc.enabled ? '🔛' : '🔘' }}
            </span>
            <button v-if="props.canManage" class="kb-doc-remove-btn" @click="removeDoc(doc.id)" title="移除引用">✕</button>
          </div>
        </div>
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
        <div v-else-if="!docTree.length" class="kb-empty">暂无文档，请先点击「导入文档」</div>
        <KbTreeView v-else :nodes="docTree" show-meta @open="onOpenFile" />
      </div>
    </AppCard>

    <KnowledgeImportDialog
      :visible="showImportDialog"
      @imported="onImported" @close="showImportDialog = false"
    />
    <KnowledgePreviewDrawer
      v-if="previewPath"
      :path="previewPath"
      @close="previewPath = ''"
    />
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
  gap: var(--app-space-md);
  padding: 0;
}
.kb-view > :first-child {
  flex-shrink: 0;
}
.kpi-row { display:grid;grid-template-columns:var(--layout-kpi-cols);gap:var(--app-space-md);margin-bottom:var(--app-space-md) }
.kpi-row :deep(.kpi-card__value) {
  font-size: var(--app-size-sm);
  font-weight: 700;
  letter-spacing: 0.04em;
  line-height: 1.4;
}
@media (max-width: 768px) { .kpi-row { grid-template-columns: repeat(2, 1fr); } }
.kb-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.kb-hint {
  font-size: var(--app-size-sm);
  color: var(--app-ink-muted);
}
.kb-switch { margin-left: auto; display: inline-flex; align-items: center; gap: var(--app-space-sm); }
.kb-switch-label { font-size: var(--app-size-sm); font-weight: 700; color: var(--ink); }

.kb-range-head { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.kb-range-title { font-size: var(--app-size-md); font-weight: 700; color: var(--ink); }
.kb-range-count { font-size: var(--app-size-xs); color: var(--app-ink-muted); }
.kb-range-head .el-button { margin-left: auto; }

.kb-imported-list { display: flex; flex-direction: column; gap: var(--app-space-sm); }
.kb-doc-card {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px var(--app-space-md); border: 1.5px solid var(--ai-warm-border);
  border-radius: 12px; background: var(--app-bg-card); transition: border-color .15s;
}
.kb-doc-card:hover { border-color: var(--ai-teal); }
.kb-doc-card-left { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.kb-doc-card-name { font-weight: 600; font-size: var(--app-size-sm); color: var(--ink); }
.kb-doc-card-meta { font-size: var(--app-size-xs); color: var(--app-ink-muted); }
.kb-doc-card-right { display: flex; align-items: center; gap: var(--app-space-sm); flex-shrink: 0; }
.kb-doc-toggle { font-size:var(--app-size-md); cursor: pointer; opacity: 0.5; transition: opacity .15s; }
.kb-doc-toggle.on { opacity: 1; }
.kb-doc-toggle:hover { opacity: 0.8; }
.kb-doc-remove-btn {
  background: none; border: none; color: var(--app-ink-muted);
  font-size:var(--app-size-sm); cursor: pointer; padding: 2px 6px; border-radius: 4px;
  transition: all .15s;
}
.kb-doc-remove-btn:hover { color: #e74c3c; background: #fef0ef; }

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
  padding: 20px var(--app-space-lg);
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
  padding: var(--app-space-xl);
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
  padding: 6px var(--app-space-md);
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
