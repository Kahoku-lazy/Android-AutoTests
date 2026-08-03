<script setup>
/**
 * ApiStepEditor — single API step form card.
 * Supports: api_request, api_assert, api_sleep, api_log.
 */
import { computed } from 'vue'

const props = defineProps({
  modelValue: { type: Object, required: true },
  index: { type: Number, required: true },
})

const emit = defineEmits(['update:modelValue', 'remove', 'duplicate'])

const step = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
const OP_OPTIONS = ['equals', 'contains', 'greater_than']

// ── Extract helpers ──
const extractPairs = computed({
  get: () => {
    const e = step.value.extract || {}
    return Object.entries(e).map(([k, v]) => ({ key: k, value: v }))
  },
  set: (pairs) => {
    const obj = {}
    pairs.forEach(p => { if (p.key) obj[p.key] = p.value })
    step.value = { ...step.value, extract: obj }
  },
})

function addExtractPair() {
  extractPairs.value = [...extractPairs.value, { key: '', value: '' }]
}
function removeExtractPair(i) {
  const arr = [...extractPairs.value]; arr.splice(i, 1)
  extractPairs.value = arr
}

// ── Assertion helpers ──
const assertions = computed({
  get: () => step.value.assertions || [],
  set: (v) => { step.value = { ...step.value, assertions: v } },
})

function addAssertion() {
  assertions.value = [...assertions.value, { path: '', op: 'equals', expect: '' }]
}
function removeAssertion(i) {
  const arr = [...assertions.value]; arr.splice(i, 1)
  assertions.value = arr
}

// ── Headers / Body helpers (JSON string <-> object) ──
function jsonStr(obj, fallback = '') {
  if (!obj || !Object.keys(obj).length) return fallback
  try { return JSON.stringify(obj, null, 2) } catch { return fallback }
}
function parseJson(str) {
  if (!str || !str.trim()) return {}
  try { const o = JSON.parse(str); return typeof o === 'object' && o ? o : {} } catch { return {} }
}
</script>

