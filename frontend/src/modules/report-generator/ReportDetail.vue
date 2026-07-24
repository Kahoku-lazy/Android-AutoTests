<script setup>

import AppCard from "@/shared/components/AppCard.vue";
import AppTabs from "@/shared/components/AppTabs.vue";
import AppTable from "@/shared/components/AppTable.vue";
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { animate, stagger } from 'animejs'
import PageHeader from '@/shared/components/PageHeader.vue'
import { getRunReport, statusLabel, statusBadgeClass, iterBadgeClass, formatTime } from './api.js'

const route = useRoute()
const router = useRouter()
const runId = computed(() => String(route.params.runId))

const report = ref(null)
const loading = ref(false)
const activeTab = ref('cases')
const expandedFailCases = ref(new Set())
const expandedStepGroups = ref(new Set())

const PAGE_SIZE_OPTIONS = [10, 20, 50, 100]
const TABLE_HEADER_HEIGHT = 45
const TABLE_ROW_HEIGHT = 41
const pageSize = ref(20)
const currentPage = ref(1)

onMounted(() => loadReport())
watch(runId, () => {
  currentPage.value = 1
  expandedFailCases.value = new Set()
  expandedStepGroups.value = new Set()
  loadReport()
})

async function loadReport() {
  loading.value = true
  try {
    const { data } = await getRunReport(runId.value)
    if (data.ok) report.value = data.run
  } catch (_) {}
  loading.value = false
  await nextTick()
  animate('.detail-table tbody tr', { opacity: [0, 1], translateY: [12, 0], delay: stagger(30), duration: 350, ease: 'outCubic' })
}

// ── AppTabs ──
const tabs = computed(() => {
  const items = [{ key: 'cases', label: '用例执行明细' }]
  const failCount = failedSteps.value.length || failedCases.value.length
  if (failCount > 0) items.push({ key: 'failures', label: `失败分析 (${failCount})` })
  return items
})

// ── Computed ──
const runMeta = computed(() => report.value || {})

const allCases = computed(() => {
  if (!report.value) return []
  return report.value.cases || []
})

const totalPages = computed(() => Math.max(1, Math.ceil(allCases.value.length / pageSize.value)))

const pagedCases = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return allCases.value.slice(start, start + pageSize.value)
})

const tableScrollY = computed(() => TABLE_HEADER_HEIGHT + pageSize.value * TABLE_ROW_HEIGHT)

const failedCases = computed(() => allCases.value.filter(c => c.fail > 0))

// TaskAppCard failed_steps — detailed step-level failure records
const failedSteps = computed(() => {
  if (!report.value) return []
  return report.value.task_failed_steps || []
})

const failedStepsByCase = computed(() => {
  const caseIdByTitle = Object.fromEntries(
    allCases.value.map(c => [c.case_title, c.case_id]),
  )
  const groups = new Map()

  for (const fs of failedSteps.value) {
    const caseTitle = fs.caseTitle || fs.caseId || '未知用例'
    const caseId = fs.caseId || caseIdByTitle[caseTitle] || caseTitle
    if (!groups.has(caseId)) {
      groups.set(caseId, {
        key: caseId,
        caseId,
        caseTitle,
        steps: [],
      })
    }
    groups.get(caseId).steps.push(fs)
  }

  return [...groups.values()]
    .map(group => ({
      ...group,
      steps: [...group.steps].sort(
        (a, b) => a.iteration - b.iteration || a.stepIndex - b.stepIndex,
      ),
    }))
    .sort((a, b) => a.caseTitle.localeCompare(b.caseTitle, 'zh-CN'))
})

const kpiPassRate = computed(() => {
  if (!report.value) return 0
  return report.value.pass_rate || 0
})

function goBack() { router.push('/reports') }

function setPageSize(size) {
  pageSize.value = size
  currentPage.value = 1
}

function goPage(page) {
  currentPage.value = Math.min(Math.max(1, page), totalPages.value)
}

function toggleFailExpand(caseId) {
  const s = new Set(expandedFailCases.value)
  if (s.has(caseId)) s.delete(caseId)
  else s.add(caseId)
  expandedFailCases.value = s
}

function toggleStepGroupExpand(groupKey) {
  const s = new Set(expandedStepGroups.value)
  if (s.has(groupKey)) s.delete(groupKey)
  else s.add(groupKey)
  expandedStepGroups.value = s
}

