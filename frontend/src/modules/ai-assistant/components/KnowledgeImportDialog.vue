<script setup lang="ts">
/** KnowledgeImportDialog — 知识库导入弹窗：目录（dir:）与文件（doc:）混选 */
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import KbTreeView from './KbTreeView.vue'
import { buildKbTree, dirKeyToPath, type KbDoc } from '../helpers/kb-tree'

const props = defineProps<{
  visible?: boolean
  allDocs?: KbDoc[]
  importedDocIds?: (string | number)[]
}>()

const emit = defineEmits<{ import: [keys: string[]]; close: [] }>()

const searchText = ref('')
const selectedKeys = ref(new Set<string>())

const importedKeys = computed(() => new Set<string>((props.importedDocIds || []).map(String)))

/** 文档是否已被导入覆盖（文件键或某个目录键命中） */
function isCovered(doc: KbDoc): boolean {
  const keys = importedKeys.value
  if (keys.has(String(doc.id))) return true
  const src = doc.source || ''
  for (const k of keys) {
    if (k.startsWith('dir:')) {
      const dirPath = dirKeyToPath(k)
      if (src === dirPath || src.startsWith(dirPath + '/')) return true
    }
  }
  return false
}

const availableDocs = computed(() => {
  const query = searchText.value.trim().toLowerCase()
  const docs = (props.allDocs || []).filter(d => !isCovered(d))
  if (!query) return docs
  return docs.filter(d =>
    String(d.source || '').toLowerCase().includes(query) ||
    String(d.id).toLowerCase().includes(query) ||
    (d.type || '').toLowerCase().includes(query),
  )
})

const tree = computed(() => buildKbTree(availableDocs.value))

const selectedCount = computed(() => selectedKeys.value.size)

function toggleSelect(key: string) {
  const next = new Set(selectedKeys.value)
  next.has(key) ? next.delete(key) : next.add(key)
  selectedKeys.value = next
}

/** 全选 = 全部顶层节点键（目录保持 dir: 动态引用语义） */
function selectAll() {
  selectedKeys.value = new Set(tree.value.map(n => n.key))
}

function deselectAll() {
  selectedKeys.value = new Set()
}

function handleImport() {
  if (selectedKeys.value.size === 0) {
    ElMessage.warning('请至少选择一个文档或目录')
    return
  }
  emit('import', [...selectedKeys.value])
  selectedKeys.value = new Set()
  searchText.value = ''
}

function handleClose() {
  selectedKeys.value = new Set()
  searchText.value = ''
  emit('close')
}
</script>

<template>
  <el-dialog
    :model-value="visible"
    title="从知识库导入文档 / 目录"
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
        />
      </div>
      <div class="import-select-row">
        <el-button size="small" text type="primary" @click="selectAll">全选</el-button>
        <el-button size="small" text type="primary" @click="deselectAll">全部取消</el-button>
        <span class="import-count">已选 {{ selectedCount }} 项</span>
        <span class="import-hint">勾选目录 = 动态引用该目录下全部文件</span>
      </div>
      <div class="import-doc-list">
        <div v-if="!tree.length" class="import-empty">没有可导入的文档</div>
        <KbTreeView
          v-else
          :nodes="tree"
          selectable
          :selected-keys="selectedKeys"
          @toggle-select="toggleSelect"
        />
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
.import-select-row { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.import-count { font-size: var(--app-size-xs); color: var(--ai-ink-muted); margin-left: auto; }
.import-hint { font-size: var(--app-size-xs); color: var(--ai-ink-muted); }
.import-doc-list { max-height: 360px; overflow-y: auto; display: flex; flex-direction: column; gap: 4px; }
.import-empty { padding: 24px; text-align: center; color: var(--ai-ink-muted); font-size: var(--app-size-sm); }
</style>
