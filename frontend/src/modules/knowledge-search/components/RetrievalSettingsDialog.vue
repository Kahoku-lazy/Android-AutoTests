<script setup lang="ts">
import { ref, watch } from "vue"
import { ElMessage } from "element-plus"
import DoodleBtn from "@/shared/components/DoodleBtn.vue"
import ErrorState from "@/shared/components/patterns/ErrorState.vue"
import SkeletonCard from "@/shared/components/patterns/SkeletonCard.vue"
import { formatApiError } from "@/shared/types/api-error"
import { fetchEvalModelConfigs, fetchRetrievalSettings, saveRetrievalSettings } from "../api"
import {
  KS_RETRIEVAL_DIALOG_TITLE,
  KS_RETRIEVAL_LOAD_FAILED,
  KS_RETRIEVAL_MODEL_REQUIRED,
  KS_RETRIEVAL_SAVE,
  KS_RETRIEVAL_SAVE_FAILED,
  KS_RETRIEVAL_SAVE_REINDEX,
} from "../constants"
import type { EvalModelConfig, RetrievalSettings } from "../types"

const visible = defineModel<boolean>({ required: true })

const settings = ref<RetrievalSettings | null>(null)
const models = ref<EvalModelConfig[]>([])
const loading = ref(false)
const saving = ref(false)
const loadError = ref("")

async function load() {
  settings.value = null
  loadError.value = ""
  loading.value = true
  try {
    const [current, configs] = await Promise.all([
      fetchRetrievalSettings(),
      fetchEvalModelConfigs("embedding"),
    ])
    if (!current.status || !current.data) throw current
    settings.value = current.data
    models.value = (configs.data?.configs || []).filter((item) => item.model_kind === "embedding")
  } catch (error) {
    loadError.value = formatApiError(error as never, KS_RETRIEVAL_LOAD_FAILED)
  } finally {
    loading.value = false
  }
}

async function save() {
  if (!settings.value?.embedding_model_id) {
    ElMessage.error(KS_RETRIEVAL_MODEL_REQUIRED)
    return
  }
  saving.value = true
  try {
    const saved = await saveRetrievalSettings({
      embedding_model_id: settings.value.embedding_model_id,
      top_k: settings.value.top_k,
      score_threshold: settings.value.score_threshold,
      chunk_size: settings.value.chunk_size,
      chunk_overlap: settings.value.chunk_overlap,
    })
    if (!saved.status || !saved.data) throw saved
    settings.value = saved.data
    ElMessage.success(saved.data.reindex_required ? KS_RETRIEVAL_SAVE_REINDEX : KS_RETRIEVAL_SAVE)
  } catch (error) {
    ElMessage.error(formatApiError(error as never, KS_RETRIEVAL_SAVE_FAILED))
  } finally {
    saving.value = false
  }
}

watch(visible, (open) => {
  if (open) void load()
})
</script>

<template>
  <el-dialog
    v-model="visible"
    :title="KS_RETRIEVAL_DIALOG_TITLE"
    width="520px"
    append-to-body
    destroy-on-close
    :close-on-click-modal="false"
  >
    <SkeletonCard v-if="loading" variant="list" :lines="5" />
    <ErrorState v-else-if="loadError" :message="loadError" @retry="load" />
    <el-form v-else-if="settings" label-width="96px" label-position="left">
      <el-form-item label="向量模型" required>
        <el-select v-model="settings.embedding_model_id" placeholder="选择向量模型">
          <el-option
            v-for="model in models"
            :key="model.id"
            :label="`${model.model_name} · ${model.provider}`"
            :value="model.id"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="默认返回条数">
        <el-input v-model.number="settings.top_k" />
      </el-form-item>
      <el-form-item label="相似度阈值">
        <el-input v-model.number="settings.score_threshold" />
      </el-form-item>
      <el-form-item label="切块大小">
        <el-input v-model.number="settings.chunk_size" />
      </el-form-item>
      <el-form-item label="切块重叠">
        <el-input v-model.number="settings.chunk_overlap" />
      </el-form-item>
      <p v-if="settings.reindex_required" class="ks-settings__note">
        切块参数已变更，需对模块重建索引后才能检索。
      </p>
    </el-form>
    <template #footer>
      <DoodleBtn @click="visible = false">取消</DoodleBtn>
      <DoodleBtn tone="yellow" :disabled="saving || !settings" @click="save">保存</DoodleBtn>
    </template>
  </el-dialog>
</template>

<style scoped>
.ks-settings__note {
  margin: 0;
  font-size: var(--app-size-sm);
  color: var(--app-text-secondary);
}
</style>
