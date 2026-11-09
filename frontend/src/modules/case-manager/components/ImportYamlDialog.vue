<script setup lang="ts">
/**
 * ImportYamlDialog — 把一份 YAML 用例导入当前项目。
 *
 * 表名默认取文件名（去扩展名），同名表复用并按标题覆盖；「清理旧行」才删除
 * YAML 中已消失的用例。导入结论在弹窗内展示，成功后通知父级刷新目录树。
 */
import { computed, ref, watch } from "vue"
import { ElMessage } from "element-plus"
import { formatApiError } from "@/shared/api-client"
import { importYaml } from "../api"
import { BUSINESS_TYPE_OPTIONS } from "../types"
import type { YamlImportResult } from "../api"
import type { BusinessType } from "../types"

const props = defineProps<{
  modelValue: boolean
  projectId: number
}>()

const emit = defineEmits<{
  "update:modelValue": [value: boolean]
  "imported": [result: YamlImportResult]
}>()

const YAML_ACCEPT = ".yaml,.yml"
const MAX_SIZE = 20 * 1024 * 1024

const file = ref<File | null>(null)
const fileName = ref("")
/** YAML 没写 business 时落到哪一类；同一产品线通常是同一业务类型 */
const businessType = ref<BusinessType>("appliance")
const prune = ref(false)
const submitting = ref(false)
const result = ref<YamlImportResult | null>(null)
const error = ref("")

const canSubmit = computed(() => file.value !== null && fileName.value.trim() !== "")

function reset() {
  file.value = null
  fileName.value = ""
  businessType.value = "appliance"
  prune.value = false
  submitting.value = false
  result.value = null
  error.value = ""
}

watch(
  () => props.modelValue,
  (open) => {
    if (open) reset()
  },
)

function onFilePicked(picked: File | null) {
  result.value = null
  error.value = ""
  if (!picked) {
    file.value = null
    fileName.value = ""
    return
  }
  if (!/\.(yaml|yml)$/i.test(picked.name || "")) {
    ElMessage.error("只支持 YAML（.yaml / .yml）")
    return
  }
  if (picked.size > MAX_SIZE) {
    ElMessage.error("文件过大（上限 20MB）")
    return
  }
  file.value = picked
  fileName.value = picked.name.replace(/\.(yaml|yml)$/i, "")
}

async function submit() {
  if (!canSubmit.value || !file.value) return
  submitting.value = true
  error.value = ""
  try {
    const form = new FormData()
    form.append("file", file.value)
    form.append("project_id", String(props.projectId))
    form.append("file_name", fileName.value.trim())
    form.append("business_type", businessType.value)
    form.append("prune", prune.value ? "1" : "0")
    const { data } = await importYaml(form)
    if (data.status && data.data) {
      result.value = data.data
      ElMessage.success(`已导入 ${data.data.total} 条用例`)
      emit("imported", data.data)
    } else {
      error.value = data.message || "导入失败"
    }
  } catch (err: unknown) {
    error.value = formatApiError(err as never, "导入失败，请稍后重试")
  }
  submitting.value = false
}

function close() {
  emit("update:modelValue", false)
}
</script>

<template>
  <el-dialog
    :model-value="modelValue"
    title="导入 YAML 用例"
    width="560px"
    :close-on-click-modal="false"
    @update:model-value="emit('update:modelValue', $event as boolean)"
  >
    <div class="yaml-import">
      <p class="yaml-import__hint">
        每份 YAML 对应一张用例表；同名表会按用例标题覆盖更新，未出现在 YAML 中的旧行默认保留。
      </p>
      <el-upload
        :accept="YAML_ACCEPT"
        :limit="1"
        :auto-upload="false"
        :show-file-list="true"
        :on-change="(item) => onFilePicked(item.raw ?? null)"
        :on-remove="() => onFilePicked(null)"
      >
        <el-button size="small">选择 YAML</el-button>
      </el-upload>
      <el-form label-width="96px" @submit.prevent>
        <el-form-item label="用例表名">
          <el-input v-model="fileName" maxlength="200" show-word-limit placeholder="默认取文件名" />
        </el-form-item>
        <el-form-item label="业务类型">
          <el-radio-group v-model="businessType">
            <el-radio v-for="item in BUSINESS_TYPE_OPTIONS" :key="item.value" :value="item.value">
              {{ item.label }}
            </el-radio>
          </el-radio-group>
          <p class="yaml-import__field-hint">YAML 里写了 business 的用例以 YAML 为准</p>
        </el-form-item>
        <el-form-item label="清理旧行">
          <el-checkbox v-model="prune">删除 YAML 中已不存在的用例</el-checkbox>
        </el-form-item>
      </el-form>
      <p v-if="error" class="yaml-import__error">{{ error }}</p>
      <div v-if="result" class="yaml-import__result">
        <p class="yaml-import__result-title">
          表「{{ result.file_name }}」：共 {{ result.total }} 条，新建 {{ result.created }}，更新
          {{ result.updated }}，删除 {{ result.removed }}
        </p>
        <ul v-if="result.skipped.length" class="yaml-import__skipped">
          <li v-for="item in result.skipped" :key="item.title">
            {{ item.title }}：{{ item.reason }}
          </li>
        </ul>
      </div>
    </div>
    <template #footer>
      <el-button @click="close">关闭</el-button>
      <el-button type="primary" :loading="submitting" :disabled="!canSubmit" @click="submit">
        开始导入
      </el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.yaml-import {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-md);
}
.yaml-import__hint {
  margin: 0;
  font-size: var(--app-size-xs);
  line-height: var(--app-line-height-relaxed);
  color: var(--app-text-secondary);
}
.yaml-import__field-hint {
  margin: 0;
  width: 100%;
  font-size: var(--app-size-xs);
  line-height: var(--app-line-height-tight);
  color: var(--app-text-secondary);
}
.yaml-import__error {
  margin: 0;
  font-size: var(--app-size-sm);
  color: var(--app-status-danger-text);
}
.yaml-import__result {
  border: 2px solid var(--ink);
  border-radius: var(--app-radius-md);
  background: var(--app-bg-card);
  padding: var(--app-space-sm) var(--app-space-md);
}
.yaml-import__result-title {
  margin: 0;
  font-size: var(--app-size-sm);
  font-weight: var(--app-font-weight-bold);
  color: var(--app-text-primary);
}
.yaml-import__skipped {
  margin: var(--app-space-xs) 0 0;
  padding-left: var(--app-space-md);
  font-size: var(--app-size-xs);
  color: var(--app-text-secondary);
}
</style>
