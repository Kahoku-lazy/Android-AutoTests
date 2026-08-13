<template>
  <div class="step-card" :class="{ 'step-card--collapsed': collapsed }">
    <!-- Header: always visible -->
    <div class="step-card__head" role="button" tabindex="0" @click="collapsed = !collapsed" @keydown.enter.prevent="collapsed = !collapsed" @keydown.space.prevent="collapsed = !collapsed">
      <span class="step-card__idx">{{ index + 1 }}</span>
      <span class="step-card__method" :style="{ color: methodColor }">{{ modelValue.method || 'GET' }}</span>
      <span class="step-card__summary">{{ modelValue.name || modelValue.url || '未命名步骤' }}</span>
      <span v-if="modelValue.assert" class="step-card__assert-badge">断言</span>
      <span class="step-card__toggle">{{ collapsed ? '▶' : '▼' }}</span>
      <div class="step-card__actions" @click.stop>
        <button class="act-btn" @click="$emit('moveUp')" :disabled="index === 0" title="上移">↑</button>
        <button class="act-btn" @click="$emit('moveDown')" title="下移">↓</button>
        <button class="act-btn" @click="$emit('duplicate')" title="复制">⧉</button>
        <button class="act-btn act-btn--del" @click="$emit('remove')" title="删除">×</button>
      </div>
    </div>

    <!-- Body: collapsible -->
    <div v-if="!collapsed" class="step-card__body">
      <!-- Name + Method row -->
      <div class="form-row">
        <div class="form-group form-group--flex">
          <label class="form-label">步骤名称</label>
          <el-input v-model="local.name" size="small" placeholder="如：登录获取Token" @change="emitUpdate" />
        </div>
        <div class="form-group form-group--w110">
          <label class="form-label">方法</label>
          <el-select v-model="local.method" size="small" @change="emitUpdate">
            <el-option v-for="m in METHODS" :key="m" :label="m" :value="m" />
          </el-select>
        </div>
      </div>

      <!-- Domain + URL -->
      <div class="form-row">
        <div class="form-group form-group--w200">
          <label class="form-label">域名</label>
          <el-input v-model="local.domain" size="small" placeholder="https://api.example.com" @change="emitUpdate" />
        </div>
        <div class="form-group form-group--flex">
          <label class="form-label">路径 <span class="form-hint">支持 {{ mustache('var') }}</span></label>
          <el-input v-model="local.url" size="small" placeholder="/api/auth/login" @change="emitUpdate" />
        </div>
      </div>

      <!-- Headers -->
      <div class="form-group">
        <label class="form-label">
          Headers
          <span class="form-hint">支持 {{ mustache('var') }}</span>
          <span v-if="unresolvedVars('headers').length" class="form-warn">{{ unresolvedVars('headers').join(', ') }} 未匹配</span>
        </label>
        <el-input
          :model-value="jsonText(local.headers)"
          type="textarea"
          :rows="3"
          size="small"
          placeholder='{"Content-Type": "application/json", "Authorization": "Bearer {{token}}"}'
          @update:model-value="updateJsonField('headers', $event)"
        />
      </div>

      <!-- Body -->
      <div class="form-group">
        <label class="form-label">
          Body
          <span class="form-hint">支持 {{ mustache('var') }}</span>
          <span v-if="unresolvedVars('body').length" class="form-warn">{{ unresolvedVars('body').join(', ') }} 未匹配</span>
        </label>
        <el-input
          :model-value="jsonText(local.body)"
          type="textarea"
          :rows="4"
          size="small"
          placeholder='{"username": "{{username}}", "password": "{{password}}"}'
          @update:model-value="updateJsonField('body', $event)"
        />
      </div>

      <!-- Extract -->
      <div class="form-group">
        <label class="form-label">变量提取</label>
        <div v-if="!local.extract.length" class="empty-hint">暂无提取规则，从响应中提取变量供后续步骤使用</div>
        <div v-for="(ex, ei) in local.extract" :key="ei" class="extract-row">
          <el-input v-model="ex.name" size="small" placeholder="变量名" class="form-group__input--w130" @change="emitUpdate" />
          <span class="extract-arrow">←</span>
          <el-input v-model="ex.path" size="small" placeholder="$.data.token" class="form-group__input--flex" @change="emitUpdate" />
          <el-button size="small" text type="danger" @click="removeExtract(ei)">×</el-button>
        </div>
        <el-button size="small" text type="primary" @click="addExtract">+ 添加提取规则</el-button>
      </div>

      <!-- Upstream variables reference -->
      <div v-if="upstreamVars && upstreamVars.length" class="upstream-hint">
        <span class="upstream-title">📥 可用上游变量：</span>
        <span v-for="(v, vi) in upstreamVars" :key="vi" class="upstream-chip" @click="insertVar(v.name)">
          {{ mustache(v.name) }}
        </span>
      </div>

      <!-- Schema editors: request_schema + response_schema -->
      <div class="schema-row">
        <div class="form-group form-group--flex">
          <label class="form-label">请求体 Schema</label>
          <div class="mode-switch">
            <el-radio-group v-model="reqSchemaMode" size="small">
              <el-radio-button value="visual">可视化</el-radio-button>
              <el-radio-button value="code">代码</el-radio-button>
            </el-radio-group>
          </div>
          <div v-if="reqSchemaMode === 'visual'" class="visual-schema">
            <div v-for="(f, fi) in reqFields" :key="fi" class="schema-field">
              <el-input v-model="f.key" size="small" placeholder="字段名" class="form-group__input--w110" @change="syncReqSchema" />
              <el-select v-model="f.type" size="small" class="form-group__select--w85" @change="syncReqSchema">
                <el-option label="string" value="string" />
                <el-option label="number" value="number" />
                <el-option label="integer" value="integer" />
                <el-option label="boolean" value="boolean" />
                <el-option label="object" value="object" />
                <el-option label="array" value="array" />
              </el-select>
              <el-checkbox v-model="f.required" size="small" @change="syncReqSchema">必填</el-checkbox>
              <el-button size="small" text type="danger" @click="removeReqField(fi)">×</el-button>
            </div>
            <el-button size="small" text @click="addReqField">+ 字段</el-button>
          </div>
          <el-input
            v-else
            :model-value="reqSchemaCode"
            type="textarea"
            :rows="4"
            size="small"
            @update:model-value="updateReqSchemaCode($event)"
          />
        </div>
        <div class="form-group form-group--flex">
          <label class="form-label">响应体 Schema</label>
          <div class="mode-switch">
            <el-radio-group v-model="respSchemaMode" size="small">
              <el-radio-button value="visual">可视化</el-radio-button>
              <el-radio-button value="code">代码</el-radio-button>
            </el-radio-group>
          </div>
          <div v-if="respSchemaMode === 'visual'" class="visual-schema">
            <div v-for="(f, fi) in respFields" :key="fi" class="schema-field">
              <el-input v-model="f.key" size="small" placeholder="字段名" class="form-group__input--w110" @change="syncRespSchema" />
              <el-select v-model="f.type" size="small" class="form-group__select--w85" @change="syncRespSchema">
                <el-option label="string" value="string" />
                <el-option label="number" value="number" />
                <el-option label="integer" value="integer" />
                <el-option label="boolean" value="boolean" />
                <el-option label="object" value="object" />
                <el-option label="array" value="array" />
              </el-select>
              <el-checkbox v-model="f.required" size="small" @change="syncRespSchema">必填</el-checkbox>
              <el-button size="small" text type="danger" @click="removeRespField(fi)">×</el-button>
            </div>
            <el-button size="small" text @click="addRespField">+ 字段</el-button>
          </div>
          <el-input
            v-else
            :model-value="respSchemaCode"
            type="textarea"
            :rows="4"
            size="small"
            @update:model-value="updateRespSchemaCode($event)"
          />
        </div>
      </div>

      <!-- Assert toggle -->
      <div class="form-row form-row--end">
        <label class="form-label">响应断言</label>
        <el-switch v-model="local.assert" size="small" @change="emitUpdate" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import type { ApiStep, ExtractRule, ResolvedVariable } from '../../types/api-config'
