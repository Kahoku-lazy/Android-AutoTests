<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import WorkbenchHeader from '@/shared/components/WorkbenchHeader.vue'
import ErrorState from '@/shared/components/patterns/ErrorState.vue'
import ProjectTree from './components/ProjectTree.vue'
import { useProjectTree } from './composables/useProjectTree'

const route = useRoute()
const router = useRouter()

const projectId = computed(() => Number(route.params.projectId))

const {
  project,
  tree,
  error: treeError,
  loadTree,
  addDirectory,
  renameDirectory,
  removeDirectory,
  addFile,
  renameFile,
  removeFile,
  moveTreeItem,
} = useProjectTree(() => projectId.value)

const pageTitle = computed(() => project.value?.name || '项目工作台')

async function refreshTree() {
  await loadTree()
}

async function selectFile(fileId: number) {
  await router.push(`/cases/projects/${projectId.value}/files/${fileId}`)
}

async function onCreateDirectory(payload: { name: string; parentId: number | null }) {
  await addDirectory(payload.name, payload.parentId)
}

async function onRenameDirectory(payload: { id: number; name: string }) {
  await renameDirectory(payload.id, payload.name)
}

async function onDeleteDirectory(id: number) {
  await removeDirectory(id)
}

async function onCreateFile(payload: { name: string; directoryId: number | null }) {
  const fileId = await addFile(payload.name, payload.directoryId)
  if (fileId) await selectFile(fileId)
}

async function onRenameFile(payload: { id: number; name: string }) {
  await renameFile(payload.id, payload.name)
}

async function onDeleteFile(fileId: number) {
  await removeFile(fileId)
}

async function onMoveItem(payload: {
  itemType: 'directory' | 'file'
  itemId: number
  targetDirectoryId: number | null
}) {
  await moveTreeItem(payload.itemType, payload.itemId, payload.targetDirectoryId)
}

function goBack() {
  router.push('/cases')
}

onMounted(async () => {
  await loadTree()
})
</script>

<template>
  <div class="project-workspace">
    <WorkbenchHeader
      :title="pageTitle"
      subtitle="目录与文件 · 点文件进入表格编辑"
      icon="layers"
      :icon-gradient="'linear-gradient(135deg,var(--c-case),#6ee7d8)'"
    >
      <template #actions>
        <el-button class="wb-btn" @click="goBack">← 返回项目列表</el-button>
      </template>
    </WorkbenchHeader>

    <ErrorState v-if="treeError && !tree.length" :message="treeError" @retry="refreshTree" />

    <div v-else class="project-workspace__main">
      <ProjectTree
        :tree-data="tree"
        :active-file-id="null"
        @select-file="selectFile"
        @refresh="refreshTree"
        @create-directory="onCreateDirectory"
        @rename-directory="onRenameDirectory"
        @delete-directory="onDeleteDirectory"
        @create-file="onCreateFile"
        @rename-file="onRenameFile"
        @delete-file="onDeleteFile"
        @move-item="onMoveItem"
      />
    </div>
  </div>
</template>

<style scoped>
.project-workspace {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}
.project-workspace__main {
  flex: 1;
  min-height: 0;
  width: 100%;
  border-top: 2px solid var(--case-border-subtle);
  background-color: var(--paper);
  background-image: radial-gradient(circle, var(--dot) 0.6px, transparent 0.6px);
  background-size: 15px 15px;
  overflow: hidden;
}
</style>
