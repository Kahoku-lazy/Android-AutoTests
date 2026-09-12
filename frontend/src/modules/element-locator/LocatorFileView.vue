<script setup lang="ts">
/**
 * 文件详情页：从目录树点进后全屏查看/编辑。
 * Android 页面 → 元素表；Web/API → 表单。
 */
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import WorkbenchHeader from '@/shared/components/WorkbenchHeader.vue'
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
  <div class="file-view">
    <WorkbenchHeader
      :title="headerTitle"
      :subtitle="headerSubtitle"
      icon="crosshair"
      :icon-gradient="'linear-gradient(135deg,var(--c-element),#c4b5fd)'"
    >
      <template #actions>
        <el-button class="wb-btn" @click="goBackToTree">← 返回目录</el-button>
      </template>
    </WorkbenchHeader>

    <div v-if="loading" class="file-view__body">
      <el-skeleton :rows="6" animated />
    </div>
    <ErrorState v-else-if="error" :message="error" @retry="loadFileMeta" />
    <div v-else-if="file" class="file-view__body">
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
.file-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}
.file-view__body {
  flex: 1 1 0;
  min-height: 0;
  overflow: hidden;
  border-top: 2px solid var(--app-border-light);
  background-color: var(--paper);
  background-image: radial-gradient(circle, var(--dot) 0.6px, transparent 0.6px);
  background-size: 15px 15px;
}
</style>