import { useJsonSchemaEditor, type SchemaField } from '../../composables/useJsonSchemaEditor'

const METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']
const METHOD_COLORS: Record<string, string> = {
  GET: '#6fba2c', POST: '#889df0', PUT: '#f7cd67', DELETE: '#e85f5f', PATCH: '#b39ef3',
  HEAD: '#909399', OPTIONS: '#909399',
}

const props = defineProps<{
  modelValue: ApiStep
  index: number
  upstreamVars?: { stepIndex: number; stepName: string; name: string; path: string }[]
}>()

const emit = defineEmits<{
  'update:modelValue': [value: ApiStep]
  remove: []
  duplicate: []
  moveUp: []
  moveDown: []
}>()

const collapsed = ref(false)
const local = reactive<ApiStep>(structuredClone(props.modelValue))

// Sync external changes → local
watch(() => props.modelValue, (v) => {
  const cloned = structuredClone(v)
  Object.keys(local).forEach(k => delete (local as any)[k])
  Object.assign(local, cloned)
}, { deep: true })

function emitUpdate() {
  emit('update:modelValue', { ...local })
}

const methodColor = computed(() => METHOD_COLORS[local.method] || '#909399')

// ── JSON text helpers ──
function jsonText(obj: Record<string, unknown> | null | undefined): string {
  if (!obj || !Object.keys(obj).length) return ''
  try { return JSON.stringify(obj, null, 2) } catch { return '' }
}

