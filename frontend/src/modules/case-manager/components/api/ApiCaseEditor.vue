<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import WorkbenchHeader from '@/shared/components/WorkbenchHeader.vue'
import ErrorState from '@/shared/components/patterns/ErrorState.vue'
import { getApiDefinition, saveApiDefinition, deleteApiDefinition } from '../../api/apiTesting'
import ApiStepEditor from './ApiStepEditor.vue'

const STEP_TYPES = ['api_request', 'api_assert', 'api_sleep', 'api_log']

const router = useRouter()
const route = useRoute()

const caseId = computed(() => route.params.id)
const isNew = computed(() => !caseId.value || caseId.value === 'new')
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const directoryName = ref('')

const METHOD_COLORS = { GET: '#6fba2c', POST: '#889df0', PUT: '#f7cd67', DELETE: '#e85f5f', PATCH: '#b39ef3' }
const PRIORITY_COLORS = { P0: '#e85f5f', P1: '#f7cd67', P2: '#889df0' }
const TYPES = ['string', 'number', 'boolean', 'object', 'array']

const form = ref({
  id: '', title: '', description: '',
  precondition: '', priority: 'P1', enabled: true,
  directory_id: null,
})

// ── Steps (multi-step editor) ──
const steps = ref([])

function defaultApiStep(type = 'api_request') {
  const base = { type, description: '', expected_status: 200 }
  if (type === 'api_request') return { ...base, method: 'GET', url: '', headers: {}, body: {}, extract: {} }
  if (type === 'api_assert')  return { ...base, assertions: [] }
  if (type === 'api_sleep')   return { ...base, timeout: 1 }
  if (type === 'api_log')     return { ...base, value: '' }
  return base
}

function addStep(type) { steps.value = [...steps.value, defaultApiStep(type || 'api_request')] }
function removeStep(i) { const arr = [...steps.value]; arr.splice(i, 1); steps.value = arr }
function duplicateStep(i) { const arr = [...steps.value]; arr.splice(i + 1, 0, JSON.parse(JSON.stringify(arr[i]))); steps.value = arr }

// ── Field editors (parsed from JSON strings) ──
const headerFields = ref([])    // [{key, type}]
const bodyFields = ref([])
const respFields = ref([])

function parseFields(jsonStr) {
  if (!jsonStr || !jsonStr.trim()) return []
  try {
    const obj = JSON.parse(jsonStr)
    if (typeof obj !== 'object' || Array.isArray(obj)) return []
    return Object.entries(obj).map(([k, v]) => ({ key: k, type: guessType(v) }))
  } catch { return [] }
}
function guessType(v) {
  if (v === null) return 'string'
  const t = typeof v; if (t === 'object') return Array.isArray(v) ? 'array' : 'object'
  return t
}
function fieldsToJson(fields) {
  if (!fields.length) return ''
  const obj = {}
  fields.forEach(f => { obj[f.key] = typeDefault(f.type) })
  return JSON.stringify(obj, null, 2)
}
function typeDefault(t) { return { string: '', number: 0, boolean: true, object: {}, array: [] }[t] || '' }

function syncFromForm() { headerFields.value = parseFields(form.value.headers); bodyFields.value = parseFields(form.value.body); respFields.value = parseFields(form.value.expected_response) }
function syncToForm() { form.value.headers = fieldsToJson(headerFields.value); form.value.body = fieldsToJson(bodyFields.value); form.value.expected_response = fieldsToJson(respFields.value) }

function addField(list) { list.push({ key: '', type: 'string' }) }
function removeField(list, i) { list.splice(i, 1) }

// ── Data module ──
const inputCols = computed(() => bodyFields.value.filter(f => f.key))
const validateCols = computed(() => (form.value.rows || []).filter(r => r.kind === 'validate'))

const allDataCols = computed(() => [
  ...inputCols.value.map(f => ({ key: f.key, type: f.type, kind: 'input' })),
  ...validateCols.value.map(r => ({ key: r.key, type: r.type || 'string', kind: 'validate' })),
])

function getColValues(key) {
  const col = (form.value.rows || []).find(r => r.key === key)
  return col?.values || []
}
function setColValues(key, vals) {
  const rows = [...(form.value.rows || [])]
  const idx = rows.findIndex(r => r.key === key)
  if (idx >= 0) rows[idx] = { ...rows[idx], values: vals }
  else rows.push({ key, values: vals, kind: rows.some(r => r.key.startsWith('$.')) ? 'validate' : 'input', type: 'string' })
  form.value.rows = rows
}

