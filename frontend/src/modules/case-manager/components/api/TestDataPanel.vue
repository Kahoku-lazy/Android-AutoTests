<template>
  <div class="test-data-panel">
    <div class="panel-header">
      <h3>📊 测试数据</h3>
      <span class="panel-badge">{{ dataColumns.length }} 列 · {{ modelValue.length }} 行</span>
      <el-button size="small" type="primary" text :disabled="readonly" @click="addRow">+ 添加行</el-button>
    </div>
    <div class="panel-body">
      <el-empty v-if="!dataColumns.length && !modelValue.length" description="暂无测试数据。在步骤的 body/headers/url 中使用 {{var}} 占位符后，此处自动生成列头。" :image-size="60" />
      <div v-else class="data-table-wrapper">
        <div class="data-table-scroll">
          <table class="data-table">
            <thead>
              <tr>
                <th class="data-th data-th--idx">#</th>
                <th v-for="col in allColumns" :key="col" class="data-th">
                  {{ col }}
                  <small>{{ col }} 值</small>
                </th>
                <th class="data-th data-th--output">输出断言</th>
                <th class="data-th data-th--act"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, ri) in modelValue" :key="ri">
                <td class="data-td data-td--idx">{{ ri + 1 }}</td>
                <td v-for="col in allColumns" :key="col" class="data-td">
                  <input
                    :value="(row.input || {})[col] || ''"
                    @input="updateCell(ri, col, ($event.target as HTMLInputElement).value)"
                    class="data-cell"
                    :placeholder="col"
                    :disabled="readonly"
                  />
                </td>
                <td class="data-td data-td--output">
                  <button class="output-btn" :disabled="readonly" @click="openOutputEditor(ri)">
                    {{ (row.output_schema && row.output_schema.schema && Object.keys(row.output_schema.schema).length > 2) ? '已配置 ✓' : '未配置' }}
                  </button>
                </td>
                <td class="data-td data-td--act">
                  <button class="row-del-btn" :disabled="readonly" @click="removeRow(ri)" title="删除行">×</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Output schema editor dialog -->
    <el-dialog v-model="outputDialogVisible" title="行输出断言配置" width="500px" :close-on-click-modal="false">
      <div class="dialog-row">
        <label class="form-label">目标步骤</label>
        <el-select v-model="editingOutput.step_index" size="small" class="form-group__select--w120" :disabled="readonly">
          <el-option v-for="j in stepCount" :key="j - 1" :label="`步骤 ${j}`" :value="j - 1" />
        </el-select>
      </div>
      <div class="dialog-row">
        <label class="form-label">JSON Schema</label>
        <div class="mode-switch">
          <el-radio-group v-model="outputSchemaMode" size="small" :disabled="readonly">
            <el-radio-button value="visual">可视化</el-radio-button>
            <el-radio-button value="code">代码</el-radio-button>
          </el-radio-group>
        </div>
        <div v-if="outputSchemaMode === 'visual'" class="visual-schema">
          <div v-for="(f, fi) in outputFields" :key="fi" class="schema-field">
            <el-input v-model="f.key" size="small" placeholder="字段名" class="form-group__input--w110" :disabled="readonly" @change="syncOutputSchema" />
            <el-select v-model="f.type" size="small" class="form-group__select--w85" :disabled="readonly" @change="syncOutputSchema">
              <el-option label="string" value="string" />
              <el-option label="number" value="number" />
              <el-option label="integer" value="integer" />
              <el-option label="boolean" value="boolean" />
              <el-option label="object" value="object" />
              <el-option label="array" value="array" />
            </el-select>
            <el-checkbox v-model="f.required" size="small" :disabled="readonly" @change="syncOutputSchema">必填</el-checkbox>
            <el-button size="small" text type="danger" :disabled="readonly" @click="removeOutputField(fi)">×</el-button>
          </div>
          <el-button size="small" text :disabled="readonly" @click="addOutputField">+ 字段</el-button>
        </div>
        <el-input
          v-else
          v-model="outputSchemaCode"
          type="textarea"
          :rows="6"
          size="small"
          :disabled="readonly"
          @change="syncOutputSchemaFromCode"
        />
      </div>
      <template #footer>
        <el-button @click="outputDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveOutputSchema">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { ElMessageBox } from 'element-plus'
import type { TestDataRow, OutputSchema } from '../../types/api-config'
import { useJsonSchemaEditor, type SchemaField } from '../../composables/useJsonSchemaEditor'

const props = defineProps<{
  modelValue: TestDataRow[]
  dataColumns: string[]
  stepCount: number
  readonly?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: TestDataRow[]]
}>()

// Union of auto-extracted columns + columns from existing row inputs
const allColumns = computed(() => {
  const set = new Set(props.dataColumns)
  for (const row of props.modelValue) {
    if (row.input) {
      for (const k of Object.keys(row.input)) {
        set.add(k)
      }
    }
  }
  return [...set]
})

function updateCell(rowIdx: number, col: string, val: string) {
  const copy = props.modelValue.map((r, i) => {
    if (i !== rowIdx) return r
    return { ...r, input: { ...(r.input || {}), [col]: val } }
  })
  emit('update:modelValue', copy)
}

