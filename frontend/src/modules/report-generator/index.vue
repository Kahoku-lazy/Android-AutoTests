<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Chart, LineController, LineElement, PointElement, LinearScale, CategoryScale, BarController, BarElement, Filler, Tooltip, Legend } from 'chart.js'
import { animate, stagger } from 'animejs'
import { Button as AnimalButton, Card, Table, Tabs } from 'animal-island-vue'
import PageHeader from '@/shared/components/PageHeader.vue'
import { listRuns, statusLabel, statusBadgeClass, formatTime } from './api.js'

Chart.register(LineController, LineElement, PointElement, LinearScale, CategoryScale, BarController, BarElement, Filler, Tooltip, Legend)

const router = useRouter()

const runs = ref([])
const summary = ref(null)
const loading = ref(false)
const activeFilter = ref('all')
const dateRange = ref([])

const PAGE_SIZE_OPTIONS = [10, 50, 100]
const TABLE_TOOLBAR_HEIGHT = 52
const TABLE_HEADER_HEIGHT = 54
const TABLE_ROW_HEIGHT = 50
const pageSize = ref(10)
const currentPage = ref(1)

// ── Format date to YYYY-MM-DD ──
function fmtDate(d) {
  const pad = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

const trend = ref(null)

// Chart.js instances
let passRateChart = null
let dailyCountChart = null

onMounted(() => fetchReports())
watch(dateRange, () => { currentPage.value = 1; fetchReports() }, { deep: true })
watch(activeFilter, () => { currentPage.value = 1 })

onUnmounted(() => {
  if (passRateChart) passRateChart.destroy()
  if (dailyCountChart) dailyCountChart.destroy()
})

// Watch trend data to re-render charts
watch(trend, async () => { await nextTick(); setTimeout(renderTrendCharts, 100) })

async function fetchReports() {
  loading.value = true
  try {
    const params = {}
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = fmtDate(dateRange.value[0])
      params.end_date = fmtDate(dateRange.value[1])
    }
    const { data } = await listRuns(params)
    if (data.ok) {
      runs.value = data.runs || []
      summary.value = data.summary || null
      trend.value = data.trend || null
    }
  } catch (_) {}
  loading.value = false
  await nextTick()
  animate('.report-table tbody tr', { opacity: [0, 1], translateY: [16, 0], delay: stagger(40), duration: 380, ease: 'outCubic' })
}

function renderTrendCharts() {
  if (!trend.value || !trend.value.labels?.length) return
  renderPassRateChart()
  renderDailyCountChart()
}

