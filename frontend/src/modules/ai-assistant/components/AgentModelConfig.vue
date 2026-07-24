<script setup>
defineProps({
  form: { type: Object, required: true },
  isNew: { type: Boolean, default: false },
  providers: { type: Array, default: () => [] },
  availableModels: { type: Array, default: () => [] },
  detectedModels: { type: Array, default: () => [] },
  detectingModels: { type: Boolean, default: false },
})

const emit = defineEmits(['provider-change', 'detect-models'])
</script>

<template>
  <div v-if="!isNew || step === 2" class="doc-section step-panel">
    <div class="section-title">
      <span class="section-num">2</span>
      <span>模型配置</span>
    </div>
    <el-form label-width="110px" class="agent-form">
      <el-form-item label="模型服务">
        <el-select v-model="form.model_provider" @change="emit('provider-change')" style="width:100%">
          <el-option v-for="p in providers" :key="p.value" :label="p.label" :value="p.value" />
        </el-select>
      </el-form-item>
      <el-form-item label="模型名称">
        <el-select v-if="form.model_provider !== 'custom'" v-model="form.model_name"
          style="width:100%" allow-create filterable>
          <el-option v-for="m in availableModels" :key="m" :label="m" :value="m" />
        </el-select>
        <el-input v-else v-model="form.model_name" placeholder="输入模型名称" />
        <div v-if="detectedModels.length" class="form-hint" style="margin-top:4px">
          已检测模型: {{ detectedModels.length }} 个
        </div>
      </el-form-item>
      <el-form-item label="API Key">
        <el-input v-model="form.api_key" type="password" show-password placeholder="sk-..." />
        <el-button :loading="detectingModels" @click="emit('detect-models')" style="margin-left:8px" size="default">
          {{ detectingModels ? '检测中...' : '🔍 检测模型' }}
        </el-button>
      </el-form-item>
      <el-form-item v-if="form.model_provider === 'custom'" label="API 地址">
        <el-input v-model="form.base_url" placeholder="https://api.example.com/v1" />
      </el-form-item>
      <el-form-item label="温度">
        <el-slider v-model="form.temperature" :min="0" :max="2" :step="0.1" show-input />
      </el-form-item>
      <el-form-item label="最大Token">
        <el-input-number v-model="form.max_tokens" :min="256" :max="128000" :step="256" />
      </el-form-item>
      <el-form-item label="Formatter">
        <el-select v-model="form.formatter" style="width:100%">
          <el-option value="dashscope" label="DashScope (Qwen)" />
          <el-option value="openai" label="OpenAI (GPT)" />
          <el-option value="anthropic" label="Anthropic (Claude)" />
        </el-select>
      </el-form-item>
      <el-form-item label="生成参数">
        <el-input v-model="form.generate_kwargs" type="textarea" :rows="2" placeholder='{"parallel_tool_calls":true}' />
      </el-form-item>
    </el-form>
  </div>
</template>

<style scoped>
.form-hint { font-size: var(--app-size-sm); color: #a0936e; margin-left: 10px; }
</style>
