<script setup lang="ts">
import { onMounted, ref } from "vue"
import { useRouter } from "vue-router"
import { ElMessageBox, type FormInstance } from "element-plus"
import WorkbenchHeader from "@/shared/components/WorkbenchHeader.vue"
import SketchCard from "@/shared/components/SketchCard.vue"
import EmptyState from "@/shared/components/patterns/EmptyState.vue"
import ErrorState from "@/shared/components/patterns/ErrorState.vue"
import SkeletonCard from "@/shared/components/patterns/SkeletonCard.vue"
import { sketchTiltAt, sketchToneAt } from "@/shared/helpers/sketchCard"
import { useProjects } from "./composables/useProjects"

const router = useRouter()
const { projects, loading, creating, error, isEmpty, loadProjects, addProject, removeProject } =
  useProjects()

const createDialogVisible = ref(false)
const newProjectName = ref("")
const newProjectDesc = ref("")

const createFormRef = ref<FormInstance>()
/** 新建项目的字段级校验（按 L4 口径走 EP :rules，取代原 Toast 空值守卫） */
const createRules = {
  name: [{ required: true, message: "请输入项目名称", trigger: "blur" }],
}

onMounted(() => {
  loadProjects()
})

function openCreateDialog() {
  newProjectName.value = ""
  newProjectDesc.value = ""
  createDialogVisible.value = true
}

async function confirmCreate() {
  try {
    await createFormRef.value?.validate()
  } catch {
    // 校验失败：EP 的 validate 以 reject 表示，交由字段内联提示（非静默吞错）
    return
  }
  const created = await addProject(newProjectName.value, newProjectDesc.value)
  if (created) {
    createDialogVisible.value = false
    router.push(`/cases/projects/${created.id}`)
  }
}

function enterProject(id: number) {
  router.push(`/cases/projects/${id}`)
}

async function onDeleteProject(id: number, name: string) {
  try {
    await ElMessageBox.confirm(
      `删除项目「${name}」将同时删除其下全部目录与用例，此操作不可恢复。`,
      "确认删除项目",
      { confirmButtonText: "删除", cancelButtonText: "取消", type: "warning" },
    )
  } catch {
    return
  }
  await removeProject(id)
}
</script>

<template>
  <div class="doc-page doc-page--fixed wb-shell case-workbench project-list-page">
    <WorkbenchHeader
      title="用例管理"
      subtitle="按项目组织文档型测试用例，维护目录结构与用例表单"
      icon="layers"
      :icon-gradient="'linear-gradient(135deg,var(--c-case),var(--case-icon-accent))'"
    >
      <template #actions>
        <el-button type="primary" class="wb-btn" @click="openCreateDialog">+ 新建项目</el-button>
      </template>
    </WorkbenchHeader>

    <div v-if="loading" class="doc-body">
      <SkeletonCard variant="list" :lines="4" />
    </div>

    <ErrorState v-else-if="error" :message="error" @retry="loadProjects" />

    <div v-else class="doc-body">
      <EmptyState
        v-if="isEmpty"
        icon="📁"
        text="还没有用例项目"
        hint="创建第一个项目，开始维护目录与文档用例"
      >
        <el-button type="primary" @click="openCreateDialog">创建项目</el-button>
      </EmptyState>

      <div v-else class="project-grid">
        <SketchCard
          v-for="(item, index) in projects"
          :key="item.id"
          :title="item.name"
          :description="item.description"
          :meta="`${item.case_count} 条用例 · ${item.updated_at?.slice(0, 10) || '—'}`"
          icon="layers"
          :tone="sketchToneAt(index)"
          :tilt="sketchTiltAt(index)"
          deletable
          delete-label="删除项目"
          @activate="enterProject(item.id)"
          @delete="onDeleteProject(item.id, item.name)"
        />
      </div>
    </div>

    <el-dialog
      v-model="createDialogVisible"
      title="新建项目"
      width="440px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="createFormRef"
        :model="{ name: newProjectName }"
        :rules="createRules"
        label-position="top"
      >
        <el-form-item label="项目名称" prop="name">
          <el-input
            v-model="newProjectName"
            maxlength="200"
            placeholder="例如：制冰机回归用例"
            @keyup.enter="confirmCreate"
          />
        </el-form-item>
        <el-form-item label="项目描述">
          <el-input
            v-model="newProjectDesc"
            type="textarea"
            :rows="3"
            maxlength="500"
            placeholder="可选，简要说明项目范围"
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
/* 模块作用域色板：登记本页用到的非全局色值（消费点都在页面根之内；页面根即组件根） */

/* 页面根/主体骨架由 .doc-page / .doc-body 提供，这里只留本页增量 */
.project-list-page .doc-body {
  overflow-y: auto;
  padding: var(--app-space-lg);
}
.project-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--app-space-md);
}
</style>
