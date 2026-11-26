<script setup lang="ts">
import { onMounted, ref } from "vue"
import { useRouter } from "vue-router"
import { ElMessageBox, type FormInstance } from "element-plus"
import WorkbenchHeader from "@/shared/components/WorkbenchHeader.vue"
import SketchCard from "@/shared/components/SketchCard.vue"
import SectionDivider from "@/shared/components/SectionDivider.vue"
import DoodleBtn from "@/shared/components/DoodleBtn.vue"
import EmptyState from "@/shared/components/patterns/EmptyState.vue"
import ErrorState from "@/shared/components/patterns/ErrorState.vue"
import SkeletonCard from "@/shared/components/patterns/SkeletonCard.vue"
import { sketchTiltAt, sketchToneAt } from "@/shared/helpers/sketchCard"
import { useProjects } from "./composables/useProjects"
import { LIBRARY_OPTIONS, type LibraryKind } from "./types"

const router = useRouter()
const { projects, loading, creating, error, isEmpty, loadProjects, addProject, removeProject } =
  useProjects()

const createDialogVisible = ref(false)
const newProjectName = ref("")
const newProjectDesc = ref("")
const newLibraryKind = ref<LibraryKind>("automation")

const createFormRef = ref<FormInstance>()

const createRules = {
  name: [{ required: true, message: "请输入项目名称", trigger: "blur" }],
}

onMounted(() => {
  loadProjects()
})

function openCreateDialog() {
  newProjectName.value = ""
  newProjectDesc.value = ""
  newLibraryKind.value = "automation"
  createDialogVisible.value = true
}

async function confirmCreate() {
  try {
    await createFormRef.value?.validate()
  } catch {
    return
  }
  const created = await addProject(newProjectName.value, newLibraryKind.value, newProjectDesc.value)
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
      icon="layers"
      :icon-gradient="'linear-gradient(135deg,var(--c-case),var(--case-icon-accent))'"
    />

    <div v-if="loading" class="doc-body">
      <SkeletonCard variant="list" :lines="4" />
    </div>

    <ErrorState v-else-if="error" :message="error" @retry="loadProjects" />

    <div v-else class="doc-body">
      <div class="project-toolbar">
        <el-button type="primary" @click="openCreateDialog">新建项目</el-button>
      </div>

      <SectionDivider class="project-divider" />
      <EmptyState
        v-if="isEmpty"
        icon="📁"
        text="还没有用例项目"
        hint="创建一个自动化或功能项目，用例直接写在这一张表里"
      >
        <el-button type="primary" @click="openCreateDialog">创建项目</el-button>
      </EmptyState>

      <div v-else class="project-grid">
        <SketchCard
          v-for="(item, index) in projects"
          :key="item.id"
          :title="item.name"
          :description="item.description"
          :meta="`${item.library_kind === 'automation' ? '自动化' : '功能'} · ${item.case_count}/999`"
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
        <el-form-item label="库类型">
          <el-radio-group v-model="newLibraryKind">
            <el-radio-button v-for="item in LIBRARY_OPTIONS" :key="item.value" :value="item.value">
              {{ item.label }}
            </el-radio-button>
          </el-radio-group>
        </el-form-item>
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
        <div class="create-dialog__actions">
          <DoodleBtn tone="paper" @click="createDialogVisible = false">取消</DoodleBtn>
          <DoodleBtn tone="yellow" :disabled="creating" @click="confirmCreate">
            {{ creating ? "创建中…" : "创建" }}
          </DoodleBtn>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.project-list-page .doc-body {
  overflow-y: auto;
  padding: var(--app-space-lg);
}
.project-toolbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: var(--app-space-sm);
}

.create-dialog__actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--app-space-sm);
}

.project-divider {
  margin-bottom: var(--app-space-md);
}
.project-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--app-space-md);
}
</style>
