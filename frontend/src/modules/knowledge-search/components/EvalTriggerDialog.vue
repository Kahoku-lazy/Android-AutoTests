<script setup lang="ts">
/** EvalTriggerDialog — 发起评测：选模块 / chat 模型 / 题量，展示预估 token。 */
import { computed, reactive, ref, watch } from "vue"
import DoodleBtn from "@/shared/components/DoodleBtn.vue"
import { fetchEvalModelConfigs } from "../api"
import {
  KS_EVAL_DIALOG_TITLE,
  KS_EVAL_ESTIMATE_NOTE,
  KS_EVAL_NEG_DEFAULT,
  KS_EVAL_NO_CHAT_MODEL,
  KS_EVAL_POS_DEFAULT,
  KS_EVAL_TOTAL_MAX,
} from "../constants"
import { estimateEvalTokens } from "../helpers/estimate"
import type { EvalModelConfig, EvalTriggerPayload, KnowledgeModuleRow } from "../types"

const props = defineProps<{ modules: KnowledgeModuleRow[] }>()
const visible = defineModel<boolean>({ required: true })
const emit = defineEmits<{ trigger: [payload: EvalTriggerPayload] }>()

const models = ref<EvalModelConfig[]>([])
const modelError = ref("")
const form = reactive({
  module_id: 0,
  model_config_id: 0,
  pos_count: KS_EVAL_POS_DEFAULT,
  neg_count: KS_EVAL_NEG_DEFAULT,
})

const enabledModules = computed(() => props.modules.filter((module) => module.enabled))
const estimate = computed(() => estimateEvalTokens(form.pos_count, form.neg_count))
const overCap = computed(() => form.pos_count + form.neg_count > KS_EVAL_TOTAL_MAX)
const canSubmit = computed(
  () => form.module_id > 0 && form.model_config_id > 0 && !overCap.value && form.pos_count >= 1,
)

watch(visible, async (open) => {
  if (!open) return
  form.module_id = enabledModules.value[0]?.id ?? 0
  form.pos_count = KS_EVAL_POS_DEFAULT
  form.neg_count = KS_EVAL_NEG_DEFAULT
  modelError.value = ""
  try {
    const response = await fetchEvalModelConfigs()
    const configs = response.data?.configs ?? []
    models.value = configs.filter((config) => config.model_kind === "chat")
    form.model_config_id = models.value[0]?.id ?? 0
    if (models.value.length === 0) modelError.value = KS_EVAL_NO_CHAT_MODEL
  } catch {
    modelError.value = KS_EVAL_NO_CHAT_MODEL
  }
})

function onSubmit() {
  if (!canSubmit.value) return
  emit("trigger", { ...form })
}
</script>

<template>
  <el-dialog v-model="visible" :title="KS_EVAL_DIALOG_TITLE" width="520px" append-to-body>
    <el-form label-width="88px" label-position="left">
      <el-form-item label="模块" required>
        <el-select v-model="form.module_id" placeholder="选择要评测的模块">
          <el-option
            v-for="module in enabledModules"
            :key="module.id"
            :label="module.name"
            :value="module.id"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="出题模型" required>
        <el-select v-model="form.model_config_id" placeholder="chat 类模型配置">
          <el-option
            v-for="model in models"
            :key="model.id"
            :label="`${model.model_name}（${model.provider}）`"
            :value="model.id"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="正题数">
        <el-input-number v-model="form.pos_count" :min="1" :max="KS_EVAL_TOTAL_MAX" />
      </el-form-item>
      <el-form-item label="负样本数">
        <el-input-number v-model="form.neg_count" :min="0" :max="KS_EVAL_TOTAL_MAX" />
      </el-form-item>
    </el-form>
    <p v-if="modelError" class="ks-trigger__error">{{ modelError }}</p>
    <p v-if="overCap" class="ks-trigger__error">题量合计不能超过 {{ KS_EVAL_TOTAL_MAX }}</p>
    <p class="ks-trigger__estimate">
      预估：出题输入 ≈ {{ estimate.chat_input_tokens }} tokens · 输出 ≈
      {{ estimate.chat_output_tokens }} tokens · 检索嵌入 ≈ {{ estimate.embedding_tokens }} tokens
    </p>
    <p class="ks-trigger__note">{{ KS_EVAL_ESTIMATE_NOTE }}</p>
    <template #footer>
      <DoodleBtn @click="visible = false">取消</DoodleBtn>
      <DoodleBtn tone="teal" :disabled="!canSubmit" @click="onSubmit">发起</DoodleBtn>
    </template>
  </el-dialog>
</template>

<style scoped>
.ks-trigger__error {
  margin: 0 0 var(--app-space-xs);
  font-size: var(--app-size-xs);
  color: var(--app-status-danger-text);
}

.ks-trigger__estimate {
  margin: 0 0 var(--app-space-xs);
  font-size: var(--app-size-xs);
  color: var(--app-text-primary);
}

.ks-trigger__note {
  margin: 0;
  font-size: var(--app-size-xs);
  color: var(--app-text-secondary);
}
</style>
