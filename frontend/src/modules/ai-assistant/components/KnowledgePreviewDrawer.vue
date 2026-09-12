<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import ErrorState from '@/shared/components/patterns/ErrorState.vue'
import { previewKnowledgeDocument, type KnowledgePreviewPayload } from '../api/toolbox'
import { renderSkillMarkdown } from '../helpers/skill-markdown'

const props = defineProps<{
  path: string
}>()

const emit = defineEmits<{ close: [] }>()

const loading = ref(false)
const loadError = ref('')
const file = ref<KnowledgePreviewPayload | null>(null)

const markdownHtml = computed(() => {
  if (file.value?.kind !== 'markdown' || !file.value.content) return ''
  return renderSkillMarkdown(file.value.content)
})

async function loadPreview() {
  if (!props.path) return
  loading.value = true
  loadError.value = ''
  file.value = null
  try {
    const data = await previewKnowledgeDocument(props.path)
    if (data.status && data.data) file.value = data.data
    else loadError.value = data.message || '无法预览该文档'
  } catch {
    loadError.value = '无法预览该文档'
  } finally {
    loading.value = false
  }
}

watch(() => props.path, loadPreview, { immediate: true })
</script>

<template>
  <el-drawer
    :model-value="true"
    :title="file?.name || path"
    size="48%"
    @close="emit('close')"
  >
    <ErrorState v-if="loadError" :message="loadError" @retry="loadPreview" />
    <div v-else v-loading="loading" class="kb-preview-body">
      <p v-if="file?.converted" class="kb-preview-note">已转换为 Markdown 并保存在原文件旁</p>
      <article v-if="file?.kind === 'markdown'" class="kb-preview-md" v-html="markdownHtml" />
      <pre v-else-if="file?.kind === 'text'" class="kb-preview-text">{{ file.content }}</pre>
    </div>
  </el-drawer>
</template>

<style scoped>
.kb-preview-body { min-height: 200px; }
.kb-preview-note {
  margin: 0 0 12px;
  font-size: var(--app-size-xs);
  color: var(--app-ink-muted);
}
.kb-preview-md {
  font-size: var(--app-size-sm);
  line-height: 1.65;
  color: var(--ink);
}
.kb-preview-md :deep(h1),
.kb-preview-md :deep(h2),
.kb-preview-md :deep(h3) { margin: 0.8em 0 0.4em; }
.kb-preview-md :deep(p) { margin: 0.4em 0; }
.kb-preview-md :deep(pre) {
  overflow: auto;
  padding: 10px 12px;
  border-radius: 8px;
  background: rgba(121, 79, 39, 0.06);
}
.kb-preview-text {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: var(--app-size-sm);
  color: var(--ink);
}
</style>
