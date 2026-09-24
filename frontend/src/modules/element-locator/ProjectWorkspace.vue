<script setup lang="ts">
/**
 * 项目目录工作台：左栏目录树 + 右栏当前页面元素（宽屏并置，点页面不再整页跳走）。
 * 窄屏（<1280px）退化为既有两页流程：点页面跳文件详情路由 `/files/:fileId`。
 * 目录与文件的增删改只在本工作台；元素行的增删改在右栏面板内（与详情页同一组件）。
 */
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue"
import { useRoute, useRouter } from "vue-router"
import WorkbenchHeader from "@/shared/components/WorkbenchHeader.vue"
import WorkbenchCrumbs from "@/shared/components/WorkbenchCrumbs.vue"
import EmptyState from "@/shared/components/patterns/EmptyState.vue"
import ErrorState from "@/shared/components/patterns/ErrorState.vue"
import SkeletonCard from "@/shared/components/patterns/SkeletonCard.vue"
import LocatorTree from "./components/LocatorTree.vue"
import LocatorPagePreview from "./components/LocatorPagePreview.vue"
import SplitHandle from "@/shared/components/SplitHandle.vue"
import { useLocatorTree } from "./composables/useLocatorTree"
import type { LocatorFileNode, LocatorTreeNode } from "./types"

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

// ── 宽屏阈值：≥1280px 并置；以下退化为两页流程 ──
const WIDE_QUERY = "(min-width: 1280px)"
const isWide = ref(true)
/** 宽屏下的右栏选中页面；窄屏不使用（走路由跳转） */
const selectedFileId = ref<number | null>(null)
let media: MediaQueryList | null = null

// ── 左栏宽度：可拖动 + 记忆（初值取 T0 分栏档位，单一真相源在 tokens.css）──
const SPLIT_KEY = "app-split-locator-tree-w"
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

const pageTitle = computed(() => project.value?.name || "元素项目")

/** 页头概况：目录数与页面数由目录树统计（不改接口） */
function flatten(nodes: LocatorTreeNode[]): LocatorTreeNode[] {
  return nodes.flatMap((node) => [
    node,
    ...(node.type === "directory" && node.children ? flatten(node.children) : []),
  ])
}
const counts = computed(() => {
  const all = flatten(tree.value)
  return {
    directories: all.filter((n) => n.type === "directory").length,
    pages: all.filter((n) => n.type === "file").length,
  }
})
const headerSubtitle = computed(() =>
  tree.value.length
    ? `${counts.value.directories} 个目录 · ${counts.value.pages} 个页面`
    : "目录树 · 点击页面在右侧查看元素",
)

function findFile(nodes: LocatorTreeNode[], id: number): LocatorFileNode | null {
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
    { label: "元素定位", to: "/elements" },
    { label: pageTitle.value },
  ]
  // 右栏选中页面时，面包屑末项即当前页面（不可点）
  if (selectedFile.value) items.push({ label: selectedFile.value.name })
  return items
})

async function selectFile(id: number) {
  if (!isWide.value) {
    await router.push(`/elements/projects/${projectCode.value}/files/${id}`)
    return
  }
  selectedFileId.value = id
}

/** 右栏只做预览：编辑一律进文件详情页 */
async function openFilePage(id: number) {
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
  const ok = await removeFile(payload.fileId)
  if (ok && selectedFileId.value === payload.fileId) selectedFileId.value = null
}

watch(projectCode, () => {
  selectedFileId.value = null
  loadTree()
})

onMounted(async () => {
  media = window.matchMedia(WIDE_QUERY)
  isWide.value = media.matches
  media.addEventListener("change", onMediaChange)
  // 宽度：先读 CSS 令牌（= T0 档位），再用记忆值覆盖
  const tokenValue = splitRef.value
    ? Number.parseFloat(
        getComputedStyle(splitRef.value).getPropertyValue("--locator-tree-pane-w"),
      )
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
  <div class="doc-page doc-page--fixed wb-shell locator-workbench locator-project-workspace">
    <WorkbenchHeader
      :title="pageTitle"
      :subtitle="headerSubtitle"
      icon="crosshair"
      :icon-gradient="'linear-gradient(135deg,var(--c-element),var(--locator-header-icon-end))'"
    />

    <div class="doc-body">
      <WorkbenchCrumbs
        back-to="/elements"
        back-label="返回项目列表"
        :items="crumbItems"
      />
      <div class="locator-workspace-main">
        <SkeletonCard v-if="loading" variant="list" :lines="6" />
        <ErrorState v-else-if="treeError && !tree.length" :message="treeError" @retry="loadTree" />
        <div
          v-else
          ref="splitRef"
          class="locator-split"
          :class="{ 'locator-split--single': !isWide }"
          :style="{ '--locator-tree-pane-w': `${paneWidth}px` }"
        >
          <div class="locator-tree-pane">
            <LocatorTree
              :tree-data="tree"
              :active-file-id="selectedFileId"
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

          <SplitHandle
            v-if="isWide"
            v-model="paneWidth"
            :default-width="PANE_FALLBACK"
            label="调整目录树宽度"
            @commit="onSplitCommit"
          />

          <div v-if="isWide" class="locator-detail-pane element-detail-pane">
            <template v-if="selectedFile">
              <LocatorPagePreview
                :key="selectedFile.id"
                :file="selectedFile"
                @open="openFilePage"
              />
            </template>
            <EmptyState
              v-else
              icon="🖱"
              text="从左侧选择一个页面"
              hint="点目录树里的页面，这里显示元素只读预览；编辑请进入页面"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<!-- 硬边按键皮肤与表纸线型：与文件详情页共用同一份（components/elementDetailSkin.css） -->
<style scoped src="./components/elementDetailSkin.css"></style>

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
/* 分栏台：左栏固定档位宽度（可拖动调整）+ 分隔手柄 + 右栏元素内容 */
.locator-split {
  flex: 1 1 0;
  min-height: 0;
  display: grid;
  grid-template-columns: var(--locator-tree-pane-w) auto minmax(0, 1fr);
}
.locator-split--single {
  grid-template-columns: minmax(0, 1fr);
}
.locator-tree-pane {
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
}
.locator-detail-pane {
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
/* 未选中页面时引导空态居中 */
.locator-detail-pane :deep(.empty-state) {
  margin: auto;
}
</style>
