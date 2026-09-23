<script setup lang="ts">
/**
 * 新增元素行弹窗：字段与元素表呈现列同源（元素名称 / 文本 / 主定位 / 测试点），
 * 另加去重键 resource-id 与坐标（至少填一个）。
 * 校验规则与后端 element_fields.py 同口径，见 helpers/elementRowValidation.ts。
 */
import { reactive, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { PageElementFields } from '../api'
import {
  validateAlias,
  validateBounds,
  validateText,
  type TextField,
} from '../helpers/elementRowValidation'

const props = defineProps<{ modelValue: boolean }>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  confirm: [fields: PageElementFields]
}>()

function emptyForm() {
  return {
    alias: '',
    resource_id: '',
    bounds: '',
    text_val: '',
    primary_xpath: '',
    notes: '',
    is_test_point: false,
  }
}

const form = reactive(emptyForm())
const errors = reactive<Record<string, string>>({})

watch(
  () => props.modelValue,
  (opened) => {
    if (!opened) return
    Object.assign(form, emptyForm())
    clearErrors()
  },
)

function clearErrors() {
  for (const key of Object.keys(errors)) delete errors[key]
}

function limitedTextPairs(): Array<[TextField, string]> {
  return [
    ['alias', form.alias],
    ['text_val', form.text_val],
    ['primary_xpath', form.primary_xpath],
    ['resource_id', form.resource_id],
  ]
}

function validate(): boolean {
  clearErrors()
  const aliasReason = validateAlias(form.alias)
  if (aliasReason) errors.alias = aliasReason
  if (!form.resource_id.trim() && !form.bounds.trim()) {
    errors.resource_id = 'resource-id 与坐标至少填一个'
  }
  if (form.bounds.trim()) {
    const reason = validateBounds(form.bounds)
    if (reason) errors.bounds = reason
  }
  for (const [field, value] of limitedTextPairs()) {
    if (!value) continue
    const reason = validateText(field, value)
    if (reason) errors[field] = reason
  }
  return Object.keys(errors).length === 0
}

function close() {
  emit('update:modelValue', false)
}

function confirm() {
  if (!validate()) {
    ElMessage.warning('请先修正标红的字段')
    return
  }
  const fields: PageElementFields = { is_test_point: form.is_test_point }
  if (form.alias.trim()) fields.alias = form.alias.trim()
  if (form.text_val) fields.text_val = form.text_val
  if (form.primary_xpath.trim()) fields.primary_xpath = form.primary_xpath.trim()
  if (form.resource_id.trim()) fields.resource_id = form.resource_id.trim()
  if (form.bounds.trim()) fields.bounds = form.bounds.trim()
  if (form.notes) fields.notes = form.notes
  emit('confirm', fields)
}
</script>

<template>
  <el-dialog
    :model-value="modelValue"
    title="新增元素行"
    width="640px"
    :close-on-click-modal="false"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <p class="element-form__hint">元素名称必填；resource-id 与坐标至少填一个（二者用于识别同一元素）。</p>
    <el-form label-position="top" class="element-form">
      <el-form-item label="元素名称" required :error="errors.alias">
        <el-input v-model="form.alias" maxlength="500" placeholder="元素名称" />
      </el-form-item>
      <el-form-item label="resource-id" :error="errors.resource_id">
        <el-input v-model="form.resource_id" maxlength="500" placeholder="com.example:id/btn" />
      </el-form-item>
      <el-form-item label="坐标" :error="errors.bounds">
        <el-input v-model="form.bounds" maxlength="200" placeholder="[x1,y1][x2,y2]" />
      </el-form-item>
      <el-form-item label="文本" :error="errors.text_val">
        <el-input v-model="form.text_val" maxlength="2000" />
      </el-form-item>
      <el-form-item label="主定位" class="element-form__wide" :error="errors.primary_xpath">
        <el-input v-model="form.primary_xpath" placeholder="//android.widget.TextView[@text='登录']" />
      </el-form-item>
      <el-form-item label="备注" class="element-form__wide">
        <el-input v-model="form.notes" type="textarea" :rows="2" />
      </el-form-item>
      <el-form-item label="测试点">
        <el-switch v-model="form.is_test_point" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="close">取消</el-button>
      <el-button type="primary" @click="confirm">确定新增</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.element-form__hint {
  margin: 0 0 var(--app-space-md);
  font-size: var(--app-size-xs);
  color: var(--app-text-secondary);
}

.element-form {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  column-gap: var(--app-space-md);
  max-height: 60vh;
  overflow-y: auto;
  padding-right: var(--app-space-xs);
}

/**
 * Element Plus 的错误行是绝对定位（`.el-form-item__error` 为 top:100%），
 * 只占条目 margin 的空间；margin 小于错误行高度时它会被下一格输入框盖住，
 * 所以这里统一留 --app-space-lg（24px）。
 */
.element-form :deep(.el-form-item) {
  margin-bottom: var(--app-space-lg);
}

.element-form__wide {
  grid-column: 1 / -1;
}
</style>
