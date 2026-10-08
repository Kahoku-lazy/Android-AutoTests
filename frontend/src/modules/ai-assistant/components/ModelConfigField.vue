<script setup lang="ts">
import { computed } from "vue"
import type { RouteModelConfig } from "@/shared/types/ai"
import { isKnownTextOnly, modelOptionLabel, type ModelOption } from "../helpers/model-capability"

const props = defineProps<{ label: string; disabled?: boolean; needsImage?: boolean }>()
const model = defineModel<RouteModelConfig>({ required: true })

// DeepSeek 清单镜像引擎侧的模型目录（engines/ai/agents/config.py 的 DEEPSEEK_MODELS），
// 两侧由 tests/graybox/unit/test_ai_deepseek_model_catalog.py 对拍，改一侧不齐即红。
const providers: { value: string; label: string; models: ModelOption[] }[] = [
  {
    value: "dashscope",
    label: "阿里百炼 (DashScope)",
    models: [
      { name: "qwen-max" },
      { name: "qwen-plus" },
      { name: "qwen-turbo" },
      { name: "qwen3-235b" },
    ],
  },
  {
    value: "openai",
    label: "OpenAI",
    models: [
      { name: "gpt-4o" },
      { name: "gpt-4-turbo" },
      { name: "gpt-3.5-turbo" },
      { name: "o4-mini" },
    ],
  },
  {
    value: "anthropic",
    label: "Anthropic (Claude)",
    models: [
      { name: "claude-fable-5" },
      { name: "claude-opus-4-8" },
      { name: "claude-sonnet-4-6" },
    ],
  },
  {
    value: "deepseek",
    label: "DeepSeek",
    models: [{ name: "deepseek-flash", multimodal: true }, { name: "deepseek-v4-pro" }],
  },
  { value: "custom", label: "自定义 (OpenAI 兼容)", models: [] },
]

// 模型名下拉选项：跟随当前所选厂商
const modelOptions = computed(() => {
  const prov = providers.find((p) => p.value === (model.value.provider || "deepseek"))
  return prov?.models || []
})

/**
 * 本角色需要读截图、但当前选中的是**已知纯文本**模型。
 * 只对清单内的已知模型判定：手工输入的自定义模型名能力未知，不提示（避免误报）。
 */
const imageMismatch = computed(
  () => Boolean(props.needsImage) && isKnownTextOnly(modelOptions.value, model.value.model_name),
)
</script>

<template>
  <div class="role-block">
    <div class="role-label">{{ label }}</div>
    <el-form label-width="90px" class="agent-form" :disabled="disabled">
      <el-form-item label="模型服务">
        <el-select v-model="model.provider" style="width: 100%">
          <el-option v-for="p in providers" :key="p.value" :label="p.label" :value="p.value" />
        </el-select>
      </el-form-item>
      <el-form-item label="模型名">
        <el-select
          v-model="model.model_name"
          style="width: 100%"
          allow-create
          filterable
          placeholder="选择或输入模型名"
        >
          <el-option
            v-for="m in modelOptions"
            :key="m.name"
            :label="modelOptionLabel(m)"
            :value="m.name"
          />
        </el-select>
      </el-form-item>
      <div v-if="needsImage" class="model-hint" :class="{ 'model-hint--warn': imageMismatch }">
        {{
          imageMismatch
            ? "该模型不支持图片输入，本角色需要读截图，请改用多模态模型（如 deepseek-flash）"
            : "本角色需要多模态模型（可读截图）"
        }}
      </div>
      <el-form-item label="API Key">
        <!-- autocomplete="new-password"：本表单是配置表单（上方是模型名文本输入 + 这里是密码框），
             浏览器会误判为登录表单并提示保存/填充凭据；new-password 表示"新凭据，不要填充"。 -->
        <el-input
          v-model="model.api_key"
          type="password"
          show-password
          autocomplete="new-password"
          placeholder="sk-..."
        />
      </el-form-item>
      <el-form-item label="API 地址">
        <el-input v-model="model.base_url" placeholder="留空用默认" />
      </el-form-item>
    </el-form>
  </div>
</template>

<style scoped>
.role-block {
  margin-bottom: 18px;
}
.role-label {
  font-size: var(--app-size-md);
  font-weight: 700;
  color: var(--ai-ink-soft);
  margin-bottom: var(--app-space-sm);
}
.model-hint {
  margin: -8px 0 var(--app-space-sm) 90px;
  font-size: var(--app-size-xs);
  color: var(--ai-ink-soft);
}
.model-hint--warn {
  color: var(--el-color-warning);
  font-weight: 700;
}
</style>
