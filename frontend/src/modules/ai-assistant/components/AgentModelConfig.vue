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
      <el-form-item label="主推理模型">
        <el-select v-if="form.model_provider !== 'custom'" v-model="form.model_name"
          style="width:100%" allow-create filterable>
          <el-option v-for="m in availableModels" :key="m" :label="m" :value="m" />
        </el-select>
        <el-input v-else v-model="form.model_name" placeholder="输入模型名称" />
        <div class="form-hint" style="margin-top:4px">规划 / 推理任务使用，视觉模型留空时回退此模型</div>
        <div v-if="detectedModels.length" class="form-hint" style="margin-top:4px">
          已检测模型: {{ detectedModels.length }} 个
        </div>
      </el-form-item>
      <el-form-item label="视觉模型">
        <el-select v-model="form.vision_model_name" style="width:100%" allow-create filterable clearable
          placeholder="留空则使用文本模型">
          <el-option v-for="m in availableModels" :key="m" :label="m" :value="m" />
        </el-select>
        <div class="form-hint" style="margin-top:4px">控制手机时使用，留空则回退文本模型</div>
      </el-form-item>
      <el-form-item label="强模型">
        <el-switch v-model="form.strong_enabled" />
        <div class="form-hint" style="margin-top:4px">开启后对话直接下发强模型 Harness 执行（短路视觉执行）</div>
      </el-form-item>
      <el-form-item v-if="form.strong_enabled" label="强模型名">
        <el-select v-model="form.strong_model_name" style="width:100%" allow-create filterable clearable
          placeholder="留空则回退视觉模型">
          <el-option v-for="m in availableModels" :key="m" :label="m" :value="m" />
        </el-select>
        <div class="form-hint" style="margin-top:4px">强模型为空时回退使用视觉模型</div>
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
