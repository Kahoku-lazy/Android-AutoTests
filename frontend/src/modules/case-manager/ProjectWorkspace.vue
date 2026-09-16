<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import WorkbenchHeader from '@/shared/components/WorkbenchHeader.vue'
import WorkbenchCrumbs from '@/shared/components/WorkbenchCrumbs.vue'
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

onMounted(async () => {
  await loadTree()
})
</script>

<template>
  <div class="doc-page doc-page--fixed wb-shell case-workbench project-workspace">
    <WorkbenchHeader
      :title="pageTitle"
      subtitle="目录与文件 · 点文件进入表格编辑"
      icon="layers"
      :icon-gradient="'linear-gradient(135deg,var(--c-case),var(--case-icon-accent))'"
    >
      <template #nav>
        <WorkbenchCrumbs
          back-to="/cases"
          back-label="返回项目列表"
          :items="[
            { label: '用例管理', to: '/cases' },
            { label: pageTitle },
          ]"
        />
      </template>
    </WorkbenchHeader>

    <ErrorState v-if="treeError && !tree.length" :message="treeError" @retry="refreshTree" />

    <div v-else class="doc-body">
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
/* 模块作用域色板：登记本页用到的非全局色值（消费点都在页面根之内；页面根即组件根） */
.case-workbench {
  --case-icon-accent: var(--color-teal-67) /* -> --color-teal-67 */;  /* 页头图标渐变收尾色（与 --c-case 组成模块标识渐变） */
}

/* 页面根/主体骨架由 .doc-page / .doc-body 提供；本页主体自带分隔线（纸面纯色，禁自绘点阵） */
.project-workspace .doc-body {
  width: 100%;
  border-top: 2px solid var(--case-border-subtle);
  background-color: var(--paper);
  overflow: hidden;
}
</style>