function renderPassRateChart() {
  const canvas = document.getElementById('overviewPassRateCanvas')
  if (!canvas) return
  if (passRateChart) passRateChart.destroy()
  passRateChart = new Chart(canvas, {
    type: 'line',
    data: {
      labels: trend.value.labels,
      datasets: [{
        label: '通过率',
        data: trend.value.rate,
        borderColor: '#19c8b9',
        backgroundColor: 'rgba(25,200,185,0.08)',
        fill: true, tension: 0.3,
        pointBackgroundColor: '#19c8b9', pointBorderColor: '#fff',
        pointBorderWidth: 2, pointRadius: 4, pointHoverRadius: 6, borderWidth: 2.5,
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

function renderDailyCountChart() {
  const canvas = document.getElementById('overviewDailyCountCanvas')
  if (!canvas) return
  if (dailyCountChart) dailyCountChart.destroy()
  dailyCountChart = new Chart(canvas, {
    type: 'bar',
    data: {
      labels: trend.value.labels,
      datasets: [
        { label: '通过', data: trend.value.pass, backgroundColor: 'rgba(111,186,44,0.6)', borderColor: '#6fba2c', borderWidth: 1, borderRadius: 6, borderSkipped: false },
        { label: '失败', data: trend.value.fail, backgroundColor: 'rgba(224,90,90,0.6)', borderColor: '#e05a5a', borderWidth: 1, borderRadius: 6, borderSkipped: false },
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { position: 'bottom', labels: { usePointStyle: true, padding: 20 } } },
      scales: { x: { stacked: true }, y: { stacked: true, ticks: { stepSize: 1 } } },
    }
  })
}

// ── Filter tabs ──
const statusTabs = computed(() => [
  { key: 'all', label: `全部 (${runs.value.length})` },
  { key: 'COMPLETED', label: '已完成' },
  { key: 'FAILED', label: '失败' },
  { key: 'STOPPED', label: '已停止' },
])

const filteredRuns = computed(() => {
  if (activeFilter.value === 'all') return runs.value
  return runs.value.filter(r => r.status === activeFilter.value)
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredRuns.value.length / pageSize.value)))

const pagedRuns = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredRuns.value.slice(start, start + pageSize.value)
})

const displayRowCount = computed(() => {
  if (pagedRuns.value.length === 0) return 3
  return pagedRuns.value.length
})

const tableAreaMinHeight = computed(() => (
  TABLE_TOOLBAR_HEIGHT + TABLE_HEADER_HEIGHT + displayRowCount.value * TABLE_ROW_HEIGHT
))

// ── Table columns（百分比宽度，铺满容器）──
const columns = [
  { title: 'Run ID', dataIndex: 'run_id', width: '13%' },
  { title: '设备', dataIndex: 'device_serial', width: '9%' },
  { title: '任务名称', dataIndex: 'task_name', width: '20%' },
  { title: '创建人', dataIndex: 'creator', width: '7%' },
  { title: '用例数', dataIndex: 'case_count', width: '5%', align: 'center' },
  { title: '通过', dataIndex: 'passed', width: '5%', align: 'center' },
  { title: '失败', dataIndex: 'failed', width: '5%', align: 'center' },
  { title: '通过率', dataIndex: 'rate', width: '11%' },
  { title: '状态', dataIndex: 'status', width: '7%', align: 'center' },
  { title: '耗时', dataIndex: 'duration', width: '6%', align: 'center' },
  { title: '时间', dataIndex: 'started_at', width: '12%' },
]

function openReport(run) {
  router.push(`/reports/${encodeURIComponent(run.run_id)}`)
}

function setPageSize(size) {
  pageSize.value = size
  currentPage.value = 1
}

function goPage(page) {
  currentPage.value = Math.min(Math.max(1, page), totalPages.value)
}
</script>

<template>
  <div class="doc-page">
    <PageHeader
      title="测试报告 Test Reports"
      subtitle="查看历史测试执行记录，点击 Run ID 进入详细报告"
      color="app-yellow"
    />

    <div class="doc-body">
      <!-- Date range filter -->
      <div class="date-filter-bar">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          value-format="YYYY-MM-DD"
          :clearable="true"
          :unlink-panels="true"
          style="width: 280px"
        />
        <span v-if="summary" class="date-summary">
          共 {{ summary.total_runs }} 次执行 · {{ summary.total_iterations }} 次迭代
        </span>
      </div>

      <!-- KPI Summary Cards -->
      <div v-if="summary" class="kpi-row">
        <div class="kpi-card">
          <div class="kpi-accent accent-teal"></div>
          <div class="kpi-value">{{ summary.total_runs }}</div>
          <div class="kpi-label">总执行次数</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-accent accent-green"></div>
          <div class="kpi-value num-pass">{{ summary.total_pass }}</div>
          <div class="kpi-label">✅ 通过</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-accent accent-red"></div>
          <div class="kpi-value num-fail">{{ summary.total_fail }}</div>
          <div class="kpi-label">❌ 失败</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-accent accent-yellow"></div>
          <div class="kpi-value" :class="summary.pass_rate >= 95 ? 'num-pass' : summary.pass_rate >= 80 ? 'num-warn' : 'num-fail'">
            {{ summary.pass_rate }}%
          </div>
          <div class="kpi-label">📊 总通过率</div>
          <div class="kpi-sub">{{ summary.total_iterations }} 次迭代</div>
        </div>
      </div>

      <!-- Trend Charts -->
      <div v-if="trend && trend.labels?.length" class="chart-row">
        <Card color="brown" pattern="brown" class="chart-card">
          <h4 class="chart-title">通过率趋势</h4>
          <div class="chart-wrap"><canvas id="overviewPassRateCanvas"></canvas></div>
        </Card>
        <Card color="brown" pattern="brown" class="chart-card">
          <h4 class="chart-title">每日通过/失败</h4>
          <div class="chart-wrap"><canvas id="overviewDailyCountCanvas"></canvas></div>
        </Card>
      </div>

      <!-- Filter Tabs -->
      <Tabs
        class="report-tabs"
        :style="{ minHeight: `${tableAreaMinHeight + 88}px` }"
        :items="statusTabs"
        v-model="activeFilter"
        :leaf-animation="true"
        :shadow="true"
      >
        <template v-for="tab in statusTabs" #[tab.key] :key="tab.key">
          <Card
            color="brown"
            pattern="brown"
            class="table-card"
            :style="{ minHeight: `${tableAreaMinHeight}px` }"
          >
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
              <div v-if="filteredRuns.length > 0" class="table-toolbar-right">
                <span class="page-info">
                  第 {{ currentPage }} / {{ totalPages }} 页 · 共 {{ filteredRuns.length }} 条
                </span>
                <div v-if="totalPages > 1" class="page-nav">
                  <AnimalButton size="small" :disabled="currentPage <= 1" @click="goPage(currentPage - 1)">上一页</AnimalButton>
                  <AnimalButton size="small" :disabled="currentPage >= totalPages" @click="goPage(currentPage + 1)">下一页</AnimalButton>
                </div>
              </div>
            </div>
            <Table
              :columns="columns"
              :data-source="pagedRuns"
              row-key="run_id"
              :striped="false"
              :loading="loading"
              empty-text="暂无执行记录，请先执行测试"
              class="report-table report-table--rainbow"
            >
              <!-- Run ID — clickable link -->
              <template #cell-run_id="{ record }">
                <a class="run-link" @click.prevent="openReport(record)" href="#">
                  <code class="cell-run-id">{{ record.run_id }}</code>
                </a>
              </template>

              <template #cell-device_serial="{ value }">
                <span class="cell-device">{{ value }}</span>
              </template>

              <template #cell-task_name="{ record }">
                <span class="cell-task-name">{{ record.task_name || '—' }}</span>
              </template>

              <template #cell-creator="{ record }">
                <span class="cell-creator">{{ record.creator || '—' }}</span>
              </template>

              <template #cell-case_count="{ value }">
                <span class="cell-count">{{ value }}</span>
              </template>

              <!-- Passed count — green -->
              <template #cell-passed="{ record }">
                <span class="num-pass">{{ record.passed }}</span>
              </template>

              <!-- Failed count — red -->
              <template #cell-failed="{ record }">
                <span :class="record.failed > 0 ? 'num-fail' : ''">{{ record.failed }}</span>
              </template>

              <!-- Pass rate with progress bar -->
              <template #cell-rate="{ record }">
                <div class="rate-cell">
                  <div class="progress-bar">
                    <div class="p-pass" :style="{ width: record.rate + '%' }"></div>
                    <div v-if="record.failed > 0" class="p-fail" :style="{ width: (100 - record.rate) + '%' }"></div>
                  </div>
                  <span class="rate-text" :class="{ 'rate-ok': record.rate >= 95, 'rate-warn': record.rate >= 80 && record.rate < 95, 'rate-bad': record.rate < 80 }">
                    {{ record.rate }}%
                  </span>
                </div>
              </template>

              <!-- Status badge -->
              <template #cell-status="{ record }">
                <span class="badge" :class="statusBadgeClass(record.status)">{{ statusLabel(record.status) }}</span>
              </template>

              <!-- Time -->
              <template #cell-duration="{ value }">
                <span class="cell-duration">{{ value }}</span>
              </template>
              <template #cell-started_at="{ record }">
                <span class="cell-time">{{ formatTime(record.started_at) }}</span>
              </template>

              <!-- Empty state -->
              <template #empty>
                <div class="table-empty">
                  <span>📋</span>
                  <p>暂无执行记录</p>
                  <p class="sub">请先在执行引擎中运行测试，完成后将自动生成报告</p>
                </div>
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
  width: 100%;
  display: flex;
  flex-direction: column;
  overflow: visible;
}

/* ── Date filter bar ── */
.date-filter-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
  flex-shrink: 0;
}
.date-summary {
  font-size: 13px;
  color: #8a7b66;
  font-weight: 600;
}

/* ── Trend Charts ── */
.chart-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  margin-bottom: 16px;
  flex-shrink: 0;
}
.chart-card :deep(.animal-card__content) { padding: 14px 18px; }
.chart-title {
  font-size: 13px;
  font-weight: 700;
  color: #794f27;
  margin: 0 0 6px;
}
.chart-wrap {
  position: relative;
  height: 200px;
}
.chart-wrap canvas { width: 100% !important; height: 100% !important; }

