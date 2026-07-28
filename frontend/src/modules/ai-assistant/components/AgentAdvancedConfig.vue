<script setup>
defineProps({
  form: { type: Object, required: true },
  isNew: { type: Boolean, default: false },
})
</script>

<template>
  <div v-if="!isNew || step === 5" class="doc-section step-panel">
    <div class="section-title">
      <span class="section-num">5</span>
      <span>高级设置</span>
    </div>
    <el-form label-width="120px" class="agent-form">
      <el-form-item label="TTS 语音">
        <el-switch v-model="form.tts_enabled" />
        <span class="form-hint">启用文本转语音输出</span>
      </el-form-item>
    </el-form>

    <el-divider>内存压缩 (CompressionConfig)</el-divider>
    <el-form label-width="120px" class="agent-form">
      <el-form-item label="启用压缩">
        <el-switch v-model="form.compression_enabled" />
        <span class="form-hint">对话过长时自动压缩历史</span>
      </el-form-item>
      <template v-if="form.compression_enabled">
        <el-form-item label="触发阈值">
          <el-input-number v-model="form.compression_threshold" :min="1000" :max="100000" :step="1000" />
          <span class="form-hint">tokens</span>
        </el-form-item>
        <el-form-item label="保留最近">
          <el-input-number v-model="form.compression_keep_recent" :min="1" :max="50" />
          <span class="form-hint">条消息</span>
        </el-form-item>
        <el-form-item label="压缩提示词">
          <el-input v-model="form.compression_prompt" type="textarea" :rows="2" placeholder="Summarize the conversation..." />
        </el-form-item>
        <el-form-item label="摘要模板">
          <el-input v-model="form.compression_template" type="textarea" :rows="2" placeholder="Previous summary: {summary}" />
        </el-form-item>
      </template>
    </el-form>
  </div>
</template>

<style scoped>
.form-hint { font-size: var(--app-size-sm); color: var(--ai-ink-muted); margin-left: 10px; }
</style>