function updateJsonField(field: 'headers' | 'body', text: string) {
  try {
    const parsed = JSON.parse(text)
    if (typeof parsed === 'object' && parsed && !Array.isArray(parsed)) {
      ;(local as any)[field] = parsed
    }
  } catch {
    // Keep old value if invalid JSON
  }
  emitUpdate()
}

// ── Extract helpers ──
function addExtract() {
  local.extract = [...local.extract, { name: '', path: '' }]
  emitUpdate()
}
function removeExtract(i: number) {
  const arr = [...local.extract]; arr.splice(i, 1)
  local.extract = arr
  emitUpdate()
}

// ── Unresolved variable detection ──
function unresolvedVars(field: 'headers' | 'body'): string[] {
  const text = JSON.stringify((local as any)[field] || {})
  const matches = text.matchAll(/\{\{(\w+)\}\}/g)
  const upstream = new Set((props.upstreamVars || []).map(v => v.name))
  return [...matches].map(m => m[1]).filter(name => !upstream.has(name))
}

function insertVar(name: string) {
  // Insert into body — prepend a new key with the variable reference
  local.body = { ...local.body, [name]: `{{${name}}}` }
  emitUpdate()
}

function mustache(name: string) {
  return '{{' + name + '}}'
}

// ── Schema editors ──
const { schemaToFields, fieldsToSchema, toCodeText, parseCodeText } = useJsonSchemaEditor()

const reqSchemaMode = ref('visual')
const respSchemaMode = ref('visual')
const reqFields = ref<SchemaField[]>(schemaToFields(local.request_schema as Record<string, any> | null))
const respFields = ref<SchemaField[]>(schemaToFields(local.response_schema as Record<string, any> | null))
const reqSchemaCode = ref(toCodeText(local.request_schema as Record<string, any> | null))
const respSchemaCode = ref(toCodeText(local.response_schema as Record<string, any> | null))

function syncReqSchema() {
  const schema = fieldsToSchema(reqFields.value)
  local.request_schema = schema
  reqSchemaCode.value = toCodeText(schema)
  emitUpdate()
}
function syncRespSchema() {
  const schema = fieldsToSchema(respFields.value)
  local.response_schema = schema
  respSchemaCode.value = toCodeText(schema)
  emitUpdate()
}
function addReqField() {
  reqFields.value = [...reqFields.value, { key: '', type: 'string', required: false, description: '' }]
  syncReqSchema()
}
function removeReqField(i: number) {
  const arr = [...reqFields.value]; arr.splice(i, 1); reqFields.value = arr
  syncReqSchema()
}
function addRespField() {
  respFields.value = [...respFields.value, { key: '', type: 'string', required: false, description: '' }]
  syncRespSchema()
}
function removeRespField(i: number) {
  const arr = [...respFields.value]; arr.splice(i, 1); respFields.value = arr
  syncRespSchema()
}
function updateReqSchemaCode(text: string) {
  reqSchemaCode.value = text
  const parsed = parseCodeText(text)
  if (parsed) { local.request_schema = parsed; reqFields.value = schemaToFields(parsed); emitUpdate() }
}
function updateRespSchemaCode(text: string) {
  respSchemaCode.value = text
  const parsed = parseCodeText(text)
  if (parsed) { local.response_schema = parsed; respFields.value = schemaToFields(parsed); emitUpdate() }
}
</script>

