<script setup lang="ts">
/**
 * 用例项目工作台：左栏目录树 + 右栏当前文件的用例只读预览（宽屏并置，点文件不再整页跳走）。
 * 窄屏（<1280px）退化为既有两页流程：点文件跳详情路由 `/files/:fileId`。
 * 目录与文件的增删改只在本工作台；用例行的增删改在详情页（CaseFileSheet）。
 */
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue"
import { useRoute, useRouter } from "vue-router"
import WorkbenchHeader from "@/shared/components/WorkbenchHeader.vue"
import WorkbenchCrumbs from "@/shared/components/WorkbenchCrumbs.vue"
import EmptyState from "@/shared/components/patterns/EmptyState.vue"
import ErrorState from "@/shared/components/patterns/ErrorState.vue"
import SkeletonCard from "@/shared/components/patterns/SkeletonCard.vue"
import ProjectTree from "./components/ProjectTree.vue"
import CasePagePreview from "./components/CasePagePreview.vue"
import SplitHandle from "@/shared/components/SplitHandle.vue"
import { useProjectTree } from "./composables/useProjectTree"
import type { TreeFileNode, TreeNode } from "./types"

const route = useRoute()
const router = useRouter()

const projectId = computed(() => Number(route.params.projectId))

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
  renameFile,
  removeFile,
  moveTreeItem,
} = useProjectTree(() => projectId.value)

// ── 宽屏阈值：≥1280px 并置；以下退化为两页流程 ──
const WIDE_QUERY = "(min-width: 1280px)"
const isWide = ref(true)
/** 宽屏下的右栏选中文件；窄屏不使用（走路由跳转） */
const selectedFileId = ref<number | null>(null)
let media: MediaQueryList | null = null

// ── 左栏宽度：可拖动 + 记忆（初值取 T0 分栏档位，单一真相源在 tokens.css）──
const SPLIT_KEY = "app-split-case-tree-w"
const PANE_FALLBACK = 280
const splitRef = ref<HTMLElement | null>(null)
const paneWidth = ref(PANE_FALLBACK)

function onSplitCommit(width: number) {
  paneWidth.value = width
  localStorage.setItem(SPLIT_KEY, String(width))
}

function onMediaChange(event: MediaQueryListEvent) {
  isWide.value = event.matches
  if (!event.matches) selectedFileId.value = null
}

const pageTitle = computed(() => project.value?.name || "项目工作台")

/** 页头概况：目录数与文件数由目录树统计（不改接口） */
function flatten(nodes: TreeNode[]): TreeNode[] {
  return nodes.flatMap((node) => [
    node,
    ...(node.type === "directory" && node.children ? flatten(node.children) : []),
  ])
}
const counts = computed(() => {
  const all = flatten(tree.value)
  return {
    directories: all.filter((n) => n.type === "directory").length,
    files: all.filter((n) => n.type === "file").length,
  }
})
const headerSubtitle = computed(() =>
  tree.value.length
    ? `${counts.value.directories} 个目录 · ${counts.value.files} 个文件`
    : "目录与文件 · 点文件在右侧预览用例",
)

function findFile(nodes: TreeNode[], id: number): TreeFileNode | null {
  for (const node of nodes) {
    if (node.type === "file" && node.id === id) return node
    if (node.type === "directory" && node.children?.length) {
      const found = findFile(node.children, id)
      if (found) return found
    }
  }
  return null
}

const selectedFile = computed(() =>
  selectedFileId.value == null ? null : findFile(tree.value, selectedFileId.value),
)

const crumbItems = computed(() => {
  const items: Array<{ label: string; to?: string }> = [
    { label: "用例管理", to: "/cases" },
    { label: pageTitle.value },
  ]
  // 右栏选中文件时，面包屑末项即当前文件（不可点）
  if (selectedFile.value) items.push({ label: selectedFile.value.name })
  return items
})

async function selectFile(id: number) {
  if (!isWide.value) {
    await router.push(`/cases/projects/${projectId.value}/files/${id}`)
    return
  }
  selectedFileId.value = id
}

