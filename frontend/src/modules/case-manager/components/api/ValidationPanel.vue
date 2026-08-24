<template>
  <div class="validation-panel">
    <div class="panel-header">
      <h3>🔍 数据校验</h3>
      <el-button size="small" type="primary" text :disabled="readonly" @click="addRule">+ 添加规则</el-button>
    </div>
    <div class="panel-body">
      <el-empty v-if="!modelValue.length" description="暂无校验规则" :image-size="60" />
      <div v-for="(rule, i) in modelValue" :key="i" class="validation-rule">
        <div class="rule-header">
          <span class="rule-title">规则 {{ i + 1 }}</span>
          <el-button size="small" text type="danger" :disabled="readonly" @click="removeRule(i)">删除</el-button>
        </div>
        <div class="rule-row">
          <label>目标步骤</label>
          <el-select
            :model-value="rule.step_index"
            size="small"
            class="form-group__select--w120"
            :disabled="readonly"
            @update:model-value="updateRule(i, 'step_index', $event)"
          >
            <el-option
              v-for="j in stepCount"
              :key="j - 1"
              :label="`步骤 ${j}`"
              :value="j - 1"
            />
          </el-select>
        </div>
        <div class="rule-row">
          <label>启用</label>
          <el-switch
            :model-value="rule.enabled"
            size="small"
            :disabled="readonly"
            @update:model-value="updateRule(i, 'enabled', $event)"
          />
        </div>
        <div class="rule-row schema-editor">
          <label>JSON Schema</label>
          <div class="mode-switch">
            <el-radio-group
              :model-value="editorModes[i] || 'visual'"
              size="small"
              :disabled="readonly"
              @update:model-value="switchMode(i, String($event))"
            >
              <el-radio-button value="visual">可视化</el-radio-button>
              <el-radio-button value="code">代码</el-radio-button>
            </el-radio-group>
          </div>
          <!-- Visual mode -->
          <div v-if="(editorModes[i] || 'visual') === 'visual'" class="visual-schema">
            <div v-for="(field, fi) in (fieldCache[i] || [])" :key="fi" class="schema-field">
              <el-input v-model="field.key" size="small" placeholder="字段名" class="form-group__input--w120" :disabled="readonly" @change="syncFieldsToRule(i)" />
              <el-select v-model="field.type" size="small" class="form-group__select--w90" :disabled="readonly" @change="syncFieldsToRule(i)">
                <el-option label="string" value="string" />
                <el-option label="number" value="number" />
                <el-option label="integer" value="integer" />
                <el-option label="boolean" value="boolean" />
                <el-option label="object" value="object" />
                <el-option label="array" value="array" />
              </el-select>
              <el-checkbox v-model="field.required" size="small" :disabled="readonly" @change="syncFieldsToRule(i)">必填</el-checkbox>
              <el-button size="small" text type="danger" :disabled="readonly" @click="removeField(i, fi)">×</el-button>
            </div>
            <el-button size="small" text :disabled="readonly" @click="addField(i)">+ 字段</el-button>
          </div>
          <!-- Code mode -->
          <div v-else class="code-schema">
            <el-input
              :model-value="codeCache[i] || '{}'"
              type="textarea"
              :rows="6"
              size="small"
              :disabled="readonly"
              @update:model-value="updateCode(i, $event)"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'
import { ElMessageBox } from 'element-plus'
import type { ValidationRule } from '../../types/api-config'
import { useJsonSchemaEditor, type SchemaField } from '../../composables/useJsonSchemaEditor'

const props = defineProps<{ modelValue: ValidationRule[]; stepCount: number; readonly?: boolean }>()
const emit = defineEmits<{ 'update:modelValue': [value: ValidationRule[]] }>()

// Per-rule editor state
const editorModes = reactive<Record<number, string>>({})
const fieldCache = reactive<Record<number, SchemaField[]>>({})
const codeCache = reactive<Record<number, string>>({})
const { schemaToFields, fieldsToSchema, toCodeText, parseCodeText } = useJsonSchemaEditor()

