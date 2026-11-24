<script setup lang="ts">
import { onMounted, ref } from "vue"
import { ElMessage } from "element-plus"
import AppCard from "@/shared/components/AppCard.vue"
import DoodleBtn from "@/shared/components/DoodleBtn.vue"
import { formatApiError } from "@/shared/types/api-error"
import { fetchEvalModelConfigs, fetchRetrievalSettings, saveRetrievalSettings } from "../api"
import type { EvalModelConfig, RetrievalSettings } from "../types"

const settings = ref<RetrievalSettings | null>(null)
const models = ref<EvalModelConfig[]>([])
const saving = ref(false)
const loadError = ref("")

async function load() {
  loadError.value = ""
  try {
    const [current, configs] = await Promise.all([
      fetchRetrievalSettings(),
      fetchEvalModelConfigs("embedding"),
    ])
    if (!current.status || !current.data) throw current
    settings.value = current.data
    models.value = (configs.data?.configs || []).filter((item) => item.model_kind === "embedding")
  } catch (error) {
    loadError.value = formatApiError(error as never, "检索配置加载失败")
  }
}

async function save() {
  if (!settings.value?.embedding_model_id) {
    ElMessage.error("请选择向量模型")
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
    ElMessage.success(
      saved.data.reindex_required ? "已保存，切块已变，需重建索引" : "检索配置已保存",
    )
  } catch (error) {
    ElMessage.error(formatApiError(error as never, "检索配置保存失败"))
  } finally {
    saving.value = false
  }
}

onMounted(() => void load())
</script>

<template>
  <AppCard tone="var(--c-element)" :pin="false" :tilt="-0.4" class="ks-settings">
    <template #header><span>检索配置</span></template>
    <p v-if="loadError" class="ks-settings__note">{{ loadError }}</p>
    <div v-else-if="settings" class="sketch-kit">
      <div class="sketch-form">
        <label class="sketch-field">
          <span class="sketch-field__label">向量模型</span>
          <el-select v-model="settings.embedding_model_id" placeholder="选择向量模型">
            <el-option
              v-for="model in models"
              :key="model.id"
              :label="`${model.model_name} · ${model.provider}`"
              :value="model.id"
            />
          </el-select>
        </label>
        <label class="sketch-field">
          <span class="sketch-field__label">默认返回条数</span>
          <el-input v-model.number="settings.top_k" />
        </label>
        <label class="sketch-field">
          <span class="sketch-field__label">相似度阈值</span>
          <el-input v-model.number="settings.score_threshold" />
        </label>
        <label class="sketch-field">
          <span class="sketch-field__label">切块大小</span>
          <el-input v-model.number="settings.chunk_size" />
        </label>
        <label class="sketch-field">
          <span class="sketch-field__label">切块重叠</span>
          <el-input v-model.number="settings.chunk_overlap" />
        </label>
        <p v-if="settings.reindex_required" class="ks-settings__note">
          切块参数已变更，需对模块重建索引后才能检索。
        </p>
        <div class="sketch-form__actions">
          <DoodleBtn tone="yellow" :disabled="saving" @click="save">保存</DoodleBtn>
        </div>
      </div>
    </div>
  </AppCard>
</template>

<style scoped>
.ks-settings__note {
  margin: 0 0 var(--app-space-sm);
  font-size: var(--app-size-sm);
  color: var(--app-text-secondary);
}
</style>
