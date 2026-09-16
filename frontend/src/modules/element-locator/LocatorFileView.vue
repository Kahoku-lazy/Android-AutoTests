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
import LocatorFilePanel from './components/LocatorFilePanel.vue'
import { useLocatorTree } from './composables/useLocatorTree'
import { getLocatorProjectTree } from './api'
import { formatApiError } from '@/shared/api-client'
import {
  FILE_KIND_BY_CODE,
  isLocatorProjectCode,
  type LocatorFileKind,
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

async function onDeleteFile(payload: { fileId: number; kind: LocatorFileKind }) {
  const ok = await removeFile(payload.fileId, payload.kind)
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
  <div class="doc-page doc-page--fixed wb-shell file-view">
    <WorkbenchHeader
      :title="headerTitle"
      :subtitle="headerSubtitle"
      icon="crosshair"
      :icon-gradient="'linear-gradient(135deg,var(--c-element),var(--locator-header-icon-end))'"
    >
      <template #nav>
        <WorkbenchCrumbs
          :back-to="`/elements/projects/${projectCode}`"
          back-label="返回目录"
          :items="[
            { label: '元素定位', to: '/elements' },
            { label: projectName || projectCode, to: `/elements/projects/${projectCode}` },
            { label: headerTitle },
          ]"
        />
      </template>
    </WorkbenchHeader>

    <div v-if="loading" class="doc-body">
      <el-skeleton :rows="6" animated />
    </div>
    <ErrorState v-else-if="error" :message="error" @retry="loadFileMeta" />
    <div v-else-if="file" class="doc-body">
      <LocatorFilePanel
        :key="`${file.kind}-${file.id}`"
        :file="file"
        hide-identity
        @delete-file="onDeleteFile"
        @back="goBackToTree"
      />
    </div>
  </div>
</template>

<style scoped>
/* 页面根/主体骨架由 .doc-page / .doc-body 提供；本页主体自带分隔线（纸面纯色，禁自绘点阵） */
/* 页头图标渐变末端色：tokens.css 未登记 #c4b5fd，登记在本页根作用域，随根元素继承给页头图标块 */
.file-view {
  --locator-header-icon-end: var(--color-indigo-84) /* -> --color-indigo-84 */;
}
.file-view .doc-body {
  overflow: hidden;
  border-top: 2px solid var(--app-border-light);
  background-color: var(--paper);
}
</style>
