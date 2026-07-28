<script setup>
defineProps({
  form: { type: Object, required: true },
  isNew: { type: Boolean, default: false },
})
</script>

<template>
  <div v-if="!isNew || step === 3" class="doc-section step-panel">
    <div class="section-title">
      <span class="section-num">3</span>
      <span>提示词</span>
    </div>
    <el-form label-width="120px" class="agent-form">
      <el-form-item label="系统提示词">
        <div style="display:flex;flex-direction:column;gap:8px;width:100%">
          <el-button size="small" @click="$emit('load-default-prompt')" style="align-self:flex-start">
            📋 加载默认模板
          </el-button>
          <el-input v-model="form.system_prompt" type="textarea" :rows="10"
            placeholder="你是一个专业的测试用例编写助手，擅长..." />
        </div>
      </el-form-item>
      <el-form-item label="最大迭代次数">
        <el-input-number v-model="form.max_iters" :min="1" :max="100" />
      </el-form-item>
      <el-form-item label="并行工具调用">
        <el-switch v-model="form.parallel_tool_calls" />
        <span class="form-hint">允许智能体同时调用多个工具</span>
      </el-form-item>
      <el-form-item label="打印提示消息">
        <el-switch v-model="form.print_hint_msg" />
        <span class="form-hint">在控制台输出运行时提示</span>
      </el-form-item>
    </el-form>
  </div>
</template>

<style scoped>
.form-hint { font-size: var(--app-size-sm); color: var(--ai-ink-muted); margin-left: 10px; }
</style>
