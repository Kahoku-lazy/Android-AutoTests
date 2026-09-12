<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import WorkbenchHeader from '@/shared/components/WorkbenchHeader.vue'
import EmptyState from '@/shared/components/patterns/EmptyState.vue'
import ErrorState from '@/shared/components/patterns/ErrorState.vue'
import { useProjects } from './composables/useProjects'

const router = useRouter()
const { projects, loading, creating, error, isEmpty, loadProjects, addProject, removeProject } =
  useProjects()

const createDialogVisible = ref(false)
const newProjectName = ref('')
const newProjectDesc = ref('')

onMounted(() => {
  loadProjects()
})

function openCreateDialog() {
  newProjectName.value = ''
  newProjectDesc.value = ''
  createDialogVisible.value = true
}

async function confirmCreate() {
  const created = await addProject(newProjectName.value, newProjectDesc.value)
  if (created) {
    createDialogVisible.value = false
    router.push(`/cases/projects/${created.id}`)
  }
}

function enterProject(id: number) {
  router.push(`/cases/projects/${id}`)
}

async function onDeleteProject(id: number, name: string, event: Event) {
  event.stopPropagation()
  try {
    await ElMessageBox.confirm(
      `删除项目「${name}」将同时删除其下全部目录与用例，此操作不可恢复。`,
      '确认删除项目',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' },
    )
  } catch {
    return
  }
  await removeProject(id)
}
</script>

<template>
  <div class="project-list-page">
    <WorkbenchHeader
      title="用例管理"
      subtitle="按项目组织文档型测试用例，维护目录结构与用例表单"
      icon="layers"
      :icon-gradient="'linear-gradient(135deg,var(--c-case),#6ee7d8)'"
    >
      <template #actions>
        <el-button type="primary" class="wb-btn" @click="openCreateDialog">+ 新建项目</el-button>
      </template>
    </WorkbenchHeader>

    <div v-if="loading" class="project-list-page__body project-list-page__body--loading">
      <el-skeleton :rows="4" animated />
    </div>

    <ErrorState v-else-if="error" :message="error" @retry="loadProjects" />

    <div v-else class="project-list-page__body">
      <EmptyState
        v-if="isEmpty"
        icon="📁"
        text="还没有用例项目"
        hint="创建第一个项目，开始维护目录与文档用例"
      >
        <el-button type="primary" @click="openCreateDialog">创建项目</el-button>
      </EmptyState>

      <div v-else class="project-grid">
        <article
          v-for="item in projects"
          :key="item.id"
          class="project-card"
          role="button"
          tabindex="0"
          @click="enterProject(item.id)"
          @keydown.enter.prevent="enterProject(item.id)"
        >
          <div class="project-card__accent" />
          <div class="project-card__body">
            <h3 class="project-card__title">{{ item.name }}</h3>
            <p v-if="item.description" class="project-card__desc">{{ item.description }}</p>
            <p v-else class="project-card__desc project-card__desc--muted">暂无描述</p>
            <div class="project-card__meta">
              <span>{{ item.case_count }} 条用例</span>
              <span>{{ item.updated_at?.slice(0, 10) || '—' }}</span>
            </div>
          </div>
          <button
            type="button"
            class="project-card__delete"
            title="删除项目"
            @click="onDeleteProject(item.id, item.name, $event)"
          >
            删除
          </button>
        </article>
      </div>
    </div>

    <el-dialog
      v-model="createDialogVisible"
      title="新建项目"
      width="440px"
      :close-on-click-modal="false"
    >
      <el-form label-position="top">
        <el-form-item label="项目名称" required>
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
.project-list-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}
.project-list-page__body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: var(--app-space-lg);
}
.project-list-page__body--loading {
  max-width: 720px;
}
.project-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--app-space-md);
}
.project-card {
  position: relative;
  display: flex;
  flex-direction: column;
  border: 2px solid var(--case-border-subtle);
  border-radius: var(--app-radius-lg);
  background: var(--case-bg-card);
  cursor: pointer;
  transition: border-color var(--app-duration) var(--app-ease),
    box-shadow var(--app-duration) var(--app-ease);
  overflow: hidden;
}
.project-card:hover,
.project-card:focus-visible {
  border-color: var(--c-case);
  box-shadow: var(--app-shadow-sm);
  outline: none;
}
.project-card__accent {
  height: 4px;
  background: var(--c-case);
}
.project-card__body {
  padding: var(--app-space-md);
  flex: 1;
}
.project-card__title {
  margin: 0 0 var(--app-space-xs);
  font-size: var(--app-size-md);
  font-weight: 700;
  color: var(--ink);
}
.project-card__desc {
  margin: 0 0 var(--app-space-sm);
  font-size: var(--app-size-sm);
  color: var(--app-text-secondary);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.project-card__desc--muted {
  font-style: italic;
}
.project-card__meta {
  display: flex;
  justify-content: space-between;
  gap: var(--app-space-sm);
  font-size: var(--app-size-xs);
  color: var(--app-text-secondary);
}
.project-card__delete {
  position: absolute;
  top: var(--app-space-sm);
  right: var(--app-space-sm);
  border: 1px solid var(--case-border);
  background: var(--case-bg-subtle);
  color: var(--case-step-error);
  font-size: var(--app-size-xs);
  padding: 2px var(--app-space-sm);
  border-radius: var(--app-radius-sm);
  cursor: pointer;
}
.project-card__delete:hover {
  background: var(--case-badge-danger-bg);
}
</style>
