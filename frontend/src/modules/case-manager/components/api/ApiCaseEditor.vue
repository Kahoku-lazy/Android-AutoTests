<script setup>
/**
 * ApiCaseEditor — unified config_json editor for API test cases.
 *
 * Supports two formats (auto-detected):
 *   single — meta / request / cases[]   (read-only display for now)
 *   multi  — case_info / steps[] / test_data[] / validation[]
 */
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import WorkbenchHeader from '@/shared/components/WorkbenchHeader.vue'
import ErrorState from '@/shared/components/patterns/ErrorState.vue'
import CaseInfoPanel from './CaseInfoPanel.vue'
import StepListPanel from './StepListPanel.vue'
import TestDataPanel from './TestDataPanel.vue'
import ValidationPanel from './ValidationPanel.vue'
import { useApiConfigJson } from '../../composables/useApiConfigJson'
import { useCaseEditingSocket } from '../../composables/useCaseEditingSocket'
import { deleteApiDefinition } from '../../api/apiTesting'

const router = useRouter()
const route = useRoute()

const caseId = computed(() => route.params.id)
const isNew = computed(() => !caseId.value || caseId.value === 'new')
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const directoryName = ref('')

const { config, single, meta, format, load, save, dataColumns } = useApiConfigJson()

const stepCount = computed(() => config.steps.length)
const initialSnapshot = ref('')
const isDirty = computed(() => {
  if (!initialSnapshot.value) return false
  const current = JSON.stringify({
    format: format.value,
    config,
    single,
    meta: { ...meta },
  })
  return current !== initialSnapshot.value
})

function captureSnapshot() {
  initialSnapshot.value = JSON.stringify({
    format: format.value,
    config,
    single,
    meta: { ...meta },
  })
}

const METHOD_COLORS = {
  GET: '#6fba2c', POST: '#889df0', PUT: '#f7cd67', DELETE: '#e85f5f', PATCH: '#a78bfa',
}

// ── WebSocket: listen for remote updates (e.g. AI modifying the case) ──
useCaseEditingSocket(
  () => isNew.value ? null : caseId.value,
  () => {
    if (!caseId.value || isNew.value) return
    load(caseId.value).then(() => {
      captureSnapshot()
      ElMessage.info('此用例已被更新，已刷新为最新内容')
    }).catch(() => {})
  },
  {
    isDirty: () => isDirty.value,
    shouldIgnore: () => loading.value || saving.value,
  },
)

// ── Load ──
onMounted(async () => {
  if (isNew.value) {
    if (route.query.directory_id) {
      meta.directory_id = Number(route.query.directory_id)
    }
    if (route.query.dir_name) directoryName.value = route.query.dir_name
    captureSnapshot()
    return
  }
  loading.value = true
  error.value = ''
  try {
    await load(caseId.value)
    if (route.query.dir_name) {
      directoryName.value = route.query.dir_name
    }
    captureSnapshot()
  } catch (e) {
    error.value = e?.response?.data?.message || e?.message || '加载用例失败'
  } finally {
    loading.value = false
  }
})

function validateBeforeSave() {
  // Single format — read-only for now; block save
  if (format.value === 'single') {
    if (!single.meta?.title?.trim()) {
      ElMessage.warning('标题必填')
      return false
    }
    if (!String(single.request?.path || '').trim()) {
      ElMessage.warning('请求路径不能为空')
      return false
    }
    if (!single.cases.length) {
      ElMessage.warning('至少需要一条测试数据')
      return false
    }
    ElMessage.warning('单接口格式暂为只读，请在多步骤编辑器中修改')
    return false
  }
  // Multi format
  if (!config.case_info?.title?.trim()) {
    ElMessage.warning('标题必填')
    return false
  }
  if (!config.steps.length) {
    ElMessage.warning('至少需要一个测试步骤')
    return false
  }
  for (let i = 0; i < config.steps.length; i++) {
    const s = config.steps[i]
    if (!String(s.url || '').trim()) {
      ElMessage.warning(`步骤 ${i + 1} 的路径不能为空`)
      return false
    }
    for (let j = 0; j < (s.extract || []).length; j++) {
      const ex = s.extract[j]
      if (!String(ex.name || '').trim() || !String(ex.path || '').trim()) {
        ElMessage.warning(`步骤 ${i + 1} 的提取规则不完整（变量名与路径均必填）`)
        return false
      }
    }
  }
  return true
}