<template>
  <div class="api-step" :class="`api-step--${step.type}`">
    <div class="api-step__head">
      <span class="api-step__idx">{{ index + 1 }}</span>
      <select v-model="step.type" class="api-step__type">
        <option value="api_request">📤 api_request</option>
        <option value="api_assert">🔍 api_assert</option>
        <option value="api_sleep">⏱ api_sleep</option>
        <option value="api_log">📝 api_log</option>
      </select>
      <span class="api-step__desc">{{ step.description || step.url || '' }}</span>
      <div class="api-step__actions">
        <button class="act-btn" @click="emit('duplicate')" title="复制">⧉</button>
        <button class="act-btn act-btn--del" @click="emit('remove')" title="删除">×</button>
      </div>
    </div>

    <div class="api-step__body">
      <!-- ═══ api_request ═══ -->
      <template v-if="step.type === 'api_request'">
        <div class="field-row">
          <select v-model="step.method" class="method-sel">
            <option v-for="m in METHODS" :key="m" :value="m">{{ m }}</option>
          </select>
          <input v-model="step.url" class="url-inp" placeholder="https:// 或 /api/... 支持 {{var}}" />
        </div>
        <div class="kv-block">
          <label class="kv-label">Headers (JSON)</label>
          <textarea :value="jsonStr(step.headers)" @input="step.headers = parseJson($event.target.value)" rows="3" class="json-ta" placeholder='{"Authorization": "Bearer {{token}}"}'></textarea>
        </div>
        <div class="kv-block">
          <label class="kv-label">Body (JSON)</label>
          <textarea :value="jsonStr(step.body)" @input="step.body = parseJson($event.target.value)" rows="3" class="json-ta" placeholder='{"username": "admin"}'></textarea>
        </div>
        <div class="kv-block">
          <label class="kv-label">Extract 变量提取</label>
          <div class="extract-list">
            <div class="extract-row" v-for="(p, i) in extractPairs" :key="i">
              <input v-model="p.key" placeholder="变量名" class="extract-key" @change="extractPairs = [...extractPairs]" />
              <span class="extract-arrow">←</span>
              <input v-model="p.value" placeholder="$.data.token" class="extract-path" @change="extractPairs = [...extractPairs]" />
              <button class="kv-remove" @click="removeExtractPair(i)">×</button>
            </div>
          </div>
          <button class="kv-add" @click="addExtractPair">+ 添加提取规则</button>
        </div>
        <div class="field-row field-row--end">
          <label class="inline-label">预期状态码</label>
          <input v-model.number="step.expected_status" type="number" class="status-inp" min="100" max="599" />
          <input v-model="step.description" class="desc-inp" placeholder="步骤描述" />
        </div>
      </template>

      <!-- ═══ api_assert ═══ -->
      <template v-else-if="step.type === 'api_assert'">
        <div class="assert-list">
          <div class="assert-row" v-for="(a, i) in assertions" :key="i">
            <input v-model="a.path" placeholder="$.data.ok" class="a-path" />
            <select v-model="a.op" class="a-op"><option v-for="o in OP_OPTIONS" :key="o" :value="o">{{ o }}</option></select>
            <input v-model="a.expect" placeholder="期望值" class="a-expect" />
            <button class="kv-remove" @click="removeAssertion(i)">×</button>
          </div>
        </div>
        <button class="kv-add" @click="addAssertion">+ 添加断言</button>
        <div class="field-row field-row--end" style="margin-top:8px">
          <label class="inline-label">预期状态码</label>
          <input v-model.number="step.expected_status" type="number" class="status-inp" min="100" max="599" />
          <input v-model="step.description" class="desc-inp" placeholder="步骤描述" />
        </div>
      </template>

      <!-- ═══ api_sleep ═══ -->
      <template v-else-if="step.type === 'api_sleep'">
        <div class="field-row">
          <label class="inline-label">等待时间（秒）</label>
          <input v-model.number="step.timeout" type="number" class="timeout-inp" min="0" step="0.5" />
          <input v-model="step.description" class="desc-inp" placeholder="步骤描述" />
        </div>
      </template>

      <!-- ═══ api_log ═══ -->
      <template v-else-if="step.type === 'api_log'">
        <div class="field-row">
          <input v-model="step.value" class="desc-inp" style="flex:1" placeholder="日志内容" />
          <input v-model="step.description" class="desc-inp" style="flex:1" placeholder="步骤描述" />
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.api-step {
  background: #fff;
  border: 2px solid var(--app-border-light, #e0d8cc);
  border-radius: 6px 10px 6px 10px;
  margin-bottom: 8px;
  overflow: hidden;
}
.api-step--api_request { border-left: 3px solid #f7cd67; }
.api-step--api_assert  { border-left: 3px solid #889df0; }
.api-step--api_sleep  { border-left: 3px solid #b39ef3; }
.api-step--api_log    { border-left: 3px solid #6fba2c; }

.api-step__head {
  display: flex; align-items: center; gap: 8px;
  padding: 6px 10px; background: rgba(0,0,0,0.02);
  border-bottom: 1px dashed var(--app-border-lighter, #e8e0d5);
}
.api-step__idx {
  display: inline-flex; align-items: center; justify-content: center;
  width: 22px; height: 22px; border-radius: 50%;
  background: var(--ink, #2d2d2d); color: #fff;
  font-size: 11px; font-weight: 800; flex-shrink: 0;
}
.api-step__type {
  border: 1px solid var(--app-border-light, #e0d8cc);
  border-radius: 4px; padding: 2px 6px; font-size: 12px;
  background: #fff; outline: none; font-weight: 600;
}
.api-step__desc {
  flex: 1; font-size: 12px; color: #999; overflow: hidden;
  text-overflow: ellipsis; white-space: nowrap; min-width: 0;
}
.api-step__actions { display: flex; gap: 2px; flex-shrink: 0; }
.act-btn {
  border: none; background: none; font-size: 16px; cursor: pointer;
  padding: 0 4px; color: #999; font-weight: 700;
}
.act-btn:hover { color: var(--ink, #2d2d2d); }
.act-btn--del:hover { color: #e85f5f; }

.api-step__body { padding: 10px 12px; display: flex; flex-direction: column; gap: 8px; }

.field-row { display: flex; gap: 8px; align-items: center; }
.field-row--end { justify-content: flex-end; }

.method-sel { width: 90px; padding: 4px; border: 1px solid var(--app-border-light,#e0d8cc); border-radius: 4px; font-size: 12px; font-weight: 700; outline: none; }
.url-inp { flex: 1; padding: 4px 8px; border: 1px solid var(--app-border-light,#e0d8cc); border-radius: 4px; font-size: 12px; font-family: var(--app-font-mono); outline: none; }
.url-inp:focus { border-color: var(--ink); }

.kv-block { display: flex; flex-direction: column; gap: 4px; }
.kv-label { font-size: 10px; font-weight: 700; color: #999; text-transform: uppercase; letter-spacing: 0.05em; }
.json-ta {
  width: 100%; padding: 6px 8px; border: 1px solid var(--app-border-light,#e0d8cc);
  border-radius: 4px; font-size: 11px; font-family: var(--app-font-mono);
  resize: vertical; outline: none; line-height: 1.4;
}
.json-ta:focus { border-color: var(--ink); }

.extract-list { display: flex; flex-direction: column; gap: 4px; }
.extract-row { display: flex; gap: 4px; align-items: center; }
.extract-key { width: 100px; padding: 3px 6px; border: 1px solid var(--app-border-light,#e0d8cc); border-radius: 4px; font-size: 11px; font-family: var(--app-font-mono); outline: none; }
.extract-path { flex: 1; padding: 3px 6px; border: 1px solid var(--app-border-light,#e0d8cc); border-radius: 4px; font-size: 11px; font-family: var(--app-font-mono); outline: none; }
.extract-arrow { color: #999; font-size: 12px; flex-shrink: 0; }

.kv-remove { border: none; background: none; color: #e85f5f; font-size: 16px; cursor: pointer; padding: 0 4px; }
.kv-add { border: 1.5px dashed var(--app-border-light,#e0d8cc); border-radius: 6px; padding: 4px 12px; font-size: 11px; font-weight: 700; color: #999; background: transparent; cursor: pointer; align-self: flex-start; }
.kv-add:hover { border-color: var(--ink); color: var(--ink); }

.assert-list { display: flex; flex-direction: column; gap: 4px; }
.assert-row { display: flex; gap: 4px; align-items: center; }
.a-path { flex: 1; padding: 3px 6px; border: 1px solid var(--app-border-light,#e0d8cc); border-radius: 4px; font-size: 11px; font-family: var(--app-font-mono); outline: none; }
.a-op { width: 90px; padding: 3px 4px; border: 1px solid var(--app-border-light,#e0d8cc); border-radius: 4px; font-size: 11px; background: #fff; outline: none; }
.a-expect { width: 100px; padding: 3px 6px; border: 1px solid var(--app-border-light,#e0d8cc); border-radius: 4px; font-size: 11px; outline: none; }

.inline-label { font-size: 11px; font-weight: 600; color: #999; flex-shrink: 0; }
.status-inp { width: 70px; padding: 3px 6px; border: 1px solid var(--app-border-light,#e0d8cc); border-radius: 4px; font-size: 12px; font-family: var(--app-font-mono); outline: none; text-align: center; }
.desc-inp { flex: 1; padding: 3px 6px; border: 1px solid var(--app-border-light,#e0d8cc); border-radius: 4px; font-size: 12px; outline: none; }
.timeout-inp { width: 80px; padding: 3px 6px; border: 1px solid var(--app-border-light,#e0d8cc); border-radius: 4px; font-size: 12px; font-family: var(--app-font-mono); outline: none; text-align: center; }
</style>
