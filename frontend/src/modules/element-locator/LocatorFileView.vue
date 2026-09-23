<script setup lang="ts">
/**
 * 文件详情页：从目录树点进后全屏查看/编辑。
 * Android 页面 → 元素表；Web/API → 表单。
 */
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import WorkbenchHeader from '@/shared/components/WorkbenchHeader.vue'
import WorkbenchCrumbs from '@/shared/components/WorkbenchCrumbs.vue'
import ErrorState from '@/shared/components/patterns/ErrorState.vue'
import SkeletonCard from '@/shared/components/patterns/SkeletonCard.vue'
import LocatorFilePanel from './components/LocatorFilePanel.vue'
import { useLocatorTree } from './composables/useLocatorTree'
import { getLocatorProjectTree } from './api'
import { formatApiError } from '@/shared/api-client'
import {
  FILE_KIND_BY_CODE,
  isLocatorProjectCode,
  type LocatorFileNode,
  type LocatorTreeNode,
} from './types'

const route = useRoute()
const router = useRouter()

const projectCode = computed(() => String(route.params.code || ''))
const fileId = computed(() => {
  const raw = Number(route.params.fileId)
  return Number.isFinite(raw) && raw > 0 ? raw : null
})

const { removeFile } = useLocatorTree(() => projectCode.value)

const loading = ref(false)
const error = ref('')
const projectName = ref('')
const file = ref<LocatorFileNode | null>(null)

function findFile(nodes: LocatorTreeNode[], id: number): LocatorFileNode | null {
  for (const node of nodes) {
    if (node.type === 'file' && node.id === id) return node
    if (node.type === 'directory' && node.children?.length) {
      const found = findFile(node.children, id)
      if (found) return found
    }
  }
  return null
}

async function loadFileMeta() {
  if (fileId.value == null || !isLocatorProjectCode(projectCode.value)) {
    error.value = '无效的文件地址'
    file.value = null
    return
  }
  loading.value = true
  error.value = ''
  try {
    const { data } = await getLocatorProjectTree(projectCode.value)
    if (!data.status || !data.data) {
      error.value = data.message || '加载失败'
      file.value = null
      return
    }
    projectName.value = data.data.project?.name || projectCode.value
    const found = findFile(data.data.tree || [], fileId.value)
    if (found) {
      file.value = found
    } else {
      // 树里暂时找不到时，用项目默认 kind 兜底，面板仍可按 id 拉详情
      file.value = {
        type: 'file',
        id: fileId.value,
        name: `文件 #${fileId.value}`,
        kind: FILE_KIND_BY_CODE[projectCode.value],
        sort_order: 0,
      }
    }
  } catch (e: unknown) {
    error.value = formatApiError(e as never, '加载失败')
    file.value = null
  } finally {
    loading.value = false
  }
}

async function goBackToTree() {
  await router.push(`/elements/projects/${projectCode.value}`)
}

async function onDeleteFile(payload: { fileId: number }) {
  const ok = await removeFile(payload.fileId)
  if (ok) await goBackToTree()
}

const headerTitle = computed(() => file.value?.name || '文件详情')
const headerSubtitle = computed(() =>
  projectName.value ? `${projectName.value} · 元素详情` : '元素详情',
)

watch(
  () => [projectCode.value, fileId.value] as const,
  () => {
    loadFileMeta()
  },
)

onMounted(() => {
  loadFileMeta()
})
</script>

<template>
  <div class="doc-page doc-page--fixed wb-shell locator-workbench file-view">
    <WorkbenchHeader
      :title="headerTitle"
      :subtitle="headerSubtitle"
      icon="crosshair"
      :icon-gradient="'linear-gradient(135deg,var(--c-element),var(--locator-header-icon-end))'"
    />

    <div class="doc-body">
      <WorkbenchCrumbs
        :back-to="`/elements/projects/${projectCode}`"
        back-label="返回目录"
        :items="[
          { label: '元素定位', to: '/elements' },
          { label: projectName || projectCode, to: `/elements/projects/${projectCode}` },
          { label: headerTitle },
        ]"
      />
      <div class="file-view-main">
        <SkeletonCard v-if="loading" variant="list" :lines="6" />
        <ErrorState v-else-if="error" :message="error" @retry="loadFileMeta" />
        <LocatorFilePanel
          v-else-if="file"
          :key="`${file.kind}-${file.id}`"
          :file="file"
          hide-identity
          @delete-file="onDeleteFile"
          @back="goBackToTree"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 页面根/主体骨架由 .doc-page / .doc-body 提供；本页主体自带分隔线（纸面由 L0 透出，禁自绘点阵） */
.file-view .doc-body {
  overflow: hidden;
  border-top: 2px solid var(--app-border-light);
}
.file-view .doc-body > :first-child {
  flex-shrink: 0;
}
.file-view-main {
  flex: 1 1 0;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* ═══════════════════════════════════════════
   硬边按键皮肤（作用域：本页 .file-view）
   几何基准 = 侧栏「退出」与 .device-workbench / .inspector-workbench：
   2px 墨色实边 + 2px 近直角 + 2px 偏移硬阴影；hover 左上 1px、阴影增至 3px。
   共享件 DoodleBtn / FilterTabs / ErrorState 与全局主题不变。
   ═══════════════════════════════════════════ */
.file-view :deep(.el-button:not(.is-text):not(.is-link)) {
  border: 2px solid var(--ink) !important;
  border-radius: 2px !important;
  font-weight: 700 !important;
  box-shadow: 2px 2px 0 0 var(--ink) !important;
  transition:
    transform var(--app-duration-fast) var(--app-ease),
    box-shadow var(--app-duration-fast) var(--app-ease),
    background var(--app-duration-fast) var(--app-ease) !important;
}
.file-view :deep(.el-button:not(.is-text):not(.is-link):not(:disabled):hover) {
  transform: translate(-1px, -1px) !important;
  box-shadow: 3px 3px 0 0 var(--ink) !important;
}

/* 删除键：危险红底 + 浅色字（对齐 logout 几何，对比度 ≥ 4.5:1） */
.file-view :deep(.el-button--danger:not(.is-text):not(.is-link)) {
  background: var(--app-marker-red) !important;
  border-color: var(--ink) !important;
  color: var(--app-bg-card) !important;
}
.file-view :deep(.el-button--danger:not(.is-text):not(.is-link):not(:disabled):hover) {
  background: var(--app-marker-red) !important;
  border-color: var(--ink) !important;
  color: var(--app-bg-card) !important;
}

/* 表纸线型登记：实线；宽度与颜色仍取 --comp-sheet-border */
.file-view :deep(.sketch-sheet) {
  border-style: solid;
}
</style>