// ── Save ──
async function doSave() {
  if (!validateBeforeSave()) return
  saving.value = true
  try {
    const result = await save()
    const data = result && result.data
    if (data && data.status !== false) {
      ElMessage.success(isNew.value ? '创建成功' : '保存成功')
      router.push({
        path: '/cases',
        query: { tab: 'api', directory_id: meta.directory_id || undefined },
      })
    } else {
      ElMessage.error((data && data.message) || '保存失败')
    }
  } catch (e) {
    const status = e?.response?.status
    const msg = e?.response?.data?.message || e?.message || '保存失败'
    if (status === 409 && String(msg).includes('已被他人修改')) {
      ElMessageBox.alert(msg, '保存冲突', { confirmButtonText: '知道了', type: 'warning' })
    } else {
      ElMessage.error(msg)
    }
  } finally {
    saving.value = false
  }
}

const deleting = ref(false)

// ── Delete ──
async function doDelete() {
  if (deleting.value) return
  try {
    await ElMessageBox.confirm(
      `确定删除「${single.meta?.title || config.case_info?.title || caseId.value}」？`,
      '删除确认',
      { type: 'warning' },
    )
    deleting.value = true
    await deleteApiDefinition(caseId.value)
    ElMessage.success('已删除')
    router.push({ path: '/cases', query: { tab: 'api' } })
  } catch (e) {
    if (e !== 'cancel' && e !== 'close') ElMessage.error('删除失败')
  } finally {
    deleting.value = false
  }
}
</script>