function addRow() {
  const input: Record<string, string> = {}
  for (const col of allColumns.value) {
    input[col] = ''
  }
  emit('update:modelValue', [...props.modelValue, { input, output_schema: null }])
}

async function removeRow(index: number) {
  try {
    await ElMessageBox.confirm('确定删除此行测试数据？', '确认删除', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' })
  } catch { return }
  const copy = [...props.modelValue]
  copy.splice(index, 1)
  emit('update:modelValue', copy)
}

// ── Output schema editor ──
const { schemaToFields, fieldsToSchema, toCodeText, parseCodeText } = useJsonSchemaEditor()
const outputDialogVisible = ref(false)
const outputSchemaMode = ref('visual')
const editingRowIdx = ref(-1)
const editingOutput = reactive<OutputSchema>({ step_index: 0, schema: {} })
const outputFields = ref<SchemaField[]>([])
const outputSchemaCode = ref('{}')

function openOutputEditor(rowIdx: number) {
  editingRowIdx.value = rowIdx
  const row = props.modelValue[rowIdx]
  const os = row.output_schema
  editingOutput.step_index = os?.step_index ?? 0
  editingOutput.schema = os?.schema ? { ...os.schema } : {}
  outputFields.value = schemaToFields(os?.schema as Record<string, any> | null)
  outputSchemaCode.value = toCodeText(os?.schema as Record<string, any> | null)
  outputSchemaMode.value = 'visual'
  outputDialogVisible.value = true
}

function syncOutputSchema() {
  editingOutput.schema = fieldsToSchema(outputFields.value)
  outputSchemaCode.value = toCodeText(editingOutput.schema)
}
function syncOutputSchemaFromCode() {
  const parsed = parseCodeText(outputSchemaCode.value)
  if (parsed) { editingOutput.schema = parsed; outputFields.value = schemaToFields(parsed) }
}
function addOutputField() {
  outputFields.value = [...outputFields.value, { key: '', type: 'string', required: false, description: '' }]
  syncOutputSchema()
}
function removeOutputField(i: number) {
  const arr = [...outputFields.value]; arr.splice(i, 1); outputFields.value = arr
  syncOutputSchema()
}
function saveOutputSchema() {
  const copy = [...props.modelValue]
  const hasContent = editingOutput.schema && Object.keys(editingOutput.schema).length > 0
  copy[editingRowIdx.value] = {
    ...copy[editingRowIdx.value],
    output_schema: hasContent ? { step_index: editingOutput.step_index, schema: editingOutput.schema } : null,
  }
  emit('update:modelValue', copy)
  outputDialogVisible.value = false
}
</script>

<style scoped>
.test-data-panel {
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
.panel-badge { font-size: var(--app-size-xs); color: var(--app-ink-muted); font-weight: 600; margin-left: auto; margin-right: 10px; }
.panel-body { padding: 12px 16px; }

.data-table-wrapper { }
.data-table-scroll { overflow-x: auto; max-width: 100%; }
.data-table { width: 100%; min-width: 400px; border-collapse: collapse; font-size: var(--app-size-sm); }
.data-th {
  background: rgba(111,186,44,0.08); padding: 10px 12px;
  font-weight: 700; color: var(--ink); text-align: left;
  white-space: nowrap; border-bottom: 2px solid var(--ink); min-width: 120px;
}
.data-th small { display: block; font-size: var(--app-size-xs); color: var(--app-ink-muted); font-weight: 500; margin-top: 2px; }
.data-th--idx { width: 36px; min-width: 36px; text-align: center; }
.data-th--output { min-width: 100px; }
.data-th--act { width: 36px; min-width: 36px; }
.data-td { padding: 6px 8px; border-bottom: 1px solid var(--app-border-lighter); }
.data-td--idx { text-align: center; font-size: var(--app-size-xs); color: var(--app-ink-muted); font-weight: 600; }
.data-td--act { text-align: center; }
.data-td--output { text-align: center; }
.data-cell {
  width: 100%; padding: 8px 10px; border: 1px solid var(--app-border-lighter);
  border-radius: 4px; font-size: var(--app-size-sm); font-family: var(--app-font-mono);
  outline: none; min-width: 100px; line-height: 1.4; box-sizing: border-box;
}
.data-cell:focus { border-color: var(--c-case, #4ECDC4); }
.row-del-btn {
  border: none; background: none; color: var(--app-error); font-size: var(--app-size-md);
  cursor: pointer; font-weight: 700; padding: 2px 6px;
}
.output-btn {
  border: 1.5px dashed var(--app-border-light);
  border-radius: 4px; padding: 4px 10px; font-size: var(--app-size-xs);
  background: transparent; cursor: pointer; color: var(--app-ink-muted); font-weight: 600;
}
.output-btn:hover { border-color: var(--ink); color: var(--ink); }

.dialog-row { margin-bottom: 12px; }
.form-label { font-size: var(--app-size-sm); font-weight: 600; color: var(--app-ink-muted); margin-bottom: 4px; display: block; }
.mode-switch { margin: 4px 0 8px; }
.visual-schema { display: flex; flex-direction: column; gap: 4px; }
.schema-field { display: flex; align-items: center; gap: 4px; }

/* ── Form width utilities ── */
.form-group__select--w120 { width: 120px; }
.form-group__input--w110 { width: 110px; }
.form-group__select--w85 { width: 85px; }
</style>