const dataRowCount = computed(() => {
  const lens = allDataCols.value.map(c => getColValues(c.key).length)
  return Math.max(0, ...lens)
})

const dataRows = computed(() => {
  const rows = []
  for (let i = 0; i < dataRowCount.value; i++) {
    const row = {}
    allDataCols.value.forEach(c => { row[c.key] = getColValues(c.key)[i] ?? '' })
    rows.push(row)
  }
  return rows
})

function addDataRow() {
  allDataCols.value.forEach(c => {
    const vals = [...getColValues(c.key), '']
    setColValues(c.key, vals)
  })
}
function removeDataRow(i) {
  allDataCols.value.forEach(c => {
    const vals = getColValues(c.key).filter((_, idx) => idx !== i)
    setColValues(c.key, vals)
  })
}
function updateCell(colKey, rowIdx, val) {
  const vals = [...getColValues(colKey)]
  while (vals.length <= rowIdx) vals.push('')
  vals[rowIdx] = val
  setColValues(colKey, vals)
}

function addValidateCol() {
  const rows = [...(form.value.rows || [])]
  rows.push({ key: '', values: [], kind: 'validate', type: 'string' })
  form.value.rows = rows
}
function removeValidateCol(idx) {
  const rows = [...(form.value.rows || [])]
  const vi = rows.findIndex(r => r.kind === 'validate')
  if (vi >= 0) {
    // idx is relative to validate cols
    const allVi = rows.map((r, i) => r.kind === 'validate' ? i : -1).filter(i => i >= 0)
    if (idx < allVi.length) rows.splice(allVi[idx], 1)
  }
  form.value.rows = rows
}
function updateValidateColKey(vi, key) {
  const rows = [...(form.value.rows || [])]
  const allVi = rows.map((r, i) => r.kind === 'validate' ? i : -1).filter(i => i >= 0)
  if (vi < allVi.length) rows[allVi[vi]].key = key
  form.value.rows = rows
}

// ── Assertions (legacy, unused in step-list mode) ──
const assertionOps = ['exists', 'equals', 'contains', 'not_equals']

function jsonStr(obj, fallback = '') {
  if (!obj || !Object.keys(obj).length) return fallback
  try { return JSON.stringify(obj, null, 2) } catch { return fallback }
}
function tryParseJson(val) {
  if (!val || typeof val !== 'string') return val || {}
  try { const o = JSON.parse(val); return typeof o === 'object' && o ? o : {} } catch { return {} }
}

// ── Load ──
async function load() {
  if (isNew.value) {
    if (route.query.directory_id) form.value.directory_id = Number(route.query.directory_id)
    if (route.query.dir_name) directoryName.value = route.query.dir_name
    return
  }
  loading.value = true
  try {
    const { data } = await getApiDefinition(caseId.value)
    if (data.status) {
      const d = data.definition
      form.value = {
        id: d.id, title: d.title,
        description: d.description || '', precondition: d.precondition || '',
        priority: d.priority || 'P1', enabled: d.enabled,
        directory_id: d.directory_id,
        rows: d.rows || [],
      }
      // Parse steps_json → steps array (backward compat)
      try {
        const parsed = JSON.parse(d.steps_json || '[]')
        steps.value = Array.isArray(parsed) ? parsed : []
      } catch { steps.value = [] }
      if (!steps.value.length) {
        if (d.method || d.url) {
          steps.value = [{ type: 'api_request', method: d.method || 'GET', url: d.url || '',
            headers: tryParseJson(d.headers), body: tryParseJson(d.body),
            expected_status: d.expected_status || 200, description: '' }]
        }
        if ((d.assertions || []).length) {
          steps.value.push({ type: 'api_assert', assertions: d.assertions,
            expected_status: d.expected_status || 200, description: '' })
        }
      }
      // Sync body fields from first request for data module compat
      const reqStep = steps.value.find(s => s.type === 'api_request')
      if (reqStep) {
        headerFields.value = parseFields(jsonStr(reqStep.headers))
        bodyFields.value = parseFields(jsonStr(reqStep.body))
      }
      directoryName.value = d.directory_name || ''
      syncFromForm()
    } else { error.value = data.message || '加载失败' }
  } catch (e) { error.value = '加载用例失败' }
  loading.value = false
}