<template>
  <div class="doc-page wb-shell">
    <WorkbenchHeader
      :title="isNew ? '新建 API 用例' : '编辑 API 用例'"
      :subtitle="isNew ? (directoryName ? `目录: ${directoryName}` : '定义接口请求、测试数据与校验规则') : `ID: ${caseId}`"
      icon="globe"
      icon-gradient="linear-gradient(135deg,#f7cd67,#e85f5f)"
    >
      <template #actions>
        <el-button class="wb-btn wb-btn--sunset" size="small" @click="router.back()">返回列表</el-button>
      </template>
    </WorkbenchHeader>

    <ErrorState v-if="error" :message="error" @retry="loading = true; error = ''; load(caseId).finally(() => loading = false)" />

    <div v-else v-loading="loading" class="doc-body">

      <!-- ═══ Single format ═══ -->
      <template v-if="format === 'single'">
        <!-- Meta summary -->
        <div class="single-panel">
          <div class="sp-head"><span class="sp-head__icon">📋</span> 用例概览</div>
          <div class="sp-body">
            <div class="sp-field">
              <span class="sp-label">标题</span>
              <span class="sp-val">{{ single.meta.title || '—' }}</span>
            </div>
            <div class="sp-field">
              <span class="sp-label">描述</span>
              <span class="sp-val">{{ single.meta.description || '—' }}</span>
            </div>
            <div class="sp-field">
              <span class="sp-label">BASE</span>
              <code class="sp-code">{{ single.meta.base_url || '—' }}</code>
            </div>
            <div class="sp-field">
              <span class="sp-label">鉴权</span>
              <span class="sp-val">{{ single.meta.auth?.type || 'none' }}</span>
            </div>
          </div>
        </div>

        <!-- Request summary -->
        <div class="single-panel">
          <div class="sp-head"><span class="sp-head__icon">📡</span> 请求定义</div>
          <div class="sp-body">
            <div class="sp-field">
              <span class="sp-label">方法</span>
              <span class="sp-badge" :style="{ background: METHOD_COLORS[single.request.method] || '#999' }">{{ single.request.method }}</span>
            </div>
            <div class="sp-field">
              <span class="sp-label">路径</span>
              <code class="sp-code">{{ single.request.path || '—' }}</code>
            </div>
            <div class="sp-field">
              <span class="sp-label">Headers</span>
              <span class="sp-val">{{ Object.keys(single.request.headers || {}).length }} 项</span>
            </div>
          </div>
        </div>

        <!-- Cases table -->
        <div class="single-panel single-panel--table">
          <div class="sp-head"><span class="sp-head__icon">📊</span> 测试用例 <span class="sp-head__count">{{ single.cases.length }} 条</span></div>
          <div class="cases-table-wrap">
            <table class="cases-table" v-if="single.cases.length">
              <thead>
                <tr>
                  <th>#</th>
                  <th>分类</th>
                  <th>场景</th>
                  <th>Body 概要</th>
                  <th>期望状态</th>
                  <th>Body Schema</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(c, ci) in single.cases" :key="c.id || ci">
                  <td class="ct-id">{{ c.id || `#${ci + 1}` }}</td>
                  <td><span class="ct-cat">{{ c.category || '—' }}</span></td>
                  <td>{{ c.scenario || '—' }}</td>
                  <td
                    class="ct-body-preview"
                    :title="JSON.stringify(c.input?.body || {})"
                  >{{ JSON.stringify(c.input?.body || {}).slice(0, 80) }}{{ JSON.stringify(c.input?.body || {}).length > 80 ? '…' : '' }}</td>
                  <td>
                    <span class="ct-status" :class="c.expect?.status === 200 ? 'ct-status--ok' : 'ct-status--err'">
                      {{ c.expect?.status || 0 }}
                    </span>
                  </td>
                  <td>
                    <template v-if="c.expect?.body_schema && Object.keys(c.expect.body_schema).length">
                      <span
                        class="ct-schema"
                        :title="JSON.stringify(c.expect.body_schema, null, 2)"
                      >
                        <template v-for="(val, key) in (c.expect.body_schema.properties || {})" :key="key">
                          <template v-if="val && typeof val === 'object' && 'const' in val">
                            <em class="ct-schema__key">{{ key }}</em>=<code class="ct-schema__val">{{ typeof val.const === 'string' && val.const.length > 24 ? val.const.slice(0, 24) + '…' : JSON.stringify(val.const) }}</code>
                          </template>
                        </template>
                        <template v-if="!Object.values(c.expect.body_schema.properties || {}).some((v) => v && typeof v === 'object' && 'const' in v)">
                          {{ (c.expect.body_schema.required || Object.keys(c.expect.body_schema.properties || {})).slice(0, 4).join(', ') }}<template v-if="(c.expect.body_schema.required || Object.keys(c.expect.body_schema.properties || {})).length > 4">…</template>
                        </template>
                      </span>
                    </template>
                    <span v-else style="color:var(--app-ink-muted)">—</span>
                  </td>
                </tr>
              </tbody>
            </table>
            <div v-else class="sp-empty">暂无测试用例数据</div>
          </div>
        </div>
      </template>

      <!-- ═══ Multi format (original) ═══ -->
      <template v-else>
        <!-- ① Case Info -->
        <CaseInfoPanel v-model="config.case_info" />

        <!-- ② Steps -->
        <StepListPanel v-model="config.steps" />

        <!-- ③ Test Data -->
        <TestDataPanel
          v-model="config.test_data"
          :data-columns="dataColumns"
          :step-count="stepCount"
        />

        <!-- ④ Validation -->
        <ValidationPanel
          v-model="config.validation"
          :step-count="stepCount"
        />
      </template>

      <!-- Action bar (shared) -->
      <div class="action-bar">
        <el-button v-if="!isNew" type="danger" plain @click="doDelete">🗑 删除用例</el-button>
        <div class="action-bar__spacer"></div>
        <el-button class="wb-btn" @click="router.back()">取消</el-button>
        <el-button
          v-if="format !== 'single'"
          type="primary"
          :loading="saving"
          class="save-btn"
          @click="doSave"
        >
          {{ isNew ? '创建用例' : '保存修改' }}
        </el-button>
        <el-tag v-else type="info" effect="plain">单接口格式只读</el-tag>
      </div>
    </div>
  </div>
</template>

<style scoped>
.doc-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: radial-gradient(circle, var(--app-paper-dot) 0.8px, transparent 0.8px);
  background-size: 14px 14px;
  background-color: var(--doodle-bg, #faf5ee);
}
.doc-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 16px 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.action-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 0;
  flex-shrink: 0;
}
.action-bar__spacer { flex: 1; }
.save-btn :deep(span) { font-weight: 800; }
:deep(.el-loading-mask) { background: rgba(250, 245, 238, 0.6); }

