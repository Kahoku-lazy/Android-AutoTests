<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { apiGetPages } from '@/modules/element-locator/api'
import { useElementStore } from '../store'

const store = useElementStore()

const pages = ref([])
const loading = ref(false)

const mode = ref('existing')            // 'existing' | 'create'
const folderPath = ref([])              // 级联目录 label 路径（逐层选择）
const selectedPageId = ref(null)        // 已有页面
const newPageLabel = ref('')

const saveFormRef = ref(null)
/** 保存目标的必填校验（按 L4 口径走 EP :rules，取代原 Toast 空值守卫） */
const saveRules = {
  selectedPageId: [{ required: true, message: '请选择要保存到的页面', trigger: 'change' }],
  newPageLabel: [{ required: true, message: '请填写新页面名称', trigger: 'blur' }],
}

// ── 页面树 → 级联目录 options（仅目录节点，逐层嵌套）──
function buildTree(pid) {
  return pages.value
    .filter(p => p.is_folder && (p.parent_id ?? null) === pid)
    .map(f => ({ value: f.label, label: f.label, children: buildTree(f.id) }))
}
const folderOptions = computed(() => buildTree(null))

/** 当前所选目录（末层 label）下挂的页面 */
const selectedFolderPages = computed(() => {
  if (!folderPath.value.length) {
    return pages.value.filter(p => !p.is_folder && (p.parent_id ?? null) === null)
  }
  const path = [...folderPath.value]
  let parentId = null
  for (let i = 0; i < path.length; i++) {
    const node = pages.value.find(p => p.is_folder && p.label === path[i] && (p.parent_id ?? null) === parentId)
    if (!node) return []
    parentId = node.id
  }
  return pages.value.filter(p => !p.is_folder && p.parent_id === parentId)
})

const folderPathText = computed(() => folderPath.value.join(' / '))

watch(() => store.saveDialogVisible, async (v) => {
  if (!v) return
  loading.value = true
  mode.value = 'existing'
  folderPath.value = []
  selectedPageId.value = null
  newPageLabel.value = store.snapshot?.package || ''
  try {
    const { data } = await apiGetPages()
    if (data.status) pages.value = data.pages || []
  } catch (e) { console.error(e) } finally {
    loading.value = false
  }
})

async function confirm() {
  try {
    await saveFormRef.value?.validate()
  } catch {
    // 校验失败：EP 的 validate 以 reject 表示，交由字段内联提示（非静默吞错）
    return
  }
  if (mode.value === 'existing') {
    store.saveToElements({
      pageId: selectedPageId.value,
      pageLabel: '',
      folderPath: '',
    })
  } else {
    store.saveToElements({
      pageLabel: newPageLabel.value.trim(),
      folderPath: folderPathText.value,
    })
  }
}
</script>

<template>
  <el-dialog
    v-model="store.saveDialogVisible"
    title="保存到元素定位"
    width="520px"
    :close-on-click-modal="false"
  >
    <div v-loading="loading" class="save-dlg">
      <el-form ref="saveFormRef" :model="{ selectedPageId, newPageLabel }" :rules="saveRules" label-width="90px" @submit.prevent>
        <el-form-item label="目录路径">
          <!-- el-cascader 不把 data-* 透传到 DOM，测试钩子必须挂在普通元素上才真实可达 -->
          <div class="save-folder-field" data-testid="save-folder-cascader">
            <el-cascader
              v-model="folderPath"
              :options="folderOptions"
              :props="{ checkStrictly: false }"
              placeholder="逐层选择目录（不选 = 根目录）"
              clearable
            />
          </div>
        </el-form-item>

        <el-form-item label="保存目标">
          <el-radio-group v-model="mode">
            <el-radio-button value="existing">已有页面</el-radio-button>
            <el-radio-button value="create">新建页面</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <el-form-item v-if="mode === 'existing'" label="选择页面" prop="selectedPageId">
          <el-select
            v-model="selectedPageId"
            placeholder="选择该目录下的页面"
            class="save-page-select"
            data-testid="save-page-select"
          >
            <el-option
              v-for="p in selectedFolderPages"
              :key="p.id"
              :value="p.id"
              :label="p.label || `Page #${p.id}`"
            />
          </el-select>
        </el-form-item>

        <el-form-item v-else label="页面名称" prop="newPageLabel">
          <el-input v-model="newPageLabel" placeholder="新页面名称" data-testid="save-label-input" />
        </el-form-item>
      </el-form>
    </div>
    <template #footer>
      <el-button @click="store.saveDialogVisible = false">取消</el-button>
      <el-button type="primary" :loading="store.saving" data-testid="save-confirm-btn" @click="confirm">
        保存
      </el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.save-dlg { min-height: 200px; }
/* el-cascader 的根节点不携带作用域属性，直接写 .save-folder 打不中；
   包裹层自己撑满，再用 :deep() 把宽度透传到子组件内部 */
.save-folder-field { width: 100%; }
.save-folder-field :deep(.el-cascader),
.save-page-select { width: 100%; }
</style>