// ── Save ──
function syncFieldsToStep() {
  // Push field-editor headers/body back into the first api_request step
  const reqStep = steps.value.find(s => s.type === 'api_request')
  if (reqStep) {
    reqStep.headers = parseFields(fieldsToJson(headerFields.value)).length ? JSON.parse(fieldsToJson(headerFields.value) || '{}') : {}
    reqStep.body = parseFields(fieldsToJson(bodyFields.value)).length ? JSON.parse(fieldsToJson(bodyFields.value) || '{}') : {}
  }
}

function buildStepsJson() {
  syncFieldsToStep()
  const clean = steps.value.map(s => {
    const c = { ...s }
    if (c.extract && !Object.keys(c.extract).length) delete c.extract
    if (c.headers && !Object.keys(c.headers).length) delete c.headers
    if (c.body && !Object.keys(c.body).length) delete c.body
    return c
  })
  return JSON.stringify(clean)
}

async function doSave() {
  if (!form.value.title.trim()) { ElMessage.warning('标题必填'); return }
  if (!steps.value.length) { ElMessage.warning('至少需要一个步骤'); return }
  saving.value = true
  syncToForm()
  try {
    const payload = { ...form.value, steps_json: buildStepsJson() }
    const { data } = await saveApiDefinition(payload)
    if (data.status) { ElMessage.success(isNew.value ? '创建成功' : '保存成功'); router.push({ path: '/cases', query: { tab: 'api', directory_id: form.value.directory_id } }) }
    else { ElMessage.error(data.message || '保存失败') }
  } catch (e) { ElMessage.error('保存失败') }
  saving.value = false
}
async function doDelete() {
  try { await ElMessageBox.confirm(`确定删除「${form.value.title}」？`, '删除确认', { type: 'warning' }); await deleteApiDefinition(caseId.value); ElMessage.success('已删除'); router.push({ path: '/cases', query: { tab: 'api' } }) }
  catch (e) { if (e !== 'cancel') ElMessage.error('删除失败') }
}
onMounted(load)
</script>

