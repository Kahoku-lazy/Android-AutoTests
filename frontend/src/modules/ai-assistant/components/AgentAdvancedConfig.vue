<script setup lang="ts">
defineProps<{ form: Record<string, unknown>; isNew?: boolean }>()
</script>

<template>
  <div class="doc-section step-panel">
    <div class="section-title">
      <span class="section-num">5</span>
      <span>高级设置</span>
    </div>
    <el-form label-width="120px" class="agent-form">
      <el-form-item>
        <template #label>
          <span class="label-with-help">TTS 语音 <el-tooltip content="将 AI 回复转为语音输出。需要模型支持 TTS 功能。" placement="top" effect="dark"><span class="help-icon">?</span></el-tooltip></span>
        </template>
        <el-switch v-model="form.tts_enabled" />
        <span class="form-hint">启用文本转语音输出</span>
      </el-form-item>
    </el-form>

    <el-divider>内存压缩 (CompressionConfig)</el-divider>
    <el-form label-width="120px" class="agent-form">
      <el-form-item>
        <template #label>
          <span class="label-with-help">启用压缩 <el-tooltip content="对话历史过长时自动压缩，将早期消息替换为摘要，避免超出模型上下文窗口。" placement="top" effect="dark"><span class="help-icon">?</span></el-tooltip></span>
        </template>
        <el-switch v-model="form.compression_enabled" />
        <span class="form-hint">对话过长时自动压缩历史</span>
      </el-form-item>
      <template v-if="form.compression_enabled">
        <el-form-item>
          <template #label>
            <span class="label-with-help">触发阈值 <el-tooltip content="对话总 token 数超过此值时触发压缩。值越低压缩越频繁。" placement="top" effect="dark"><span class="help-icon">?</span></el-tooltip></span>
          </template>
          <el-input-number v-model="form.compression_threshold" :min="1000" :max="100000" :step="1000" />
          <span class="form-hint">tokens</span>
        </el-form-item>
        <el-form-item>
          <template #label>
            <span class="label-with-help">保留最近 <el-tooltip content="压缩时保留最近 N 条消息不被压缩。值越大上下文越完整但 token 消耗越多。" placement="top" effect="dark"><span class="help-icon">?</span></el-tooltip></span>
          </template>
          <el-input-number v-model="form.compression_keep_recent" :min="1" :max="50" />
          <span class="form-hint">条消息</span>
        </el-form-item>
        <el-form-item>
          <template #label>
            <span class="label-with-help">压缩提示词 <el-tooltip content="指导模型如何压缩历史的提示词。如'用一句话摘要以下对话'。" placement="top" effect="dark"><span class="help-icon">?</span></el-tooltip></span>
          </template>
          <el-input v-model="form.compression_prompt" type="textarea" :rows="2" placeholder="Summarize the conversation..." />
        </el-form-item>
        <el-form-item>
          <template #label>
            <span class="label-with-help">摘要模板 <el-tooltip content="压缩后摘要的存储格式模板。{summary} 会被替换为实际摘要。" placement="top" effect="dark"><span class="help-icon">?</span></el-tooltip></span>
          </template>
          <el-input v-model="form.compression_template" type="textarea" :rows="2" placeholder="Previous summary: {summary}" />
        </el-form-item>
      </template>
    </el-form>
  </div>
</template>

<style scoped>
.form-hint { font-size: var(--app-size-sm); color: var(--ai-ink-muted); margin-left: 10px; }
.label-with-help { display: inline-flex; align-items: center; gap: 4px; }
.help-icon {
  display: inline-flex; align-items: center; justify-content: center;
  width: 16px; height: 16px; border-radius: 50%;
  background: var(--ai-ink-muted); color: #fff;
  font-size: 11px; font-weight: 700; cursor: help;
  opacity: 0.5; transition: opacity 0.15s;
}
.help-icon:hover { opacity: 1; background: var(--app-accent-purple, #b39ef3); }
</style>