/** 右栏只做预览：编辑一律进文件详情页 */
async function openFilePage(id: number) {
  await router.push(`/cases/projects/${projectId.value}/files/${id}`)
}

async function refreshTree() {
  await loadTree()
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
  const ok = await removeFile(fileId)
  if (ok && selectedFileId.value === fileId) selectedFileId.value = null
}

async function onMoveItem(payload: {
  itemType: "directory" | "file"
  itemId: number
  targetDirectoryId: number | null
}) {
  await moveTreeItem(payload.itemType, payload.itemId, payload.targetDirectoryId)
}

watch(projectId, () => {
  selectedFileId.value = null
  loadTree()
})

onMounted(async () => {
  media = window.matchMedia(WIDE_QUERY)
  isWide.value = media.matches
  media.addEventListener("change", onMediaChange)
  // 宽度：先读 CSS 令牌（= T0 档位），再用记忆值覆盖
  const tokenValue = splitRef.value
    ? Number.parseFloat(getComputedStyle(splitRef.value).getPropertyValue("--case-tree-pane-w"))
    : Number.NaN
  if (Number.isFinite(tokenValue) && tokenValue > 0) paneWidth.value = tokenValue
  const saved = Number(localStorage.getItem(SPLIT_KEY))
  if (Number.isFinite(saved) && saved > 0) paneWidth.value = saved
  await loadTree()
})

onBeforeUnmount(() => {
  media?.removeEventListener("change", onMediaChange)
  media = null
})
</script>

<template>
  <div class="doc-page doc-page--fixed wb-shell case-workbench project-workspace">
    <WorkbenchHeader
      :title="pageTitle"
      :subtitle="headerSubtitle"
      icon="layers"
      :icon-gradient="'linear-gradient(135deg,var(--c-case),var(--case-icon-accent))'"
    />

    <div class="doc-body">
      <WorkbenchCrumbs
        back-to="/cases"
        back-label="返回项目列表"
        :items="crumbItems"
      />
      <div class="case-workspace-main">
        <SkeletonCard v-if="loading" variant="list" :lines="6" />
        <ErrorState v-else-if="treeError && !tree.length" :message="treeError" @retry="refreshTree" />
        <div
          v-else
          ref="splitRef"
          class="case-split"
          :class="{ 'case-split--single': !isWide }"
          :style="{ '--case-tree-pane-w': `${paneWidth}px` }"
        >
          <div class="case-tree-pane">
            <ProjectTree
              :tree-data="tree"
              :active-file-id="selectedFileId"
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

          <SplitHandle
            v-if="isWide"
            v-model="paneWidth"
            :default-width="PANE_FALLBACK"
            label="调整目录树宽度"
            @commit="onSplitCommit"
          />

          <div v-if="isWide" class="case-preview-pane">
            <template v-if="selectedFile">
              <CasePagePreview :key="selectedFile.id" :file="selectedFile" @open="openFilePage" />
            </template>
            <EmptyState
              v-else
              icon="🖱"
              text="从左侧选择一个文件"
              hint="点目录树里的用例文件，这里显示用例只读预览；编辑请进入页面"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 页面根/主体骨架由 .doc-page / .doc-body 提供；本页主体自带分隔线（纸面由 L0 透出，禁自绘点阵） */
.project-workspace .doc-body {
  width: 100%;
  border-top: 2px solid var(--case-border-subtle);
  overflow: hidden;
}
.project-workspace .doc-body > :first-child {
  flex-shrink: 0;
}
.case-workspace-main {
  flex: 1 1 0;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
/* 分栏台：左栏固定档位宽度（可拖动调整）+ 分隔手柄 + 右栏只读预览 */
.case-split {
  flex: 1 1 0;
  min-height: 0;
  display: grid;
  grid-template-columns: var(--case-tree-pane-w) auto minmax(0, 1fr);
}
.case-split--single {
  grid-template-columns: minmax(0, 1fr);
}
.case-tree-pane {
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
}
.case-preview-pane {
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
/* 未选中文件时引导空态居中 */
.case-preview-pane :deep(.empty-state) {
  margin: auto;
}
</style>