/* ── KPI Cards ── */
.kpi-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-bottom: 16px;
  flex-shrink: 0;
}
.kpi-card {
  background: rgb(247,243,223);
  border-radius: 18px;
  padding: 18px 22px;
  border: 1.5px solid #c4b89e;
  position: relative;
  overflow: hidden;
  transition: transform 0.25s cubic-bezier(0.4,0,0.2,1);
}
.kpi-card:hover { transform: translateY(-2px); }
.kpi-accent {
  position: absolute;
  left: 0; top: 0; bottom: 0;
  width: 5px;
  border-radius: 0 3px 3px 0;
}
.accent-teal { background: #19c8b9; }
.accent-green { background: #6fba2c; }
.accent-red { background: #e05a5a; }
.accent-yellow { background: #f5c31c; }
.kpi-value {
  font-size: 30px;
  font-weight: 900;
  color: #794f27;
  line-height: 1.1;
}
.kpi-label {
  font-size: 12px;
  color: #9f927d;
  margin-top: 4px;
  font-weight: 600;
}
.kpi-sub {
  font-size: 11px;
  color: #8a7b66;
  margin-top: 2px;
}
.num-pass { color: #6fba2c; }
.num-fail { color: #e05a5a; }
.num-warn { color: #dba90e; }

.report-tabs {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  width: 100%;
}

.report-tabs :deep(.animal-tabs) {
  display: flex;
  flex-direction: column;
  overflow: visible;
  width: 100%;
}

.report-tabs :deep(.animal-tabs__content) {
  overflow: visible;
  display: block;
  padding-top: 16px;
  width: 100%;
}

.report-tabs :deep(.animal-tabs__inner) {
  min-height: min-content;
  width: 100%;
}

/* Table card — zero-padding for edge-to-edge Table */
.table-card {
  overflow: visible;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  width: 100%;
}
.table-card :deep(.animal-card__content) {
  padding: 0;
  border-radius: 16px;
  overflow: visible;
  flex: 1;
  display: flex;
  flex-direction: column;
}

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

/* Rainbow gradient table — 11 columns */
.report-table { width: 100%; flex: 1; }
.report-table :deep(.animal-table-wrapper) {
  width: 100%;
}
.report-table :deep(.animal-table-wrapper),
.report-table :deep(.animal-table__body) {
  overflow: visible !important;
  max-height: none !important;
}
.report-table :deep(table) {
  width: 100%;
  table-layout: fixed;
  border-collapse: separate;
  border-spacing: 0;
}

.report-table--rainbow :deep(th) {
  font-size: 18px;
  font-weight: 800;
  padding: 16px 12px;
  text-align: left;
  text-transform: uppercase;
  letter-spacing: 0.4px;
  white-space: nowrap;
  border: none;
}
/* 1=run_id, 2=device, 3=task_name, 4=creator, 5=case_count, 6=passed, 7=failed, 8=rate, 9=status, 10=duration, 11=time */
.report-table--rainbow :deep(th:nth-child(1)) {
  background: linear-gradient(135deg, #f8a6b2 0%, #e85f5f 100%);
  color: #fff;
}
.report-table--rainbow :deep(th:nth-child(2)) {
  background: linear-gradient(135deg, #ffd97a 0%, #f7cd67 45%, #f5a623 100%);
  color: #5c3d10;
}
.report-table--rainbow :deep(th:nth-child(3)) {
  background: linear-gradient(135deg, #f5c6a3 0%, #f7a8c4 100%);
  color: #6b3d28;
}
.report-table--rainbow :deep(th:nth-child(4)) {
  background: linear-gradient(135deg, #d4c4ff 0%, #b39ef3 100%);
  color: #3d2d6b;
}
.report-table--rainbow :deep(th:nth-child(5)) {
  background: linear-gradient(135deg, #d4e87a 0%, #c5db5a 100%);
  color: #3d5010;
  text-align: center;
}
.report-table--rainbow :deep(th:nth-child(6)) {
  background: linear-gradient(135deg, #9ed456 0%, #6fba2c 100%);
  color: #1e4010;
  text-align: center;
}
.report-table--rainbow :deep(th:nth-child(7)) {
  background: linear-gradient(135deg, #ff8a8a 0%, #e85f5f 100%);
  color: #fff;
  text-align: center;
}
.report-table--rainbow :deep(th:nth-child(8)) {
  background: linear-gradient(135deg, #7ee8df 0%, #19c8b9 100%);
  color: #064a44;
}
.report-table--rainbow :deep(th:nth-child(9)) {
  background: linear-gradient(135deg, #a8b8ff 0%, #889df0 100%);
  color: #2a3568;
  text-align: center;
}
.report-table--rainbow :deep(th:nth-child(10)) {
  background: linear-gradient(135deg, #d4c4ff 0%, #b39ef3 100%);
  color: #3d2d6b;
  text-align: center;
}
.report-table--rainbow :deep(th:nth-child(11)) {
  background: linear-gradient(135deg, #f5c6a3 0%, #f7a8c4 100%);
  color: #6b3d28;
}

.report-table--rainbow :deep(td) {
  padding: 13px 12px;
  font-size: 14px;
  color: #4a3a28;
  background: transparent;
  border: none;
  border-bottom: 1px solid rgba(139, 115, 85, 0.08);
  vertical-align: middle;
}
.report-table--rainbow :deep(tr:nth-child(even) td) {
  background: rgba(139, 115, 85, 0.03);
}
.report-table--rainbow :deep(tr:hover td) {
  background: rgba(25, 200, 185, 0.06);
}
.report-table--rainbow :deep(tr:last-child td) {
  border-bottom: none;
}
/* Center-align numeric/status columns */
.report-table--rainbow :deep(td:nth-child(5)),
.report-table--rainbow :deep(td:nth-child(6)),
.report-table--rainbow :deep(td:nth-child(7)),
.report-table--rainbow :deep(td:nth-child(9)),
.report-table--rainbow :deep(td:nth-child(10)) {
  text-align: center;
}

/* Run ID link */
.run-link {
  text-decoration: none;
  color: inherit;
}
.run-link:hover .cell-run-id {
  color: #19c8b9;
  text-decoration: underline;
}
.cell-run-id {
  font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', Consolas, monospace;
  font-size: 14px;
  font-weight: 600;
  color: #c0392b;
  line-height: 1.45;
  word-break: break-all;
  transition: color 0.15s ease;
}
.cell-device {
  font-family: 'SF Mono', 'Fira Code', Consolas, monospace;
  font-size: 14px;
  font-weight: 600;
  color: #b8860b;
}
.cell-task-name {
  font-size: 14px;
  font-weight: 700;
  color: #4a3a28;
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.cell-creator {
  font-size: 14px;
  color: #8a7b66;
}
.cell-count {
  font-weight: 700;
  font-size: 14px;
  color: #6b8f1a;
}
.cell-duration {
  font-size: 14px;
  font-weight: 600;
  color: #7b5fbf;
  white-space: nowrap;
}
.cell-time {
  font-size: 14px;
  font-weight: 600;
  color: #b06b48;
  white-space: nowrap;
}

/* Pass/Fail numbers */
.num-pass { color: #4a8c1c; font-weight: 700; }
.num-fail { color: #c0392b; font-weight: 700; }

/* Rate cell */
.rate-cell { display: flex; align-items: center; gap: 10px; min-width: 0; }
.progress-bar {
  display: flex; height: 8px; border-radius: 50px; overflow: hidden;
  background: #f0ece2; flex: 1; max-width: 100px;
}
.p-pass { background: #6fba2c; transition: width 0.5s ease; border-radius: 50px; }
.p-fail { background: #e05a5a; transition: width 0.5s ease; border-radius: 50px; }
.rate-text { font-weight: 700; font-size: 14px; min-width: 42px; text-align: right; }
.rate-ok { color: #4a8c1c; }
.rate-warn { color: #b8860b; }
.rate-bad { color: #c0392b; }

/* Status badges */
.badge { display: inline-flex; align-items: center; padding: 5px 12px; border-radius: 50px; font-size: 14px; font-weight: 700; letter-spacing: 0.02em; }
.badge-pass { background: rgba(111,186,44,0.12); color: #4a8c1c; border: 1.5px solid rgba(111,186,44,0.25); }
.badge-fail { background: rgba(224,90,90,0.12); color: #c0392b; border: 1.5px solid rgba(224,90,90,0.25); }
.badge-running { background: rgba(245,195,28,0.12); color: #b8860b; border: 1.5px solid rgba(245,195,28,0.25); }
.badge-stopped { background: rgba(138,123,102,0.10); color: #8a7b66; border: 1.5px solid rgba(138,123,102,0.20); }

/* Empty state */
.table-empty { display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 48px 24px; color: #988b7a; }
.table-empty span { font-size: 36px; }
.table-empty p { font-size: 15px; margin: 0; }
.table-empty .sub { font-size: 13px; color: #b8a898; }

@media (max-width: 900px) {
  .kpi-row { grid-template-columns: repeat(2, 1fr); }
  .chart-row { grid-template-columns: 1fr; }
}
@media (max-width: 600px) {
  .kpi-row { grid-template-columns: 1fr; }
}
</style>