const FAIL_CARD_PALETTE = ['app-red', 'warm-peach-pink', 'app-pink', 'purple']

function failCardColor(index) {
  return FAIL_CARD_PALETTE[index % FAIL_CARD_PALETTE.length]
}

function failedIterations(c) {
  return (c.iterations || []).filter(i => i.result !== 'pass')
}

function failStepsForCase(c) {
  const group = failedStepsByCase.value.find(
    g => g.caseId === c.case_id || g.caseTitle === c.case_title,
  )
  return group?.steps || []
}

// ── TaskAppCard outcome helpers ──
function outcomeLabel(outcome) {
  const map = { completed: '已完成', stopped: '已停止', interrupted: '运行中断', error: '异常终止' }
  return map[outcome] || outcome || '—'
}
function outcomeBadgeClass(outcome) {
  if (outcome === 'completed') return 'badge-pass'
  if (outcome === 'stopped' || outcome === 'interrupted') return 'badge-stopped'
  if (outcome === 'error') return 'badge-fail'
  return 'badge-stopped'
}

</script>

<template>
  <div class="doc-page">
    <!-- Header -->
    <PageHeader
      title="测试执行报告"
      :subtitle="`Run: ${runMeta.run_id || '加载中...'}`"
      color="app-yellow"
    />

    <div class="doc-body">
      <!-- Back button + Run meta -->
      <div class="top-bar">
        <el-button size="small" @click="goBack">← 返回列表</el-button>
        <div class="run-meta">
          <span v-if="runMeta.device_serial">📱 {{ runMeta.device_serial }}</span>
          <span v-if="runMeta.loop_count">🔄 {{ runMeta.loop_count }} 轮</span>
          <span v-if="runMeta.duration">⏱ {{ runMeta.duration }}</span>
          <span :class="statusBadgeClass(runMeta.status)" class="badge">{{ statusLabel(runMeta.status) }}</span>
        </div>
      </div>

      <!-- KPI Cards -->
      <div class="kpi-row">
        <div class="kpi-card">
          <div class="kpi-accent accent-teal"></div>
          <div class="kpi-value">{{ runMeta.case_count || 0 }}</div>
          <div class="kpi-label">执行用例</div>
          <div class="kpi-sub">{{ runMeta.loop_count || 0 }} 轮 × {{ runMeta.case_count || 0 }} 用例 = {{ runMeta.total_iterations || 0 }} 次迭代</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-accent accent-green"></div>
          <div class="kpi-value num-pass">{{ runMeta.total_pass || 0 }}</div>
          <div class="kpi-label">✅ 通过</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-accent accent-red"></div>
          <div class="kpi-value num-fail">{{ runMeta.total_fail || 0 }}</div>
          <div class="kpi-label">❌ 失败</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-accent accent-yellow"></div>
          <div class="kpi-value" :class="kpiPassRate >= 95 ? 'num-pass' : kpiPassRate >= 80 ? 'num-warn' : 'num-fail'">{{ kpiPassRate }}%</div>
          <div class="kpi-label">📊 通过率</div>
        </div>
      </div>

      <!-- TaskAppCard Metadata (conditional) -->
      <div v-if="runMeta.client_task_id" class="task-meta-bar">
        <div class="task-meta-item">
          <span class="meta-label">📋 任务名称</span>
          <span class="meta-value">{{ runMeta.task_name || '—' }}</span>
        </div>
        <div class="task-meta-item">
          <span class="meta-label">👤 创建人</span>
          <span class="meta-value">{{ runMeta.task_creator || '—' }}</span>
        </div>
        <div class="task-meta-item">
          <span class="meta-label">🏷 执行结果</span>
          <span class="badge" :class="outcomeBadgeClass(runMeta.task_outcome)">
            {{ outcomeLabel(runMeta.task_outcome) }}
          </span>
        </div>
        <div v-if="runMeta.task_conclusion" class="task-meta-item full-width">
          <span class="meta-label">📝 结论</span>
          <span class="meta-value conclusion-text">{{ runMeta.task_conclusion }}</span>
        </div>
      </div>

      <!-- AppTabs -->
      <AppTabs
        class="detail-tabs"
        :items="tabs"
        v-model="activeTab"
        :leaf-animation="true"
        :shadow="true"
      >
        <!-- ═══ TAB: 用例执行明细 ═══ -->
        <template #cases>
          <AppCard color="brown" class="table-card">
            <div class="table-toolbar">
              <div class="page-size-control">
                <span class="toolbar-label">显示行数</span>
                <div class="page-size-btns">
                  <button
                    v-for="n in PAGE_SIZE_OPTIONS"
                    :key="n"
                    type="button"
                    class="page-size-btn"
                    :class="{ active: pageSize === n }"
                    @click="setPageSize(n)"
                  >{{ n }}</button>
                </div>
              </div>
              <div v-if="allCases.length > 0" class="table-toolbar-right">
                <span class="page-info">
                  第 {{ currentPage }} / {{ totalPages }} 页 · 共 {{ allCases.length }} 条
                </span>
                <div v-if="totalPages > 1" class="page-nav">
                  <el-button size="small" :disabled="currentPage <= 1" @click="goPage(currentPage - 1)">上一页</el-button>
                  <el-button size="small" :disabled="currentPage >= totalPages" @click="goPage(currentPage + 1)">下一页</el-button>
                </div>
              </div>
            </div>
            <AppTable
              :columns="[
                { title: '用例ID', dataIndex: 'case_id', width: '160px' },
                { title: '用例名称', dataIndex: 'case_title' },
                { title: '计划', dataIndex: 'planned', width: '60px', align: 'center' },
                { title: '实际', dataIndex: 'actual', width: '60px', align: 'center' },
                { title: '✅', dataIndex: 'pass', width: '50px', align: 'center' },
                { title: '❌', dataIndex: 'fail', width: '50px', align: 'center' },
                { title: '成功率', dataIndex: 'rate_bar', width: '150px' },
                { title: '状态', dataIndex: 'status_badge', width: '80px', align: 'center' },
              ]"
              :data-source="pagedCases"
              row-key="case_id"
              :striped="true"
              :loading="loading"
              :scroll="{ y: tableScrollY }"
              empty-text="暂无用例数据"
              class="detail-table"
            >
              <!-- Case ID -->
              <template #cell-case_id="{ record }">
                <code class="mono">{{ record.case_id }}</code>
              </template>

              <!-- Pass green -->
              <template #cell-pass="{ record }">
                <span class="num-pass">{{ record.pass }}</span>
              </template>

              <!-- Fail red -->
              <template #cell-fail="{ record }">
                <span v-if="record.fail > 0" class="num-fail">{{ record.fail }}</span>
                <span v-else>0</span>
              </template>

              <!-- Rate bar -->
              <template #cell-rate_bar="{ record }">
                <div class="rate-cell">
                  <div class="progress-bar">
                    <div class="p-pass" :style="{ width: record.rate + '%' }"></div>
                    <div v-if="record.fail > 0" class="p-fail" :style="{ width: (100 - record.rate) + '%' }"></div>
                  </div>
                  <span class="rate-text" :class="{ 'rate-ok': record.rate >= 95, 'rate-warn': record.rate >= 80 && record.rate < 95, 'rate-bad': record.rate < 80 }">{{ record.rate }}%</span>
                </div>
              </template>

              <!-- Status badge -->
              <template #cell-status_badge="{ record }">
                <span :class="record.fail > 0 ? 'badge badge-fail' : 'badge badge-pass'">
                  {{ record.fail > 0 ? 'FAIL' : 'PASS' }}
                </span>
              </template>
            </AppTable>
          </AppCard>
        </template>

        <!-- ═══ TAB: 失败分析 ═══ -->
        <template v-if="failedCases.length > 0 || failedSteps.length > 0" #failures>
          <!-- Step-level failures (from TaskCard.failed_steps) -->
          <div v-if="failedStepsByCase.length > 0" class="section-block">
            <h3 class="sec-title">
              🔍 步骤级失败详情
              <span class="sec-badge" style="background:#e85f5f;">{{ failedSteps.length }} 条</span>
              <span class="sec-badge sec-badge--muted">{{ failedStepsByCase.length }} 用例</span>
            </h3>
            <p class="sec-sub">按用例标题分类，点击展开查看具体失败步骤</p>
            <div v-for="(group, idx) in failedStepsByCase" :key="'fsg-' + group.key" class="fail-card">
              <AppCard :color="failCardColor(idx)">
                <div
                  class="fail-card-header fail-card-header--clickable"
                  role="button"
                  tabindex="0"
                  @click="toggleStepGroupExpand(group.key)"
                  @keyup.enter="toggleStepGroupExpand(group.key)"
                >
                  <span class="expand-icon" :class="{ open: expandedStepGroups.has(group.key) }">▶</span>
                  <span class="badge badge-fail">FAIL</span>
                  <div class="fail-case-title-wrap">
                    <strong class="fail-case-title">{{ group.caseTitle }}</strong>
                    <code v-if="group.caseId && group.caseId !== group.caseTitle" class="fail-case-id">{{ group.caseId }}</code>
                  </div>
                  <span class="fail-card-meta">{{ group.steps.length }} 条步骤失败</span>
                  <span class="fail-expand-hint">
                    {{ expandedStepGroups.has(group.key) ? '收起' : `展开 ${group.steps.length} 条` }}
                  </span>
                </div>

                <div v-if="expandedStepGroups.has(group.key)" class="expand-panel">
                  <div class="expand-header">{{ group.caseTitle }} — 步骤失败明细</div>
                  <div
                    v-for="(fs, i) in group.steps"
                    :key="'fs-' + group.key + '-' + i"
                    class="fail-step-row"
                  >
                    <div class="fail-step-row__head">
                      <span class="badge badge-fail">FAIL</span>
                      <span class="fail-step-row__meta">
                        第 {{ fs.iteration }} 轮 · 步骤 {{ fs.stepIndex + 1 }} · {{ fs.stepType }}
                      </span>
                    </div>
                    <div class="fail-detail-row fail-detail-row--nested">
                      <div class="fail-detail-item">
                        <span class="fd-label">步骤描述</span>
                        <span class="fd-value">{{ fs.description || '—' }}</span>
                      </div>
                      <div class="fail-detail-item">
                        <span class="fd-label">失败原因</span>
                        <span class="fd-value fd-error">{{ fs.result || '未知错误' }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </AppCard>
            </div>
          </div>

          <!-- Iteration-level failures (from TestResult) -->
          <div v-if="failedCases.length > 0">
            <h3 class="sec-title" :style="failedSteps.length > 0 ? { marginTop: '16px' } : undefined">
              📋 迭代失败汇总
              <span class="sec-badge" style="background:#e85f5f;">{{ failedCases.length }} 用例</span>
            </h3>
            <p class="sec-sub">点击用例展开查看迭代失败详情</p>
            <div v-for="(c, idx) in failedCases" :key="'fail-' + c.case_id" class="fail-card">
              <AppCard :color="failCardColor(idx)">
                <div
                  class="fail-card-header fail-card-header--clickable"
                  role="button"
                  tabindex="0"
                  @click="toggleFailExpand(c.case_id)"
                  @keyup.enter="toggleFailExpand(c.case_id)"
                >
                  <span class="expand-icon" :class="{ open: expandedFailCases.has(c.case_id) }">▶</span>
                  <span class="badge badge-fail">FAIL</span>
                  <strong>{{ c.case_title }}</strong>
                  <span class="fail-card-meta">{{ c.fail }}/{{ c.actual }} 次失败 · 成功率 {{ c.rate }}%</span>
                  <span class="fail-expand-hint">
                    {{ expandedFailCases.has(c.case_id) ? '收起' : `展开 ${failedIterations(c).length || failStepsForCase(c).length || c.fail} 条失败` }}
                  </span>
                </div>

                <div v-if="expandedFailCases.has(c.case_id)" class="expand-panel">
                  <div class="expand-header">{{ c.case_title }} — 迭代失败详情</div>

                  <table v-if="failedIterations(c).length > 0" class="mini-table">
                    <thead><tr>
                      <th>迭代</th><th>结果</th><th>耗时</th><th>详情</th>
                    </tr></thead>
                    <tbody>
                      <tr v-for="it in failedIterations(c)" :key="it.iteration" class="row-fail">
                        <td>#{{ it.iteration }}</td>
                        <td><span class="badge" :class="iterBadgeClass(it.result)">{{ it.result === 'pass' ? 'PASS' : 'FAIL' }}</span></td>
                        <td>{{ it.duration_ms ? (it.duration_ms / 1000).toFixed(1) + 's' : '—' }}</td>
                        <td class="fail-detail-text">{{ it.detail || '无详情' }}</td>
                      </tr>
                    </tbody>
                  </table>

                  <div v-else-if="failStepsForCase(c).length > 0" class="fail-step-fallback">
                    <p class="fail-step-fallback__title">步骤级失败记录（迭代明细未持久化）</p>
                    <div v-for="(fs, i) in failStepsForCase(c)" :key="'fsc-' + c.case_id + '-' + i" class="fail-step-row">
                      <span class="fail-step-row__meta">第 {{ fs.iteration }} 轮 · 步骤 {{ fs.stepIndex + 1 }} · {{ fs.stepType }}</span>
                      <span class="fail-step-row__desc">{{ fs.description || '—' }}</span>
                      <span class="fail-step-row__error">{{ fs.result || '未知错误' }}</span>
                    </div>
                  </div>

                  <div v-else class="fail-no-iterations">
                    迭代详情暂不可用（TestResult 未持久化），请查看上方步骤级失败详情
                  </div>
                </div>
              </AppCard>
            </div>
          </div>
        </template>

      </AppTabs>
    </div>
  </div>
</template>

<style scoped>
.doc-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  overflow-x: hidden;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}