<style scoped>
.step-card {
  background: var(--app-bg-card);
  border: 2px solid var(--app-border-light, #e0d8cc);
  border-left: 3px solid #f7cd67;
  border-radius: 6px 10px 6px 10px;
  margin-bottom: 8px;
  overflow: visible;
}
.step-card--collapsed { opacity: 0.85; }
.step-card__head {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 12px; cursor: pointer;
  background: rgba(0,0,0,0.02); user-select: none;
  border-bottom: 1px solid transparent;
}
.step-card:not(.step-card--collapsed) .step-card__head {
  border-bottom-color: var(--app-border-lighter, #e8e0d5);
}
.step-card__idx {
  display: inline-flex; align-items: center; justify-content: center;
  width: 24px; height: 24px; border-radius: 50%;
  background: var(--ink, #2d2d2d); color: var(--app-bg-card);
  font-size: var(--app-size-xs); font-weight: 800; flex-shrink: 0;
}
.step-card__method {
  font-size: var(--app-size-sm); font-weight: 800; font-family: var(--app-font-mono); min-width: 48px;
}
.step-card__summary {
  flex: 1; font-size: var(--app-size-sm); color: var(--app-ink-muted);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; min-width: 0;
}
.step-card__assert-badge {
  font-size: var(--app-size-xs); padding: 1px 6px; border-radius: 4px;
  background: rgba(136,157,240,0.15); color: var(--app-accent-purple); font-weight: 700; flex-shrink: 0;
}
.step-card__toggle { font-size: var(--app-size-xs); color: var(--app-ink-muted); flex-shrink: 0; }
.step-card__actions { display: flex; gap: 2px; flex-shrink: 0; }
.act-btn {
  border: none; background: none; font-size: var(--app-size-sm); cursor: pointer;
  padding: 0 4px; color: var(--app-ink-muted); font-weight: 700;
}
.act-btn:hover:not(:disabled) { color: var(--ink); }
.act-btn:disabled { opacity: 0.3; cursor: default; }
.act-btn--del:hover { color: var(--app-error); }

.step-card__body {
  padding: 14px; display: flex; flex-direction: column; gap: 12px;
}

.form-row { display: flex; gap: 10px; align-items: flex-start; }
.form-row--end { justify-content: flex-end; align-items: center; gap: 10px; }
.form-group { display: flex; flex-direction: column; gap: 4px; }
.form-label { font-size: var(--app-size-sm); font-weight: 700; color: var(--app-ink-muted); }
.form-hint { font-weight: 500; color: var(--app-ink-muted); font-size: var(--app-size-xs); }
.form-warn { color: var(--el-color-warning); font-size: var(--app-size-xs); font-weight: 600; }

.empty-hint { font-size: var(--app-size-xs); color: var(--app-ink-muted); padding: 8px 0; }

.extract-row { display: flex; gap: 6px; align-items: center; margin-bottom: 4px; }
.extract-arrow { color: var(--app-ink-muted); font-size: var(--app-size-sm); flex-shrink: 0; }

.upstream-hint {
  display: flex; flex-wrap: wrap; gap: 6px; align-items: center;
  padding: 8px 12px; background: rgba(136,157,240,0.06);
  border-radius: 6px; font-size: var(--app-size-xs);
}
.upstream-title { font-weight: 700; color: var(--app-ink-muted); margin-right: 4px; }
.upstream-chip {
  display: inline-block; padding: 2px 8px; border-radius: 4px;
  background: rgba(136,157,240,0.15); color: var(--app-accent-purple);
  font-family: var(--app-font-mono); font-size: var(--app-size-xs); font-weight: 600;
  cursor: pointer; user-select: none;
}
.upstream-chip:hover { background: rgba(136,157,240,0.3); }

.schema-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
@media (max-width: 700px) { .schema-row { grid-template-columns: 1fr; } }
.mode-switch { margin: 4px 0 6px; }
.visual-schema { display: flex; flex-direction: column; gap: 4px; }
.schema-field { display: flex; align-items: center; gap: 4px; }

/* ── Form group width utilities (replaces inline style="width:Npx") ── */
.form-group--flex { flex: 1; }
.form-group--w110 { width: 110px; }
.form-group--w200 { width: 200px; }
.form-group__input--w130 { width: 130px; }
.form-group__input--flex { flex: 1; }
.form-group__input--w110 { width: 110px; }
.form-group__select--w85 { width: 85px; }
</style>