/* ── Single format panels ── */
.single-panel {
  background: var(--app-paper, #fff);
  border-radius: 10px;
  border: 1px solid var(--app-border-tertiary, #e8e3db);
}
/* Table panel: fixed height with internal scroll so sticky th works */
.single-panel--table {
  display: flex;
  flex-direction: column;
  max-height: 62vh;
  overflow: hidden; /* clip here IS intentional — table scrolls in .cases-table-wrap */
}
.single-panel--table .sp-head {
  flex-shrink: 0;
}
.single-panel--table .cases-table-wrap {
  flex: 1;
  overflow-y: auto;
  overflow-x: visible;
  min-height: 0;
}
.sp-head {
  display: flex; align-items: center; gap: 6px;
  padding: 10px 14px;
  font-size: var(--app-size-sm); font-weight: 800; color: var(--ink);
  background: var(--app-bg-secondary, #f8f6f1);
  border-bottom: 1px solid var(--app-border-tertiary, #e8e3db);
}
.sp-head__icon { font-size:var(--app-size-sm); }
.sp-head__count { font-weight: 400; font-size: var(--app-size-xs); color: var(--app-ink-muted); margin-left: auto; }
.sp-body { padding: 12px 14px; display: flex; flex-direction: column; gap: 8px; }
.sp-field { display: flex; align-items: center; gap: 8px; }
.sp-label {
  font-size: var(--app-size-xs); font-weight: 700; color: var(--app-ink-muted);
  text-transform: uppercase; letter-spacing: 0.03em; min-width: 64px; flex-shrink: 0;
}
.sp-val { font-size: var(--app-size-sm); font-weight: 600; color: var(--ink); }
.sp-code {
  font-family: var(--app-font-mono); font-size: var(--app-size-xs);
  color: var(--app-accent-purple-dark); word-break: break-all;
}
.sp-badge {
  display: inline-block; padding: 2px 10px; border-radius: 8px;
  font-size: var(--app-size-xs); font-weight: 800; color: var(--app-bg-card);
}
.sp-empty { padding: 20px 14px; text-align: center; color: var(--app-ink-muted); font-size: var(--app-size-sm); }

/* ── Cases table ── */
.cases-table-wrap {
  /* no overflow here — handled by .single-panel--table */
}
.cases-table {
  width: 100%; border-collapse: collapse;
  font-size: var(--app-size-sm);
}
.cases-table th {
  text-align: left; padding: 8px 10px;
  font-size: var(--app-size-xs); font-weight: 700;
  color: var(--app-ink-muted); text-transform: uppercase; letter-spacing: 0.03em;
  background: var(--app-bg-secondary, #f8f6f1);
  border-bottom: 2px solid var(--app-border-tertiary, #e8e3db);
  position: sticky; top: 0; z-index: 1;
}
.cases-table td {
  padding: 8px 10px; border-bottom: 1px solid var(--app-border-tertiary, #e8e3db);
  vertical-align: middle;
}
.cases-table tbody tr:nth-child(even) td {
  background: var(--app-bg-secondary, #f8f6f1);
}
.ct-id { font-family: var(--app-font-mono); font-size: var(--app-size-xs); color: var(--app-ink-muted); white-space: nowrap; }
.ct-cat {
  display: inline-block; padding: 1px 8px; border-radius: 4px;
  background: var(--app-accent-purple-light, #ede9fe);
  color: var(--app-accent-purple-dark, #6d28d9);
  font-size: var(--app-size-xs); font-weight: 600; white-space: nowrap;
}
.ct-body-preview { font-family: var(--app-font-mono); font-size: var(--app-size-xs); color: var(--app-ink-muted); max-width: 280px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ct-status {
  display: inline-block; padding: 1px 8px; border-radius: 4px;
  font-family: var(--app-font-mono); font-size: var(--app-size-xs); font-weight: 700;
}
.ct-status--ok { background: #d1fae5; color: #065f46; }
.ct-status--err { background: #fee2e2; color: #991b1b; }
.ct-schema {
  display: inline-flex; flex-wrap: wrap; align-items: center; gap: 2px 4px;
  padding: 2px 6px; border-radius: 4px;
  background: var(--app-bg-secondary, #f8f6f1);
  font-family: var(--app-font-mono); font-size: var(--app-size-xs);
  max-width: 220px; line-height: 1.5;
}
.ct-schema__key {
  font-style: normal; font-weight: 700; color: var(--app-accent-purple-dark);
}
.ct-schema__val {
  font-family: var(--app-font-mono); font-size: var(--app-size-xs);
  background: rgba(0,0,0,0.06); padding: 0 3px; border-radius: 2px;
  color: var(--ink);
  margin-right: 5px;
}
</style>