// Initialize caches from modelValue
watch(() => props.modelValue, (rules) => {
  rules.forEach((r, i) => {
    if (!fieldCache[i]) {
      fieldCache[i] = schemaToFields(r.schema as Record<string, any> | null)
      codeCache[i] = toCodeText(r.schema as Record<string, any> | null)
      editorModes[i] = 'visual'
    }
  })
}, { immediate: true })

function updateRule(index: number, key: string, value: any) {
  const copy = [...props.modelValue]
  copy[index] = { ...copy[index], [key]: value }
  emit('update:modelValue', copy)
}

function addRule() {
  emit('update:modelValue', [
    ...props.modelValue,
    { step_index: 0, enabled: true, schema: null },
  ])
}

async function removeRule(index: number) {
  try {
    await ElMessageBox.confirm('确定删除此校验规则？', '确认删除', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' })
  } catch { return }
  const copy = [...props.modelValue]
  copy.splice(index, 1)
  // Shift cached state for rules after the removed index
  const newFieldCache: Record<number, SchemaField[]> = {}
  const newCodeCache: Record<number, string> = {}
  const newEditorModes: Record<number, string> = {}
  for (let i = index + 1; i <= copy.length; i++) {
    if (fieldCache[i]) { newFieldCache[i - 1] = fieldCache[i] }
    if (codeCache[i]) { newCodeCache[i - 1] = codeCache[i] }
    if (editorModes[i]) { newEditorModes[i - 1] = editorModes[i] }
  }
  for (const k of Object.keys(fieldCache)) delete fieldCache[Number(k)]
  for (const k of Object.keys(codeCache)) delete codeCache[Number(k)]
  for (const k of Object.keys(editorModes)) delete editorModes[Number(k)]
  Object.assign(fieldCache, newFieldCache)
  Object.assign(codeCache, newCodeCache)
  Object.assign(editorModes, newEditorModes)
  emit('update:modelValue', copy)
}

function switchMode(index: number, mode: string) {
  editorModes[index] = mode
  if (mode === 'visual') {
    fieldCache[index] = schemaToFields(parseCodeText(codeCache[index] || '{}'))
  } else {
    codeCache[index] = toCodeText(fieldsToSchema(fieldCache[index] || []))
  }
}

function addField(index: number) {
  if (!fieldCache[index]) fieldCache[index] = []
  fieldCache[index].push({ key: '', type: 'string', required: false, description: '' })
  syncFieldsToRule(index)
}

function removeField(ruleIdx: number, fieldIdx: number) {
  fieldCache[ruleIdx].splice(fieldIdx, 1)
  syncFieldsToRule(ruleIdx)
}

function syncFieldsToRule(index: number) {
  const schema = fieldsToSchema(fieldCache[index] || [])
  updateRule(index, 'schema', schema)
}

function updateCode(index: number, text: string) {
  codeCache[index] = text
  const parsed = parseCodeText(text)
  if (parsed) {
    updateRule(index, 'schema', parsed)
  }
}
</script>

<style scoped>
.validation-panel {
  background: var(--c-bg-card, #fff);
  border-radius: 8px;
  border: 1px solid var(--c-border, #e4e7ed);
}
.panel-header {
  padding: 12px 16px;
  border-bottom: 1px solid var(--c-border, #e4e7ed);
  background: var(--c-bg-subtle, #fafafa);
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.panel-header h3 { margin: 0; font-size: var(--app-size-sm); font-weight: 600; }
.panel-body { padding: 12px 16px; display: flex; flex-direction: column; gap: 12px; }
.validation-rule {
  border: 1px solid var(--c-border, #e4e7ed);
  border-radius: 6px;
  padding: 12px;
}
.rule-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
.rule-title { font-size: var(--app-size-sm); font-weight: 600; }
.rule-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-size: var(--app-size-sm);
}
.rule-row label { min-width: 60px; color: var(--c-text-secondary, #606266); }
.schema-editor { flex-direction: column; align-items: flex-start; }
.mode-switch { margin: 4px 0 8px; }
.visual-schema, .code-schema { width: 100%; }
.schema-field {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}

/* ── Form width utilities ── */
.form-group__select--w120 { width: 120px; }
.form-group__input--w120 { width: 120px; }
.form-group__select--w90 { width: 90px; }
</style>
