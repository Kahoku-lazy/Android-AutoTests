<script setup lang="ts">
/**
 * 项目目录工作台：只负责目录树。
 * 点击文件后路由跳转到独立详情页查看/编辑元素（对齐用例管理）。
 */
import { computed, onMounted, watch } from "vue"
import { useRoute, useRouter } from "vue-router"
import WorkbenchHeader from "@/shared/components/WorkbenchHeader.vue"
import WorkbenchCrumbs from "@/shared/components/WorkbenchCrumbs.vue"
import ErrorState from "@/shared/components/patterns/ErrorState.vue"
import SkeletonCard from "@/shared/components/patterns/SkeletonCard.vue"
import LocatorTree from "./components/LocatorTree.vue"
import { useLocatorTree } from "./composables/useLocatorTree"

const route = useRoute()
const router = useRouter()

const projectCode = computed(() => String(route.params.code || ""))

const {
  project,
  tree,
  loading,
  error: treeError,
  loadTree,
  addDirectory,
  renameDirectory,
  removeDirectory,
  addFile,
  removeFile,
  moveItems,
  deleteItems,
} = useLocatorTree(() => projectCode.value)

const pageTitle = computed(() => project.value?.name || "元素项目")

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

async function onDeleteFile(payload: { fileId: number }) {
  await removeFile(payload.fileId)
}

watch(projectCode, () => {
  loadTree()
})

onMounted(async () => {
  await loadTree()
})
</script>

<template>
  <div class="doc-page doc-page--fixed wb-shell locator-workbench locator-project-workspace">
    <WorkbenchHeader
      :title="pageTitle"
      subtitle="目录树 · 点击文件进入详情查看元素"
      icon="crosshair"
      :icon-gradient="'linear-gradient(135deg,var(--c-element),var(--locator-header-icon-end))'"
    />

    <div class="doc-body">
      <WorkbenchCrumbs
        back-to="/elements"
        back-label="返回项目列表"
        :items="[{ label: '元素定位', to: '/elements' }, { label: pageTitle }]"
      />
      <div class="locator-workspace-main">
        <SkeletonCard v-if="loading" variant="list" :lines="6" />
        <ErrorState v-else-if="treeError && !tree.length" :message="treeError" @retry="loadTree" />
        <LocatorTree
          v-else
          :tree-data="tree"
          :active-file-id="null"
          :move-items="moveItems"
          :delete-items="deleteItems"
          @select-file="selectFile"
          @create-directory="onCreateDirectory"
          @rename-directory="onRenameDirectory"
          @delete-directory="onDeleteDirectory"
          @create-file="onCreateFile"
          @delete-file="onDeleteFile"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 页面根/主体骨架由 .doc-page / .doc-body 提供；本页主体自带分隔线（纸面由 L0 透出，禁自绘点阵） */
.locator-project-workspace .doc-body {
  width: 100%;
  overflow: hidden;
  border-top: 2px solid var(--app-border-light);
}
.locator-project-workspace .doc-body > :first-child {
  flex-shrink: 0;
}
.locator-workspace-main {
  flex: 1 1 0;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
</style>
