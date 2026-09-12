<script setup lang="ts">
/**
 * 项目目录工作台：只负责目录树。
 * 点击文件后路由跳转到独立详情页查看/编辑元素（对齐用例管理）。
 */
import { computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import WorkbenchHeader from '@/shared/components/WorkbenchHeader.vue'
import ErrorState from '@/shared/components/patterns/ErrorState.vue'
import LocatorTree from './components/LocatorTree.vue'
import { useLocatorTree } from './composables/useLocatorTree'
import { type LocatorFileKind } from './types'

const route = useRoute()
const router = useRouter()

const projectCode = computed(() => String(route.params.code || ''))

const {
  project,
  tree,
  error: treeError,
  loadTree,
  addDirectory,
  renameDirectory,
  removeDirectory,
  addFile,
  removeFile,
} = useLocatorTree(() => projectCode.value)

const pageTitle = computed(() => project.value?.name || '元素项目')

async function selectFile(id: number) {
  await router.push(`/elements/projects/${projectCode.value}/files/${id}`)
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
  const createdId = await addFile(payload.name, payload.directoryId)
  if (createdId) await selectFile(createdId)
}

async function onDeleteFile(payload: { fileId: number; kind: LocatorFileKind }) {
  await removeFile(payload.fileId, payload.kind)
}

function goProjectList() {
  router.push('/elements')
}

watch(projectCode, () => {
  loadTree()
})

onMounted(async () => {
  await loadTree()
})
</script>

<template>
  <div class="project-workspace">
    <WorkbenchHeader
      :title="pageTitle"
      subtitle="目录树 · 点击文件进入详情查看元素"
      icon="crosshair"
      :icon-gradient="'linear-gradient(135deg,var(--c-element),#c4b5fd)'"
    >
      <template #actions>
        <el-button class="wb-btn" @click="goProjectList">← 返回项目列表</el-button>
      </template>
    </WorkbenchHeader>

    <ErrorState v-if="treeError && !tree.length" :message="treeError" @retry="loadTree" />

    <div v-else class="project-workspace__main">
      <LocatorTree
        :tree-data="tree"
        :active-file-id="null"
        :project-code="projectCode"
        @select-file="selectFile"
        @create-directory="onCreateDirectory"
        @rename-directory="onRenameDirectory"
        @delete-directory="onDeleteDirectory"
        @create-file="onCreateFile"
        @delete-file="onDeleteFile"
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
  flex: 1 1 0;
  min-height: 0;
  width: 100%;
  overflow: hidden;
  border-top: 2px solid var(--app-border-light);
  background-color: var(--paper);
  background-image: radial-gradient(circle, var(--dot) 0.6px, transparent 0.6px);
  background-size: 15px 15px;
}
</style>