<template>
  <div class="doc-page wb-shell">
    <WorkbenchHeader :title="isNew ? '新建 API 用例' : '编辑 API 用例'" :subtitle="isNew ? (directoryName ? `目录: ${directoryName}` : '定义接口请求与预期响应') : `ID: ${caseId}`" icon="api" icon-gradient="linear-gradient(135deg,#f7cd67,#e85f5f)">
      <template #actions><el-button class="wb-btn wb-btn--sunset" size="small" @click="router.back()">返回列表</el-button></template>
    </WorkbenchHeader>
    <ErrorState v-if="error" :message="error" @retry="load" />
    <div v-else v-loading="loading" class="doc-body">
      <!-- Meta -->
      <div class="meta-bar">
        <div class="meta-bar__left"><input v-model="form.title" class="title-input" placeholder="用例标题（必填）" @keyup.enter="doSave" /><span class="meta-bar__id">{{ form.id || 'ID 自动生成' }}</span></div>
        <div class="meta-bar__right"><span class="meta-badge" :style="{ background: PRIORITY_COLORS[form.priority] || '#999' }">{{ form.priority }}</span><el-switch v-model="form.enabled" size="small" active-text="启用" /></div>
      </div>

      <!-- Info Card -->
      <section class="api-card api-card--info">
        <div class="api-card__head"><span class="api-card__pin"></span><span class="api-card__title">📋 用例信息</span></div>
        <div class="api-card__body info-grid">
          <div class="field"><label class="field__label">用例 ID</label><el-input v-model="form.id" :disabled="!isNew" size="small" placeholder="留空自动生成" /></div>
          <div class="field"><label class="field__label">描述</label><el-input v-model="form.description" size="small" placeholder="接口用途说明" /></div>
          <div class="field"><label class="field__label">前置条件</label><el-input v-model="form.precondition" size="small" placeholder="如：服务已启动、需携带有效 JWT" /></div>
        </div>
      </section>

      <!-- Data Module Card -->
      <section class="api-card api-card--data">
        <div class="api-card__head"><span class="api-card__pin"></span><span class="api-card__title">📊 数据模块</span><span class="api-card__badge">{{ allDataCols.length }} 列 · {{ dataRowCount }} 行</span></div>
        <div class="api-card__body">
          <div class="data-grid" v-if="allDataCols.length">
            <div class="data-grid__scroll">
              <table class="data-table">
                <thead>
                  <tr>
                    <th class="data-th data-th--input" v-for="c in inputCols" :key="'in-'+c.key">{{ c.key }}<small>input · {{ c.type }}</small></th>
                    <th class="data-th data-th--validate" v-for="(c, vi) in validateCols" :key="'val-'+vi">
                      <input v-model="c.key" placeholder="$.path.to.field" class="validate-key-input" @change="updateValidateColKey(vi, c.key)" /><small>validate</small>
                      <button class="validate-col-del" @click="removeValidateCol(vi)" title="删除校验列">×</button>
                    </th>
                    <th class="data-th data-th--act"></th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, ri) in dataRows" :key="ri">
                    <td class="data-td" v-for="c in inputCols" :key="'in-'+c.key">
                      <input :value="row[c.key]" @input="updateCell(c.key, ri, ($event.target).value)" :placeholder="c.type" class="data-cell" />
                    </td>
                    <td class="data-td" v-for="(c, vi) in validateCols" :key="'val-'+vi">
                      <input :value="row[c.key]" @input="updateCell(c.key, ri, ($event.target).value)" placeholder="预期值" class="data-cell data-cell--expect" />
                    </td>
                    <td class="data-td data-td--act"><button class="data-row__del" @click="removeDataRow(ri)" title="删除行">×</button></td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div class="data-actions">
              <button class="data-add-row" @click="addDataRow">+ 添加数据行</button>
              <button class="data-add-col" @click="addValidateCol">+ 添加校验列</button>
            </div>
          </div>
          <div v-else class="data-empty">
            <p>在「请求 Request」卡片中添加 Body 字段后，此处自动生成输入列。</p>
            <p>点击「+ 添加校验列」可添加响应 JSONPath 校验列。</p>
          </div>
        </div>
      </section>

      <!-- Steps Editor -->
      <section class="api-card api-card--steps">
        <div class="api-card__head"><span class="api-card__pin"></span><span class="api-card__title">📋 测试步骤</span><span class="api-card__badge">{{ steps.length }} 步</span></div>
        <div class="api-card__body">
          <div v-if="!steps.length" class="data-empty">
            <p>暂无步骤，点击下方按钮添加。</p>
          </div>
          <ApiStepEditor
            v-for="(s, i) in steps" :key="i"
            :model-value="s"
            :index="i"
            @update:model-value="steps[i] = $event; steps = [...steps]"
            @remove="removeStep(i)"
            @duplicate="duplicateStep(i)"
          />
          <div class="add-step-bar">
            <el-button v-for="t in STEP_TYPES" :key="t" size="small" @click="addStep(t)" class="add-step-btn">
              + {{ t }}
            </el-button>
          </div>
        </div>
      </section>

      <!-- Request Fields (for data module compat) -->
      <section class="api-card api-card--req">
        <div class="api-card__head"><span class="api-card__pin"></span><span class="api-card__title">📤 请求字段（数据模块参考）</span></div>
        <div class="api-card__body">
          <div class="field"><label class="field__label">Headers 字段</label>
            <div class="field-editor"><div class="field-row" v-for="(f,i) in headerFields" :key="'h'+i"><input v-model="f.key" placeholder="字段名" class="field-key" /><select v-model="f.type" class="field-type"><option v-for="t in TYPES" :key="t" :value="t">{{ t }}</option></select><button class="field-btn" @click="removeField(headerFields,i)">×</button></div><button class="field-add" @click="addField(headerFields)">+ 添加</button></div>
          </div>
          <div class="field"><label class="field__label">Body 字段</label>
            <div class="field-editor"><div class="field-row" v-for="(f,i) in bodyFields" :key="'b'+i"><input v-model="f.key" placeholder="字段名" class="field-key" /><select v-model="f.type" class="field-type"><option v-for="t in TYPES" :key="t" :value="t">{{ t }}</option></select><button class="field-btn" @click="removeField(bodyFields,i)">×</button></div><button class="field-add" @click="addField(bodyFields)">+ 添加</button></div>
          </div>
        </div>
      </section>

      <!-- Actions -->
      <div class="action-bar">
        <el-button v-if="!isNew" type="danger" plain @click="doDelete">🗑 删除用例</el-button>
        <div class="action-bar__spacer"></div>
        <el-button class="wb-btn" @click="router.back()">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doSave" class="save-btn">{{ isNew ? '创建用例' : '保存修改' }}</el-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.doc-page { display:flex;flex-direction:column;height:100%;overflow:hidden;background:radial-gradient(circle,var(--app-paper-dot) 0.8px,transparent 0.8px);background-size:14px 14px;background-color:var(--doodle-bg,#faf5ee); }
