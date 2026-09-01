<script setup lang="ts">
import { computed } from 'vue'
import type { RouteModelConfig } from '@/shared/types/ai'

defineProps<{ label: string; disabled?: boolean }>()
const model = defineModel<RouteModelConfig>({ required: true })

const providers = [
  { value: 'dashscope', label: '阿里百炼 (DashScope)', models: ['qwen-max', 'qwen-plus', 'qwen-turbo', 'qwen3-235b'] },
  { value: 'openai', label: 'OpenAI', models: ['gpt-4o', 'gpt-4-turbo', 'gpt-3.5-turbo', 'o4-mini'] },
  { value: 'anthropic', label: 'Anthropic (Claude)', models: ['claude-fable-5', 'claude-opus-4-8', 'claude-sonnet-4-6'] },
  { value: 'deepseek', label: 'DeepSeek', models: ['deepseek-v4-pro', 'deepseek-v4-flash', 'deepseek-v4-flash-vision-exp'] },
  { value: 'custom', label: '自定义 (OpenAI 兼容)', models: [] },
]

// 模型名下拉选项：跟随当前所选厂商
const modelOptions = computed(() => {
  const prov = providers.find((p) => p.value === (model.value.provider || 'deepseek'))
  return prov?.models || []
})
</script>

<template>
  <div class="role-block">
    <div class="role-label">{{ label }}</div>
    <el-form label-width="90px" class="agent-form" :disabled="disabled">
      <el-form-item label="模型服务">
        <el-select v-model="model.provider" style="width:100%">
          <el-option v-for="p in providers" :key="p.value" :label="p.label" :value="p.value" />
        </el-select>
      </el-form-item>
      <el-form-item label="模型名">
        <el-select
          v-model="model.model_name"
          style="width:100%"
          allow-create
          filterable
          placeholder="选择或输入模型名"
        >
          <el-option v-for="m in modelOptions" :key="m" :label="m" :value="m" />
        </el-select>
      </el-form-item>
      <el-form-item label="API Key">
        <el-input v-model="model.api_key" type="password" show-password placeholder="sk-..." />
      </el-form-item>
      <el-form-item label="API 地址">
        <el-input v-model="model.base_url" placeholder="留空用默认" />
      </el-form-item>
    </el-form>
  </div>
</template>

<style scoped>
.role-block { margin-bottom: 18px; }
.role-label { font-size: var(--app-size-md); font-weight: 700; color: var(--ai-ink-soft); margin-bottom: 8px; }
</style>
