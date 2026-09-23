<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessageBox, type FormInstance } from 'element-plus'
import WorkbenchHeader from '@/shared/components/WorkbenchHeader.vue'
import SketchCard from '@/shared/components/SketchCard.vue'
import EmptyState from '@/shared/components/patterns/EmptyState.vue'
import ErrorState from '@/shared/components/patterns/ErrorState.vue'
import SkeletonCard from '@/shared/components/patterns/SkeletonCard.vue'
import { sketchTiltAt, sketchToneAt } from '@/shared/helpers/sketchCard'
import { usePrototypes } from './composables/usePrototypes'

const router = useRouter()
const { prototypes, loading, creating, error, isEmpty, loadPrototypes, addPrototype, removePrototype } =
  usePrototypes()

const createDialogVisible = ref(false)
const newName = ref('')
const newDesc = ref('')

const createFormRef = ref<FormInstance>()
/** 新建原型的字段级校验（按 L4 口径走 EP :rules，取代原 Toast 空值守卫） */
const createRules = {
  name: [{ required: true, message: '请输入原型名称', trigger: 'blur' }],
}

onMounted(() => {
  loadPrototypes()
})

function openCreateDialog() {
  newName.value = ''
  newDesc.value = ''
  createDialogVisible.value = true
}

async function confirmCreate() {
  try {
    await createFormRef.value?.validate()
  } catch {
    // 校验失败：EP 的 validate 以 reject 表示，交由字段内联提示（非静默吞错）
    return
  }
  const created = await addPrototype(newName.value, newDesc.value)
  if (created) {
    createDialogVisible.value = false
    router.push(`/workflow/prototypes/${created.id}`)
  }
}

function enterPrototype(id: number) {
  router.push(`/workflow/prototypes/${id}`)
}

async function onDelete(id: number, name: string) {
  try {
    await ElMessageBox.confirm(
      `删除原型「${name}」将同时删除其下全部目录与页面流，此操作不可恢复。`,
      '确认删除原型',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' },
    )
  } catch {
    return
  }
  await removePrototype(id)
}
</script>

<template>
  <div class="doc-page doc-page--fixed wb-shell proto-list-page">
    <WorkbenchHeader
      title="页面流"
      subtitle="按原型组织目录与页面流编排"
      icon="git-branch"
      :icon-gradient="'linear-gradient(135deg,var(--c-workflow),var(--wf-header-icon-end))'"
    >
      <template #actions>
        <el-button type="primary" class="wb-btn" @click="openCreateDialog">+ 新建原型</el-button>
      </template>
    </WorkbenchHeader>

    <div v-if="loading" class="doc-body">
      <SkeletonCard variant="list" :lines="4" />
    </div>

    <ErrorState v-else-if="error" :message="error" @retry="loadPrototypes" />

    <div v-else class="doc-body">
      <EmptyState
        v-if="isEmpty"
        icon="📁"
        text="还没有页面流原型"
        hint="创建第一个原型，开始维护目录与页面流"
      >
        <el-button type="primary" @click="openCreateDialog">创建原型</el-button>
      </EmptyState>

      <div v-else class="proto-grid">
        <SketchCard
          v-for="(item, index) in prototypes"
          :key="item.id"
          :title="item.name"
          :description="item.description"
          :meta="`${item.doc_count} 个页面流 · ${item.updated_at?.slice(0, 10) || '—'}`"
          icon="git-branch"
          :tone="sketchToneAt(index)"
          :tilt="sketchTiltAt(index)"
          deletable
          delete-label="删除原型"
          @activate="enterPrototype(item.id)"
          @delete="onDelete(item.id, item.name)"
        />
      </div>
    </div>

    <el-dialog
      v-model="createDialogVisible"
      title="新建原型"
      width="440px"
      :close-on-click-modal="false"
    >
      <el-form ref="createFormRef" :model="{ name: newName }" :rules="createRules" label-position="top">
        <el-form-item label="原型名称" prop="name">
          <el-input
            v-model="newName"
            maxlength="200"
            placeholder="例如：制冰机 App 主路径"
            @keyup.enter="confirmCreate"
          />
        </el-form-item>
        <el-form-item label="原型描述">
          <el-input
            v-model="newDesc"
            type="textarea"
            :rows="3"
            maxlength="500"
            placeholder="可选，简要说明原型范围"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="confirmCreate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
/* 页面根/主体骨架由 .doc-page / .doc-body 提供，这里只留本页增量 */
/* 页头图标渐变末端色：tokens.css 未登记，登记在本页根作用域，随根元素继承给页头图标块 */
.proto-list-page {
  --wf-header-icon-end: var(--color-blue-89) /* -> --color-blue-89 */;
}
.proto-list-page .doc-body {
  overflow-y: auto;
  padding: var(--app-space-lg);
}
.proto-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--app-space-md);
}
</style>