.doc-body { flex:1;min-height:0;overflow-y:auto;padding:16px 20px 24px;display:flex;flex-direction:column;gap:14px; }
.meta-bar { display:flex;align-items:center;justify-content:space-between;gap:16px;padding:10px 16px;background:#fff;border:2.5px solid var(--ink);border-radius:6px 10px 6px 10px;box-shadow:2px 3px 0 rgba(0,0,0,0.05);flex-shrink:0; }
.meta-bar__left { display:flex;align-items:center;gap:12px;flex:1;min-width:0; }
.meta-bar__id { font-size:11px;color:#999;font-family:var(--app-font-mono);flex-shrink:0; }
.meta-bar__right { display:flex;align-items:center;gap:10px;flex-shrink:0; }
.title-input { flex:1;min-width:0;border:none;border-bottom:2px dashed var(--app-border-light);font-size:var(--app-size-lg);font-weight:800;font-family:var(--app-font-display);color:var(--ink);background:transparent;outline:none;padding:2px 4px; }
.title-input:focus { border-bottom-color:var(--ink); }
.meta-badge { display:inline-block;padding:2px 10px;border-radius:8px;font-size:11px;font-weight:800;color:#fff; }
.cards-row { display:grid;grid-template-columns:1fr 1fr;gap:14px; }
@media (max-width:800px) { .cards-row { grid-template-columns:1fr; } }
.api-card { background:#fff;border:2.5px solid var(--ink);border-radius:6px 10px 6px 10px;box-shadow:2px 3px 0 rgba(0,0,0,0.05);position:relative;overflow:hidden; }
.api-card--req { transform:rotate(-0.2deg); }
.api-card--res { transform:rotate(0.2deg); }
.api-card--info { transform:rotate(-0.1deg); }
.api-card--data { transform:rotate(0.1deg); }
.api-card--assert { transform:rotate(-0.15deg); }
.api-card__head { padding:8px 14px;border-bottom:1.5px dashed var(--app-border-light);display:flex;align-items:center;gap:8px;background:rgba(247,205,103,0.08);position:relative; }
.api-card--res .api-card__head { background:rgba(136,157,240,0.08); }
.api-card--info .api-card__head { background:rgba(0,0,0,0.03); }
.api-card--data .api-card__head { background:rgba(111,186,44,0.06); }
.api-card--assert .api-card__head { background:rgba(200,180,255,0.08); }
.api-card__pin { position:absolute;top:6px;left:50%;transform:translateX(-50%);width:10px;height:10px;border-radius:50%;background:radial-gradient(circle,#e8e0d5 30%,#a09080 100%);box-shadow:0 1px 1px rgba(0,0,0,0.08);z-index:2; }
.api-card__title { font-size:13px;font-weight:800;color:var(--ink); }
.api-card__badge { font-size:11px;color:var(--app-ink-muted);margin-left:auto;font-weight:600; }
.api-card__body { padding:12px 14px;display:flex;flex-direction:column;gap:10px; }
.field { display:flex;flex-direction:column;gap:4px; }
.field__pair { display:flex;gap:8px;align-items:stretch; }
.field__label { font-size:11px;font-weight:700;color:var(--app-ink-muted);text-transform:uppercase;letter-spacing:0.03em; }
.method-select { width:100px;flex-shrink:0; }
.url-input { flex:1; }
.status-input { width:120px; }
.status-hint { font-size:12px;font-weight:700;margin-left:6px; }
.status-hint.status { color:#6fba2c; }
.status-hint.err { color:#e85f5f; }
.info-grid { display:grid;grid-template-columns:1fr 1fr;gap:10px; }
@media (max-width:600px) { .info-grid { grid-template-columns:1fr; } }

/* ── Field Editor ── */
.field-editor { display:flex;flex-direction:column;gap:4px; }
.field-row { display:flex;gap:4px;align-items:center; }
.field-key { flex:1;min-width:0;padding:3px 6px;border:1px solid var(--app-border-light);border-radius:4px;font-size:12px;font-family:var(--app-font-mono);outline:none; }
.field-key:focus { border-color:var(--ink); }
.field-type { width:80px;padding:3px 4px;border:1px solid var(--app-border-light);border-radius:4px;font-size:11px;outline:none;background:#fff; }
.field-btn { border:none;background:none;color:#e85f5f;font-size:16px;cursor:pointer;padding:0 4px;font-weight:700; }
.field-add { border:1.5px dashed var(--app-border-light);border-radius:6px;padding:4px 12px;font-size:11px;font-weight:700;color:var(--app-ink-muted);background:transparent;cursor:pointer; }
.field-add:hover { border-color:var(--ink);color:var(--ink); }

/* ── Data Module ── */
.data-grid__scroll { overflow-x:auto; }
.data-table { width:100%;border-collapse:collapse;font-size:12px; }
.data-th { background:rgba(111,186,44,0.08);padding:6px 8px;font-weight:700;color:var(--ink);text-align:left;white-space:nowrap;border-bottom:2px solid var(--ink); }
.data-th small { display:block;font-size:10px;color:var(--app-ink-muted);font-weight:400; }
.data-th--act { width:28px; }
.data-td { padding:2px 4px;border-bottom:1px solid var(--app-border-lighter); }
.data-td--act { width:28px;text-align:center; }
.data-cell { width:100%;padding:4px 6px;border:1px solid var(--app-border-lighter);border-radius:4px;font-size:12px;font-family:var(--app-font-mono);outline:none;min-width:90px; }
.data-cell:focus { border-color:var(--c-case); }
.data-row__del { border:none;background:none;color:#e85f5f;font-size:14px;cursor:pointer;font-weight:700; }
.data-th--input { background: rgba(247,205,103,0.12); }
.data-th--validate { background: rgba(136,157,240,0.12); position: relative; }
.validate-key-input { width: 100%; border: none; background: transparent; font-size: 12px; font-family: var(--app-font-mono); color: var(--ink); outline: none; padding: 0; font-weight: 700; }
.validate-key-input:focus { border-bottom: 1px dashed var(--ink); }
.validate-col-del { position: absolute; top: 2px; right: 2px; border: none; background: none; color: #e85f5f; font-size: 12px; cursor: pointer; font-weight: 700; }
.data-cell--expect { border-color: rgba(136,157,240,0.4); }
.data-add-row { border:1.5px dashed var(--c-case);border-radius:6px;padding:6px 16px;font-size:12px;font-weight:700;color:var(--c-case);background:transparent;cursor:pointer; }
.data-add-col { border:1.5px dashed #889df0;border-radius:6px;padding:6px 16px;font-size:12px;font-weight:700;color:#889df0;background:transparent;cursor:pointer; }
.data-actions { display: flex; gap: 8px; margin-top: 8px; }
.data-empty { text-align:center;padding:16px;color:var(--app-ink-muted);font-size:13px; }
.data-empty p { margin: 4px 0; }

/* ── Assertions ── */
.assert-list { display:flex;flex-direction:column;gap:6px; }
.assert-row { display:flex;gap:4px;align-items:center; }
.assert-path { flex:1;min-width:0;padding:4px 6px;border:1px solid var(--app-border-light);border-radius:4px;font-size:12px;font-family:var(--app-font-mono);outline:none; }
.assert-op { width:90px;padding:3px 4px;border:1px solid var(--app-border-light);border-radius:4px;font-size:11px;background:#fff;outline:none; }
.assert-expect { width:100px;padding:4px 6px;border:1px solid var(--app-border-light);border-radius:4px;font-size:12px;outline:none; }

.action-bar { display:flex;align-items:center;gap:10px;padding:12px 16px;flex-shrink:0; }
.action-bar__spacer { flex:1; }
.save-btn :deep(span) { font-weight:800; }
:deep(.el-loading-mask) { background:rgba(250,245,238,0.6);backdrop-filter:blur(2px); }
</style>