.doc-page :deep(.doc-hero) {
  flex-shrink: 0;
}

.doc-body {
  flex: 0 0 auto;
  min-height: auto;
  display: flex;
  flex-direction: column;
  overflow: visible;
}

.detail-tabs {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
}

.detail-tabs :deep(.el-tabs) {
  display: flex;
  flex-direction: column;
  overflow: visible;
}

/* ── Top bar ── */
.top-bar { display: flex; align-items: center; gap: 16px; margin-bottom: 20px; flex-wrap: wrap; flex-shrink: 0; }
.run-meta { display: flex; align-items: center; gap: 12px; font-size: 13px; color: #8a7b66; flex-wrap: wrap; }

/* ── KPI Cards ── */
.kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 20px; flex-shrink: 0; }
.kpi-card {
  background: rgb(247,243,223); border-radius: 18px; padding: 20px 24px;
  border: 1.5px solid #c4b89e; position: relative; overflow: hidden;
  transition: transform 0.25s cubic-bezier(0.4,0,0.2,1);
}
.kpi-card:hover { transform: translateY(-2px); }
.kpi-accent { position: absolute; left: 0; top: 0; bottom: 0; width: 5px; border-radius: 0 3px 3px 0; }
.accent-teal { background: #19c8b9; }
.accent-green { background: var(--c-workflow); }
.accent-red { background: #e05a5a; }
.accent-yellow { background: #f5c31c; }
.kpi-value { font-size: 32px; font-weight: 900; color: #794f27; line-height: 1.1; }
.kpi-label { font-size: 12px; color: #9f927d; margin-top: 4px; font-weight: 600; }
.kpi-sub { font-size: 11px; color: #8a7b66; margin-top: 2px; }
.num-pass { color: var(--c-workflow); }
.num-fail { color: #e05a5a; }
.num-warn { color: #dba90e; }

/* ── TaskAppCard metadata bar ── */
.task-meta-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 24px;
  padding: 14px 20px;
  background: linear-gradient(135deg, #fef9ef 0%, #fdf0d5 100%);
  border-radius: 14px;
  border: 1px solid rgba(139,115,85,0.1);
  margin-bottom: 16px;
  flex-shrink: 0;
}
.task-meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}
.task-meta-item.full-width {
  flex-basis: 100%;
}
.meta-label {
  color: #9f927d;
  font-weight: 500;
  white-space: nowrap;
}
.meta-value {
  color: #4a3a28;
  font-weight: 600;
}
.conclusion-text {
  line-height: 1.5;
  font-style: italic;
}

/* ── AppTabs ── */
.detail-tabs :deep(.el-tabs__content) {
  overflow: visible;
  display: block;
  padding-top: 16px;
}

.detail-tabs :deep(.el-tabs__inner) {
  min-height: min-content;
}

/* ── AppTable card ── */
.table-card { overflow: hidden; }
.table-card :deep(.el-card__body) { padding: 0; border-radius: 14px; overflow: hidden; }

.table-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(139, 115, 85, 0.1);
  background: rgba(139, 115, 85, 0.03);
}
.page-size-control { display: flex; align-items: center; gap: 10px; }
.toolbar-label { font-size: 12px; font-weight: 700; color: #8a7b66; white-space: nowrap; }
.page-size-btns { display: flex; gap: 6px; }
.page-size-btn {
  min-width: 40px;
  padding: 5px 10px;
  border-radius: 8px;
  border: 1.5px solid rgba(139, 115, 85, 0.2);
  background: #f7f3df;
  color: #6b5b48;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
}
.page-size-btn:hover { border-color: #19c8b9; color: #19c8b9; }
.page-size-btn.active {
  background: rgba(25, 200, 185, 0.12);
  border-color: #19c8b9;
  color: #0f9a8e;
}
.table-toolbar-right { display: flex; align-items: center; gap: 12px; margin-left: auto; flex-wrap: wrap; }
.page-info { font-size: 12px; color: #8a7b66; font-weight: 600; white-space: nowrap; }
.page-nav { display: flex; gap: 8px; }

/* ── AppTable styles ── */
.detail-table { width: 100%; }
.detail-table :deep(table) { width: 100%; border-collapse: collapse; }
.detail-table :deep(th) {
  font-size: 12px; font-weight: 700; color: #6b5b48; padding: 12px 14px;
  text-align: left; background: rgba(139,115,85,0.06);
  border-bottom: 2px solid rgba(139,115,85,0.12);
  text-transform: uppercase; letter-spacing: 0.3px; white-space: nowrap;
}
.detail-table :deep(td) {
  padding: 10px 14px; font-size: 13px; color: #4a3a28;
  border-bottom: 1px dashed rgba(196,184,158,0.4); vertical-align: middle;
}
.detail-table :deep(tr:hover td) { background: rgba(25,200,185,0.04); }
.detail-table :deep(tr:last-child td) { border-bottom: none; }

/* ── Misc ── */
.mono { font-family: 'SF Mono','Fira Code','Cascadia Code',Consolas,monospace; font-size: 11px; font-weight: 600; background: rgba(139,115,85,0.06); padding: 2px 6px; border-radius: 4px; }

/* ── Rate cell ── */
.rate-cell { display: flex; align-items: center; gap: 8px; }
.progress-bar { display: flex; height: 7px; border-radius: var(--app-radius-pill); overflow: hidden; background: #f0ece2; flex: 1; max-width: 90px; }
.p-pass { background: var(--c-workflow); transition: width 0.5s ease; border-radius: var(--app-radius-pill); }
.p-fail { background: #e05a5a; transition: width 0.5s ease; border-radius: var(--app-radius-pill); }
.rate-text { font-weight: 700; font-size: 12px; min-width: 38px; text-align: right; }
.rate-ok { color: var(--c-workflow); }
.rate-warn { color: #dba90e; }
.rate-bad { color: #e05a5a; }

/* ── Badges ── */
.badge { display: inline-flex; align-items: center; padding: 3px 10px; border-radius: var(--app-radius-pill); font-size: 10px; font-weight: 700; letter-spacing: 0.02em; }
.badge-pass { background: rgba(111,186,44,0.12); color: var(--c-workflow); border: 1.5px solid rgba(111,186,44,0.25); }
.badge-fail { background: rgba(224,90,90,0.12); color: #e05a5a; border: 1.5px solid rgba(224,90,90,0.25); }
.badge-running { background: rgba(245,195,28,0.12); color: #dba90e; border: 1.5px solid rgba(245,195,28,0.25); }
.badge-stopped { background: rgba(138,123,102,0.10); color: #8a7b66; border: 1.5px solid rgba(138,123,102,0.20); }

.mini-table { width: 100%; border-collapse: collapse; font-size: 12px; margin-top: 4px; }
.mini-table th { padding: 6px 10px; font-size: 11px; font-weight: 700; color: #9f927d; text-transform: uppercase; text-align: left; border-bottom: 1px solid rgba(196,184,158,0.3); }
.mini-table td { padding: 6px 10px; border-bottom: 1px dashed rgba(196,184,158,0.15); font-size: 12px; color: #725d42; }
.row-fail { background: rgba(224,90,90,0.04); }

/* ── Failure cards ── */
.fail-card { margin-bottom: 12px; }
.fail-card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 0;
  padding: 12px 16px;
  font-size: 14px;
  color: #794f27;
}
.fail-card-header--clickable {
  cursor: pointer;
  user-select: none;
  transition: background 0.15s ease;
  border-radius: 12px;
}
.fail-card-header--clickable:hover {
  background: rgba(232, 95, 95, 0.06);
}
.fail-card-meta { font-size: 12px; color: #9f927d; font-weight: 500; flex: 1; min-width: 0; }
.fail-expand-hint {
  font-size: 12px;
  font-weight: 600;
  color: #19c8b9;
  white-space: nowrap;
  margin-left: auto;
}
.fail-detail-text { font-family: 'SF Mono','Fira Code',monospace; font-size: 11px; white-space: pre-wrap; word-break: break-all; }

.expand-icon {
  cursor: pointer;
  font-size: 11px;
  color: #9f927d;
  transition: transform 0.25s ease;
  display: inline-block;
  user-select: none;
  flex-shrink: 0;
}
.expand-icon.open { transform: rotate(90deg); color: #19c8b9; }

.expand-panel {
  padding: 0 16px 14px;
  border-top: 1px dashed rgba(196,184,158,0.4);
  background: rgba(232,95,95,0.03);
  margin: 0 8px 8px;
  border-radius: 0 0 12px 12px;
}
.expand-header {
  font-size: 13px;
  font-weight: 700;
  color: #6b5b48;
  padding: 12px 0 8px;
}

.fail-step-fallback {
  padding: 4px 0 8px;
}
.fail-step-fallback__title {
  font-size: 12px;
  color: #9f927d;
  margin: 0 0 10px;
}
.fail-step-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px 12px;
  margin-bottom: 8px;
  background: rgba(255,255,255,0.5);
  border-radius: 10px;
  border: 1px dashed rgba(232,95,95,0.2);
}
.fail-step-row__meta { font-size: 12px; font-weight: 700; color: #794f27; }
.fail-step-row__desc { font-size: 13px; color: #4a3a28; }
.fail-step-row__error { font-size: 12px; color: #e85f5f; font-family: 'SF Mono','Fira Code',monospace; word-break: break-all; }

.fail-detail-row {
  display: flex; flex-wrap: wrap; gap: 16px;
  padding: 8px 0 4px; margin: 0 20px 12px;
  border-top: 1px dashed rgba(232,95,95,0.2);
}
.fail-detail-item {
  display: flex; flex-direction: column; gap: 2px;
  min-width: 140px; flex: 1;
}
.fd-label { font-size: 11px; color: #9f927d; font-weight: 500; }
.fd-value { font-size: 13px; color: #4a3a28; font-weight: 600; }
.fd-error { color: #e85f5f; }

.fail-no-iterations {
  padding: 12px 20px; font-size: 12px; color: #9f927d; font-style: italic;
}

.sec-title {
  font-weight: 800; font-size: 16px; color: #4A3A28;
  display: flex; align-items: center; gap: 8px; margin-bottom: 4px;
}
.sec-badge {
  font-size: 11px; font-weight: 800; color: #fff;
  padding: 2px 10px; border-radius: var(--app-radius-pill);
}
.sec-badge--muted {
  background: #8a7b66;
}
.sec-sub { font-size: 12px; color: #9f927d; margin-bottom: 12px; }

.fail-case-title-wrap {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  flex: 1;
}
.fail-case-title {
  font-size: 14px;
  line-height: 1.35;
  word-break: break-word;
}
.fail-case-id {
  font-family: 'SF Mono','Fira Code',monospace;
  font-size: 11px;
  font-weight: 600;
  color: #9f927d;
  background: rgba(139,115,85,0.08);
  padding: 1px 6px;
  border-radius: 4px;
  width: fit-content;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.fail-step-row__head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.fail-detail-row--nested {
  margin: 0;
  padding: 0;
  border-top: none;
}

.empty-note { text-align: center; padding: 48px 24px; color: #9f927d; }
.empty-note span { font-size: 36px; display: block; margin-bottom: 12px; }
.time-text { font-size: 12px; color: #8a7b66; white-space: nowrap; }

@media (max-width: 900px) {
  .kpi-row { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 600px) {
  .kpi-row { grid-template-columns: 1fr; }
}
</style>
