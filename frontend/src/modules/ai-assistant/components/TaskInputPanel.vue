<script setup lang="ts">
/**
 * 入模可观察性面板：送给规划模型的四键输入原文 + 附件解析正文。
 *
 * 数据来自任务详情接口（planner_input / attachment / attachment_filename），
 * 本组件只负责展示：两个默认收起的折叠区块，正文区块内部定高滚动。
 */
import EmptyState from "@/shared/components/patterns/EmptyState.vue"

defineProps<{
  /** 引擎实际交给规划模型的四键 JSON 原文 */
  plannerInput?: string
  /** 附件解析后的 Markdown 正文全文（无附件为空串） */
  attachment?: string
  /** 附件原始文件名 */
  attachmentFilename?: string
}>()
</script>

<template>
  <el-collapse class="ti-collapse">
    <el-collapse-item name="planner-input">
      <template #title>
        <span class="ti-title">送给规划模型的输入<span class="ti-tag">Planner Input</span></span>
      </template>
      <pre v-if="plannerInput" class="ti-pre">{{ plannerInput }}</pre>
      <p v-else class="ti-empty">本条任务没有规划输入记录</p>
    </el-collapse-item>

    <el-collapse-item name="attachment">
      <template #title>
        <span class="ti-title">任务附件<span class="ti-tag">Attachment</span></span>
      </template>
      <template v-if="attachment || attachmentFilename">
        <p v-if="attachmentFilename" class="ti-file">文件名：{{ attachmentFilename }}</p>
        <pre v-if="attachment" class="ti-pre">{{ attachment }}</pre>
        <p v-else class="ti-empty">该附件未解析出可用正文</p>
      </template>
      <EmptyState
        v-else
        icon="📎"
        text="未上传附件"
        hint="新建任务时可上传一份 Word / PDF，解析结果会随任务目标一起送进规划模型"
      />
    </el-collapse-item>
  </el-collapse>
</template>

<style scoped>
.ti-collapse {
  flex-shrink: 0;
  border: 2px solid var(--ink);
  border-radius: var(--app-radius-md);
  background: var(--app-bg-card);
  overflow: hidden;
}
.ti-collapse :deep(.el-collapse-item__header) {
  padding: 0 var(--app-space-md);
  font-size: var(--app-size-sm);
  font-weight: 800;
  color: var(--ink);
  background: var(--ai-sticky-bg);
  border-bottom: 1.5px dashed var(--ai-warm-border);
}
.ti-collapse :deep(.el-collapse-item__wrap) {
  background: var(--app-bg-card);
  border-bottom: none;
}
.ti-collapse :deep(.el-collapse-item__content) {
  padding: var(--app-space-md);
}
.ti-title {
  display: inline-flex;
  align-items: center;
  gap: var(--app-space-sm);
}
.ti-tag {
  padding: 1px var(--app-space-xs);
  font-size: var(--app-size-xs);
  font-weight: 700;
  color: var(--ai-ink-muted);
  border: 1.5px solid var(--ai-warm-border);
  border-radius: var(--el-border-radius-small);
}
.ti-pre {
  margin: 0;
  padding: var(--app-space-md);
  max-height: 240px;
  overflow: auto;
  background: var(--ai-sticky-bg);
  border: 1.5px dashed var(--ai-warm-border);
  border-radius: var(--app-radius-md);
  font-family: var(--app-font-mono);
  font-size: var(--app-size-xs);
  line-height: 1.6;
  color: var(--ai-ink-soft);
  white-space: pre-wrap;
  word-break: break-word;
}
.ti-file {
  margin: 0 0 var(--app-space-xs);
  font-size: var(--app-size-sm);
  font-weight: 700;
  color: var(--ink);
}
.ti-empty {
  margin: 0;
  font-size: var(--app-size-sm);
  color: var(--ai-ink-muted);
}
</style>
