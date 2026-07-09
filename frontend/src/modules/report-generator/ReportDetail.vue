<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Chart, LineController, LineElement, PointElement, LinearScale, CategoryScale, BarController, BarElement, Filler, Tooltip, Legend } from 'chart.js'
import { animate, stagger } from 'animejs'

// Register Chart.js components (tree-shakeable)
Chart.register(LineController, LineElement, PointElement, LinearScale, CategoryScale, BarController, BarElement, Filler, Tooltip, Legend)
import { Button as AnimalButton, Card, Table, Tabs } from 'animal-island-vue'
import PageHeader from '@/shared/components/PageHeader.vue'
import { getRunReport, statusLabel, statusBadgeClass, iterBadgeClass, formatTime } from './api.js'

const route = useRoute()
const router = useRouter()
const runId = computed(() => String(route.params.runId))

const report = ref(null)
const loading = ref(false)
const activeTab = ref('cases')
const expandedCases = ref(new Set())

onMounted(() => loadReport())
watch(runId, () => { expandedCases.value = new Set(); loadReport() })

// Chart.js instances for cleanup
let passRateChart = null
let durationChart = null

onUnmounted(() => {
  if (passRateChart) passRateChart.destroy()
  if (durationChart) durationChart.destroy()
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

// ── Tabs ──
const tabs = computed(() => {
  const items = [{ key: 'cases', label: '用例执行明细' }]
  if (failedCases.value.length > 0) items.push({ key: 'failures', label: `失败分析 (${failedCases.value.length})` })
  items.push({ key: 'trend', label: '趋势图表' })
  return items
})

// ── Computed ──
const runMeta = computed(() => report.value || {})

const allCases = computed(() => {
  if (!report.value) return []
  return report.value.cases || []
})

const failedCases = computed(() => allCases.value.filter(c => c.fail > 0))

const kpiPassRate = computed(() => {
  if (!report.value) return 0
  return report.value.pass_rate || 0
})

// ── Toggle case expand ──
function toggleExpand(caseId) {
  const s = new Set(expandedCases.value)
  if (s.has(caseId)) s.delete(caseId)
  else s.add(caseId)
  expandedCases.value = s
}

function goBack() { router.push('/reports') }

// ── Chart rendering (called after tab switch + nextTick) ──
function renderCharts() {
  renderPassRateTrend()
  renderDurationChart()
}

function renderPassRateTrend() {
  if (!report.value || !report.value.recent_runs) return
  const canvas = document.getElementById('passRateTrendCanvas')
  if (!canvas) return
  if (passRateChart) passRateChart.destroy()
  const runs = report.value.recent_runs
  passRateChart = new Chart(canvas, {
    type: 'line',
    data: {
      labels: runs.map(r => {
        try { const d = new Date(r.started_at); return `${d.getMonth()+1}/${d.getDate()}` } catch (_) { return '' }
      }),
      datasets: [{
        label: '通过率',
        data: runs.map(r => r.rate),
        borderColor: '#19c8b9',
        backgroundColor: 'rgba(25,200,185,0.08)',
        fill: true, tension: 0.3,
        pointBackgroundColor: '#19c8b9', pointBorderColor: '#fff',
        pointBorderWidth: 2, pointRadius: 5, pointHoverRadius: 7, borderWidth: 2.5,
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: { min: 0, max: 105, ticks: { callback: v => v + '%' } },
      }
    }
  })
}

function renderDurationChart() {
  if (!report.value || !report.value.cases) return
  const canvas = document.getElementById('durationChartCanvas')
  if (!canvas) return
  if (durationChart) durationChart.destroy()
  const cases = report.value.cases
  const labels = cases.map(c => c.case_title.length > 12 ? c.case_title.slice(0, 12) + '…' : c.case_title)
  const data = cases.map(c => {
    const total = c.iterations.reduce((sum, it) => sum + (it.duration_ms || 0), 0)
    return c.iterations.length ? Math.round(total / c.iterations.length / 100) / 10 : 0
  })
  const colors = cases.map(c => c.fail > 0 ? 'rgba(224,90,90,0.6)' : 'rgba(25,200,185,0.6)')
  const borders = cases.map(c => c.fail > 0 ? '#e05a5a' : '#19c8b9')
  durationChart = new Chart(canvas, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: '平均耗时 (s)', data,
        backgroundColor: colors, borderColor: borders, borderWidth: 1.5, borderRadius: 8, borderSkipped: false,
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false, indexAxis: 'y',
      plugins: { legend: { display: false } },
      scales: { x: { ticks: { callback: v => v + 's' } } }
    }
  })
}

// Watch tab switch to render charts
watch(activeTab, async (tab) => {
  if (tab === 'trend') {
    await nextTick()
    setTimeout(renderCharts, 100)
  }
})
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
        <AnimalButton size="small" @click="goBack">← 返回列表</AnimalButton>
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

      <!-- Tabs -->
      <Tabs
        class="detail-tabs"
        :items="tabs"
        v-model="activeTab"
        :leaf-animation="true"
        :shadow="true"
      >
        <!-- ═══ TAB: 用例执行明细 ═══ -->
        <template #cases>
          <Card color="brown" pattern="brown" class="table-card">
            <Table
              :columns="[
                { title: '', dataIndex: 'expand', width: '30px' },
                { title: '用例ID', dataIndex: 'case_id', width: '160px' },
                { title: '用例名称', dataIndex: 'case_title' },
                { title: '计划', dataIndex: 'planned', width: '60px', align: 'center' },
                { title: '实际', dataIndex: 'actual', width: '60px', align: 'center' },
                { title: '✅', dataIndex: 'pass', width: '50px', align: 'center' },
                { title: '❌', dataIndex: 'fail', width: '50px', align: 'center' },
                { title: '成功率', dataIndex: 'rate_bar', width: '150px' },
                { title: '状态', dataIndex: 'status_badge', width: '80px', align: 'center' },
              ]"
              :data-source="allCases"
              row-key="case_id"
              :striped="true"
              :loading="loading"
              empty-text="暂无用例数据"
              class="detail-table"
            >
              <!-- Expand toggle -->
              <template #cell-expand="{ record }">
                <span class="expand-icon" :class="{ open: expandedCases.has(record.case_id) }"
                  @click="toggleExpand(record.case_id)">▶</span>
              </template>

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
            </Table>

            <!-- Expanded iteration rows -->
            <div v-for="c in allCases.filter(c => expandedCases.has(c.case_id))" :key="'exp-' + c.case_id" class="expand-panel">
              <div class="expand-header">{{ c.case_title }} — 迭代详情</div>
              <table class="mini-table">
                <thead><tr>
                  <th>迭代</th><th>结果</th><th>耗时</th><th>详情</th>
                </tr></thead>
                <tbody>
                  <tr v-for="it in c.iterations" :key="it.iteration" :class="{ 'row-fail': it.result !== 'pass' }">
                    <td>#{{ it.iteration }}</td>
                    <td><span class="badge" :class="iterBadgeClass(it.result)">{{ it.result === 'pass' ? 'PASS' : 'FAIL' }}</span></td>
                    <td>{{ it.duration_ms ? (it.duration_ms / 1000).toFixed(1) + 's' : '—' }}</td>
                    <td>{{ it.detail || '—' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </Card>
        </template>

        <!-- ═══ TAB: 失败分析 ═══ -->
        <template v-if="failedCases.length > 0" #failures>
          <div v-for="c in failedCases" :key="'fail-' + c.case_id" class="fail-card">
            <Card color="app-red" pattern="app-red">
              <div class="fail-card-header">
                <span class="badge badge-fail">FAIL</span>
                <strong>{{ c.case_title }}</strong>
                <span class="fail-card-meta">{{ c.fail }}/{{ c.actual }} 次失败 · 成功率 {{ c.rate }}%</span>
              </div>
              <table class="mini-table">
                <thead><tr>
                  <th>迭代</th><th>结果</th><th>耗时</th><th>详情</th>
                </tr></thead>
                <tbody>
                  <tr v-for="it in c.iterations.filter(i => i.result !== 'pass')" :key="it.iteration" class="row-fail">
                    <td>#{{ it.iteration }}</td>
                    <td><span class="badge badge-fail">FAIL</span></td>
                    <td>{{ it.duration_ms ? (it.duration_ms / 1000).toFixed(1) + 's' : '—' }}</td>
                    <td class="fail-detail-text">{{ it.detail || '无详情' }}</td>
                  </tr>
                </tbody>
              </table>
            </Card>
          </div>

          <div v-if="failedCases.length === 0" class="empty-note">
            <span>🎉</span><p>全部用例通过，无失败记录</p>
          </div>
        </template>

        <!-- ═══ TAB: 趋势图表 ═══ -->
        <template #trend>
          <div class="chart-row">
            <Card color="brown" pattern="brown" class="chart-card">
              <h4 class="chart-title">通过率趋势（近 10 次执行）</h4>
              <div class="chart-wrap"><canvas id="passRateTrendCanvas"></canvas></div>
            </Card>
            <Card color="brown" pattern="brown" class="chart-card">
              <h4 class="chart-title">用例平均耗时分布（本次）</h4>
              <div class="chart-wrap"><canvas id="durationChartCanvas"></canvas></div>
            </Card>
          </div>

          <!-- Recent runs table -->
          <Card color="brown" pattern="brown" class="table-card" style="margin-top:16px;">
            <Table
              :columns="[
                { title: 'Run ID', dataIndex: 'run_id', width: '200px' },
                { title: '总数', dataIndex: 'total', width: '60px', align: 'center' },
                { title: '通过', dataIndex: 'passed', width: '60px', align: 'center' },
                { title: '失败', dataIndex: 'failed', width: '60px', align: 'center' },
                { title: '通过率', dataIndex: 'rate_bar', width: '150px' },
                { title: '时间', dataIndex: 'started_at', width: '150px' },
              ]"
              :data-source="(report && report.recent_runs) ? [...report.recent_runs].reverse() : []"
              row-key="run_id"
              :striped="true"
              empty-text="暂无历史数据"
              class="detail-table"
            >
              <template #cell-run_id="{ record }">
                <code class="mono">{{ record.run_id }}</code>
              </template>
              <template #cell-rate_bar="{ record }">
                <div class="rate-cell">
                  <div class="progress-bar">
                    <div class="p-pass" :style="{ width: record.rate + '%' }"></div>
                    <div v-if="record.failed > 0" class="p-fail" :style="{ width: (100 - record.rate) + '%' }"></div>
                  </div>
                  <span class="rate-text" :class="{ 'rate-ok': record.rate >= 95, 'rate-warn': record.rate >= 80 && record.rate < 95, 'rate-bad': record.rate < 80 }">{{ record.rate }}%</span>
                </div>
              </template>
              <template #cell-started_at="{ record }">
                <span class="time-text">{{ formatTime(record.started_at) }}</span>
              </template>
            </Table>
          </Card>
        </template>
      </Tabs>
    </div>
  </div>
</template>

<style scoped>
.doc-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.doc-body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.detail-tabs {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.detail-tabs :deep(.animal-tabs) {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
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
.accent-green { background: #6fba2c; }
.accent-red { background: #e05a5a; }
.accent-yellow { background: #f5c31c; }
.kpi-value { font-size: 32px; font-weight: 900; color: #794f27; line-height: 1.1; }
.kpi-label { font-size: 12px; color: #9f927d; margin-top: 4px; font-weight: 600; }
.kpi-sub { font-size: 11px; color: #8a7b66; margin-top: 2px; }
.num-pass { color: #6fba2c; }
.num-fail { color: #e05a5a; }
.num-warn { color: #dba90e; }

/* ── Tabs ── */
.detail-tabs :deep(.animal-tabs__content) {
  flex: 1;
  min-height: 0;
  overflow-x: hidden;
  overflow-y: auto;
  display: block;
  padding-top: 16px;
}

.detail-tabs :deep(.animal-tabs__inner) {
  min-height: min-content;
}

/* ── Table card ── */
.table-card { overflow: hidden; }
.table-card :deep(.animal-card__content) { padding: 0; border-radius: 14px; overflow: hidden; }

/* ── Table styles ── */
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

/* ── Expand icon ── */
.expand-icon { cursor: pointer; font-size: 11px; color: #9f927d; transition: transform 0.25s ease; display: inline-block; user-select: none; }
.expand-icon.open { transform: rotate(90deg); color: #19c8b9; }
.expand-icon:hover { color: #19c8b9; }

/* ── Misc ── */
.mono { font-family: 'SF Mono','Fira Code','Cascadia Code',Consolas,monospace; font-size: 11px; font-weight: 600; background: rgba(139,115,85,0.06); padding: 2px 6px; border-radius: 4px; }

/* ── Rate cell ── */
.rate-cell { display: flex; align-items: center; gap: 8px; }
.progress-bar { display: flex; height: 7px; border-radius: 50px; overflow: hidden; background: #f0ece2; flex: 1; max-width: 90px; }
.p-pass { background: #6fba2c; transition: width 0.5s ease; border-radius: 50px; }
.p-fail { background: #e05a5a; transition: width 0.5s ease; border-radius: 50px; }
.rate-text { font-weight: 700; font-size: 12px; min-width: 38px; text-align: right; }
.rate-ok { color: #6fba2c; }
.rate-warn { color: #dba90e; }
.rate-bad { color: #e05a5a; }

/* ── Badges ── */
.badge { display: inline-flex; align-items: center; padding: 3px 10px; border-radius: 50px; font-size: 10px; font-weight: 700; letter-spacing: 0.02em; }
.badge-pass { background: rgba(111,186,44,0.12); color: #6fba2c; border: 1.5px solid rgba(111,186,44,0.25); }
.badge-fail { background: rgba(224,90,90,0.12); color: #e05a5a; border: 1.5px solid rgba(224,90,90,0.25); }
.badge-running { background: rgba(245,195,28,0.12); color: #dba90e; border: 1.5px solid rgba(245,195,28,0.25); }
.badge-stopped { background: rgba(138,123,102,0.10); color: #8a7b66; border: 1.5px solid rgba(138,123,102,0.20); }

/* ── Expand panel ── */
.expand-panel { padding: 0 16px 14px; border-top: 1px dashed rgba(196,184,158,0.4); background: rgba(25,200,185,0.02); }
.expand-header { font-size: 13px; font-weight: 700; color: #6b5b48; padding: 12px 0 8px; }
.mini-table { width: 100%; border-collapse: collapse; font-size: 12px; margin-top: 4px; }
.mini-table th { padding: 6px 10px; font-size: 11px; font-weight: 700; color: #9f927d; text-transform: uppercase; text-align: left; border-bottom: 1px solid rgba(196,184,158,0.3); }
.mini-table td { padding: 6px 10px; border-bottom: 1px dashed rgba(196,184,158,0.15); font-size: 12px; color: #725d42; }
.row-fail { background: rgba(224,90,90,0.04); }

/* ── Failure cards ── */
.fail-card { margin-bottom: 12px; }
.fail-card-header { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; font-size: 14px; color: #794f27; }
.fail-card-meta { font-size: 12px; color: #9f927d; font-weight: 500; }
.fail-detail-text { font-family: 'SF Mono','Fira Code',monospace; font-size: 11px; white-space: pre-wrap; word-break: break-all; max-width: 400px; }

/* ── Charts ── */
.chart-row { display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 14px; margin-bottom: 16px; }
.chart-card :deep(.animal-card__content) { padding: 16px 20px; }
.chart-title { font-size: 14px; font-weight: 700; color: #794f27; margin-bottom: 8px; }
.chart-wrap { position: relative; height: 220px; }
.chart-wrap canvas { width: 100% !important; height: 100% !important; }

.empty-note { text-align: center; padding: 48px 24px; color: #9f927d; }
.empty-note span { font-size: 36px; display: block; margin-bottom: 12px; }
.time-text { font-size: 12px; color: #8a7b66; white-space: nowrap; }

@media (max-width: 900px) {
  .kpi-row { grid-template-columns: repeat(2, 1fr); }
  .chart-row { grid-template-columns: 1fr; }
}
@media (max-width: 600px) {
  .kpi-row { grid-template-columns: 1fr; }
}
</style>
