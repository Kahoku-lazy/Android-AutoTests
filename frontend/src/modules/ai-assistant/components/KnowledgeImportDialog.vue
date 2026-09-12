<script setup lang="ts">
/** KnowledgeImportDialog — 上传文件到 data/rag_datas */
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { addKnowledgeDocument } from '../api/toolbox'
import { KB_UPLOAD_ACCEPT, KB_UPLOAD_SUBDIRS } from '../constants'

const props = defineProps<{
  visible?: boolean
}>()

const emit = defineEmits<{
  imported: [ids: string[]]
  close: []
}>()

const files = ref<File[]>([])
const subdir = ref('')
const uploading = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)

watch(
  () => props.visible,
  (open) => {
    if (!open) {
      files.value = []
      subdir.value = ''
      uploading.value = false
    }
  },
)

function onPick(event: Event) {
  const input = event.target as HTMLInputElement
  files.value = input.files ? [...input.files] : []
}

function handleClose() {
  emit('close')
}

async function handleImport() {
  if (!files.value.length) {
    ElMessage.warning('请选择要导入的文件')
    return
  }
  uploading.value = true
  const ids: string[] = []
  try {
    for (const file of files.value) {
      const data = await addKnowledgeDocument(file, subdir.value)
      if (!data.status || !data.data?.id) {
        ElMessage.error(data.message || `${file.name} 导入失败`)
        return
      }
      ids.push(String(data.data.id))
    }
    ElMessage.success(`已导入 ${ids.length} 个文件`)
    emit('imported', ids)
  } catch {
    ElMessage.error('导入失败')
  } finally {
    uploading.value = false
  }
}
</script>

<template>
  <el-dialog
    :model-value="visible"
    title="导入文档到知识库"
    width="520px"
    :close-on-click-modal="false"
    @update:model-value="val => { if (!val) handleClose() }"
  >
    <div class="import-dialog-body">
      <p class="import-hint">文件保存到 data/rag_datas，支持 md / txt / Word / PDF。</p>
      <div class="import-row">
        <span class="import-label">目标目录</span>
        <el-select v-model="subdir" style="width: 200px">
          <el-option
            v-for="opt in KB_UPLOAD_SUBDIRS"
            :key="opt.value || 'root'"
            :label="opt.label"
            :value="opt.value"
          />
        </el-select>
      </div>
      <input
        ref="fileInput"
        type="file"
        multiple
        :accept="KB_UPLOAD_ACCEPT"
        class="import-file"
        @change="onPick"
      />
      <ul v-if="files.length" class="import-files">
        <li v-for="f in files" :key="f.name">{{ f.name }}</li>
      </ul>
    </div>
    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" :loading="uploading" @click="handleImport">
        确认导入{{ files.length ? ` (${files.length})` : '' }}
      </el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.import-dialog-body { display: flex; flex-direction: column; gap: 12px; }
.import-hint { margin: 0; font-size: var(--app-size-sm); color: var(--app-ink-muted); }
.import-row { display: flex; align-items: center; gap: 10px; }
.import-label { font-size: var(--app-size-sm); font-weight: 700; color: var(--ink); }
.import-file { font-size: var(--app-size-sm); }
.import-files {
  margin: 0; padding-left: 18px; font-size: var(--app-size-sm); color: var(--ink);
}
</style>
