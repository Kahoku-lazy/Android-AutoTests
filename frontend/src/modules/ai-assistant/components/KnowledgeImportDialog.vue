<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  visible: { type: Boolean, default: false },
  allDocs: { type: Array, default: () => [] },
  importedDocIds: { type: Array, default: () => [] },
})

const emit = defineEmits(['import', 'close'])

const searchText = ref('')
const selectedIds = ref(new Set())

const filteredDocs = computed(() => {
  const query = searchText.value.trim().toLowerCase()
  const importedSet = new Set(props.importedDocIds)
  // Only show docs that haven't been imported yet
  const available = props.allDocs.filter(d => !importedSet.has(d.id))
  if (!query) return available
  return available.filter(d =>
    d.source.toLowerCase().includes(query) ||
    d.id.toLowerCase().includes(query) ||
    (d.type || '').toLowerCase().includes(query)
  )
})

const selectedCount = computed(() => selectedIds.value.size)

function isSelected(id) { return selectedIds.value.has(id) }

function toggleDoc(id) {
  const next = new Set(selectedIds.value)
  next.has(id) ? next.delete(id) : next.add(id)
  selectedIds.value = next
}

function selectAll() {
  selectedIds.value = new Set(filteredDocs.value.map(d => d.id))
}

function deselectAll() {
  selectedIds.value = new Set()
}

function handleImport() {
  if (selectedIds.value.size === 0) {
    ElMessage.warning('请至少选择一个文档')
    return
  }
  emit('import', [...selectedIds.value])
  selectedIds.value = new Set()
  searchText.value = ''
}

function handleClose() {
  selectedIds.value = new Set()
  searchText.value = ''
  emit('close')
}

function formatSize(bytes) {
  if (!bytes) return '0 B'
  return bytes < 1024 ? `${bytes} B` : bytes < 1048576 ? `${(bytes/1024).toFixed(1)} KB` : `${(bytes/1048576).toFixed(1)} MB`
}
</script>

<template>
  <el-dialog
    :model-value="visible"
    title="从知识库导入文档"
    width="650px"
    :close-on-click-modal="false"
    @update:model-value="val => { if (!val) handleClose() }"
  >
    <div class="import-dialog-body">
      <div class="import-search">
        <input
          v-model="searchText"
          class="import-search-input"
          placeholder="搜索文档..."
          @input="(e) => searchText = e.target.value"
        />
      </div>
      <div class="import-select-row">
        <el-button size="small" text type="primary" @click="selectAll">全选</el-button>
        <el-button size="small" text type="primary" @click="deselectAll">全部取消</el-button>
        <span class="import-count">已选 {{ selectedCount }} 个</span>
      </div>
      <div class="import-doc-list">
        <div v-if="!filteredDocs.length" class="import-empty">没有可导入的文档</div>
        <div
          v-for="doc in filteredDocs" :key="doc.id"
          class="import-doc-item"
          :class="{ selected: isSelected(doc.id) }"
          @click="toggleDoc(doc.id)"
        >
          <el-checkbox :model-value="isSelected(doc.id)" />
          <div class="import-doc-info">
            <span class="import-doc-name">{{ doc.source || doc.id }}</span>
            <span class="import-doc-meta">{{ doc.type }} · {{ formatSize(doc.size) }}</span>
          </div>
        </div>
      </div>
    </div>
    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" @click="handleImport">确认导入 ({{ selectedCount }})</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.import-dialog-body { display: flex; flex-direction: column; gap: 12px; }
.import-search { margin-bottom: 4px; }
.import-search-input {
  width: 100%; padding: 10px 14px; border: 1.5px solid var(--ai-warm-border);
  border-radius: 10px; font-size: var(--app-size-sm); font-family: inherit;
  background: var(--ai-warm-bg); color: var(--ink); outline: none;
  box-sizing: border-box;
}
.import-search-input:focus { border-color: var(--ai-teal); }
.import-select-row { display: flex; align-items: center; gap: 8px; }
.import-count { font-size: var(--app-size-xs); color: var(--ai-ink-muted); margin-left: auto; }
.import-doc-list { max-height: 360px; overflow-y: auto; display: flex; flex-direction: column; gap: 4px; }
.import-empty { padding: 24px; text-align: center; color: var(--ai-ink-muted); font-size: var(--app-size-sm); }
.import-doc-item {
  display: flex; align-items: center; gap: 10px; padding: 10px 14px;
  border: 1.5px solid var(--ai-warm-border); border-radius: 10px;
  cursor: pointer; transition: all .15s; background: #fff;
}
.import-doc-item:hover { border-color: var(--ai-teal); background: var(--ai-teal-bg); }
.import-doc-item.selected { border-color: var(--ai-teal); background: var(--ai-teal-bg); }
.import-doc-info { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.import-doc-name { font-weight: 600; font-size: var(--app-size-sm); color: var(--ink); }
.import-doc-meta { font-size: var(--app-size-xs); color: var(--ai-ink-muted); }
</style>
