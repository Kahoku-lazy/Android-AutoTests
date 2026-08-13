<script setup lang="ts">
defineProps<{
  form: Record<string, any>
  isNew?: boolean
  providers?: { label: string; value: string }[]
  availableModels?: string[]
  detectedModels?: string[]
  detectingModels?: boolean
}>()
const emit = defineEmits<{ 'provider-change': []; 'detect-models': [] }>()
</script>

<template>
  <div class="doc-section step-panel">
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
      <el-form-item>
        <template #label>
          <span class="label-with-help">温度 <el-tooltip content="控制输出随机性。0=确定性输出（适合查询事实），0.7=默认，越高越随机。值越低回复越稳定，值越高越有创造性。" placement="top" effect="dark"><span class="help-icon">?</span></el-tooltip></span>
        </template>
        <el-slider v-model="form.temperature" :min="0" :max="2" :step="0.1" show-input />
      </el-form-item>
      <el-form-item>
        <template #label>
          <span class="label-with-help">最大Token <el-tooltip content="单次回复的硬上限。值太小回复会截断，值太大浪费 token。中文约 1 token=0.7 字。" placement="top" effect="dark"><span class="help-icon">?</span></el-tooltip></span>
        </template>
        <el-input-number v-model="form.max_tokens" :min="256" :max="128000" :step="256" />
      </el-form-item>
      <el-form-item>
        <template #label>
          <span class="label-with-help">Formatter <el-tooltip content="消息格式模板。DashScope=阿里Qwen，OpenAI=GPT/DeepSeek，Anthropic=Claude。选错会导致 API 报错。" placement="top" effect="dark"><span class="help-icon">?</span></el-tooltip></span>
        </template>
        <el-select v-model="form.formatter" style="width:100%">
          <el-option value="dashscope" label="DashScope (Qwen)" />
          <el-option value="openai" label="OpenAI (GPT)" />
          <el-option value="anthropic" label="Anthropic (Claude)" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <template #label>
          <span class="label-with-help">生成参数 <el-tooltip content="JSON 格式额外参数，合并到 API 请求中。常用: top_p(核采样), frequency_penalty(减少重复), presence_penalty(鼓励新话题)。不支持的参数会被静默忽略。" placement="top" effect="dark"><span class="help-icon">?</span></el-tooltip></span>
        </template>
        <el-input v-model="form.generate_kwargs" type="textarea" :rows="2" placeholder='{"parallel_tool_calls":true}' />
      </el-form-item>
    </el-form>
  </div>
</template>

<style scoped>
.form-hint { font-size: var(--app-size-sm); color: var(--ai-ink-muted); margin-left: 10px; }
.label-with-help { display: inline-flex; align-items: center; gap: 4px; }
.help-icon {
  display: inline-flex; align-items: center; justify-content: center;
  width: 16px; height: 16px; border-radius: 50%;
  background: var(--ai-ink-muted); color: var(--app-bg-card);
  font-size:var(--app-size-xs); font-weight: 700; cursor: help;
  opacity: 0.5; transition: opacity 0.15s;
}
.help-icon:hover { opacity: 1; background: var(--app-accent-purple, #b39ef3); }
</style>
