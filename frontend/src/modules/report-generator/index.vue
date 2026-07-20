<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Chart, LineController, LineElement, PointElement, LinearScale, CategoryScale, BarController, BarElement, Filler, Tooltip, Legend } from 'chart.js'
import { animate, stagger } from 'animejs'
// Card/Table/AppTabs → AppCard/AppTable/AppTabs
import AppCard from "@/shared/components/AppCard.vue";
import AppTable from "@/shared/components/AppTable.vue";
import AppTabs from "@/shared/components/AppTabs.vue";
import { usePagination } from '@/shared/composables/usePagination.js'
import WorkbenchHeader from '@/shared/components/WorkbenchHeader.vue'
import { listRuns, statusLabel, statusBadgeClass, formatTime } from './api.js'

Chart.register(LineController, LineElement, PointElement, LinearScale, CategoryScale, BarController, BarElement, Filler, Tooltip, Legend)

const router = useRouter()

const runs = ref([])
const summary = ref(null)
const bugSummary = ref(null)
const loading = ref(false)
const activeFilter = ref('all')
const dateRange = ref([])
const filterRunId = ref('')
const filterTaskName = ref('')
const filterDevice = ref('')
const filterCreator = ref('')

let filterDebounceTimer = null

const TABLE_TOOLBAR_HEIGHT = 52
const TABLE_HEADER_HEIGHT = 54
const TABLE_ROW_HEIGHT = 50

const trend = ref(null)

const CHART_RANGE_OPTIONS = [
  { key: 7, label: '一周' },
  { key: 30, label: '一月' },
  { key: 90, label: '一季度' },
]
const chartRange = ref(30)
const CHART_VISIBLE_DAYS = 5

const chartRangeLabel = computed(() => {
  const opt = CHART_RANGE_OPTIONS.find(o => o.key === chartRange.value)
  return opt ? opt.label : '一月'
})

// Chart.js instances
let passRateChart = null
let dailyCountChart = null

onMounted(() => {
  fetchReports()
  window.addEventListener('resize', onChartResize)
})
watch(dateRange, () => { currentPage.value = 1; fetchReports() }, { deep: true })
watch([filterRunId, filterTaskName, filterDevice, filterCreator], () => {
  currentPage.value = 1
  clearTimeout(filterDebounceTimer)
  filterDebounceTimer = setTimeout(fetchReports, 350)
})
watch(activeFilter, () => { currentPage.value = 1 })
watch(chartRange, () => { fetchReports() })

onUnmounted(() => {
  clearTimeout(filterDebounceTimer)
  clearTimeout(chartResizeTimer)
  window.removeEventListener('resize', onChartResize)
  if (passRateChart) passRateChart.destroy()
  if (dailyCountChart) dailyCountChart.destroy()
})

let chartResizeTimer = null
let syncingChartScroll = false

function onChartResize() {
  clearTimeout(chartResizeTimer)
  chartResizeTimer = setTimeout(renderTrendCharts, 150)
}

function getChartDayWidth(scrollEl) {
  if (!scrollEl || scrollEl.clientWidth <= 0) return 72
  return scrollEl.clientWidth / CHART_VISIBLE_DAYS
}

function getChartMetrics() {
  const n = trend.value?.labels?.length || 0
  const passScroll = document.getElementById('chartScrollPass')
  const dayW = getChartDayWidth(passScroll)
  const totalW = Math.max(Math.round(n * dayW), passScroll?.clientWidth || 360)
  return { n, dayW, totalW, height: 200 }
}

function applyChartInnerWidths(metrics) {
  const innerW = `${metrics.totalW}px`
  for (const id of ['chartInnerPass', 'chartInnerDaily']) {
    const el = document.getElementById(id)
    if (!el) continue
    el.style.width = innerW
    el.style.minWidth = innerW
    el.style.maxWidth = innerW
    const wrap = el.querySelector('.chart-wrap')
    if (wrap) {
      wrap.style.width = innerW
      wrap.style.minWidth = innerW
    }
  }
}

function prepareChartCanvas(canvas, metrics) {
  const dpr = window.devicePixelRatio || 1
  canvas.style.width = `${metrics.totalW}px`
  canvas.style.height = `${metrics.height}px`
  canvas.width = Math.round(metrics.totalW * dpr)
  canvas.height = Math.round(metrics.height * dpr)
  const ctx = canvas.getContext('2d')
  if (ctx) ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
}

function scrollChartsToEnd() {
  const passScroll = document.getElementById('chartScrollPass')
  const dailyScroll = document.getElementById('chartScrollDaily')
  if (!passScroll) return
  const left = Math.max(0, passScroll.scrollWidth - passScroll.clientWidth)
  passScroll.scrollLeft = left
  if (dailyScroll) dailyScroll.scrollLeft = left
}

function syncChartScroll(source) {
  if (syncingChartScroll) return
  syncingChartScroll = true
  const passScroll = document.getElementById('chartScrollPass')
  const dailyScroll = document.getElementById('chartScrollDaily')
  const src = source === 'pass' ? passScroll : dailyScroll
  const dst = source === 'pass' ? dailyScroll : passScroll
  if (src && dst) dst.scrollLeft = src.scrollLeft
  syncingChartScroll = false
}

// Watch trend data to re-render charts
watch(trend, async () => { await nextTick(); setTimeout(renderTrendCharts, 100) })

async function fetchReports() {
  loading.value = true
  try {
    const params = {}
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    const runId = filterRunId.value.trim()
    const taskName = filterTaskName.value.trim()
    const device = filterDevice.value.trim()
    const creator = filterCreator.value.trim()
    if (runId) params.run_id = runId
    if (taskName) params.task_name = taskName
    if (device) params.device_serial = device
    if (creator) params.creator = creator
    params.chart_range = String(chartRange.value)
    const { data } = await listRuns(params)
    if (data.ok) {
      runs.value = data.runs || []
      summary.value = data.summary || null
      bugSummary.value = data.bug_summary || null
      trend.value = data.trend || null
    }
  } catch (_) {}
  loading.value = false
  await nextTick()
  animate('.report-table tbody tr', { opacity: [0, 1], translateY: [16, 0], delay: stagger(40), duration: 380, ease: 'outCubic' })
}

async function renderTrendCharts() {
  if (!trend.value || !trend.value.labels?.length) return
  await nextTick()
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      const metrics = getChartMetrics()
      if (!metrics.n) return
      applyChartInnerWidths(metrics)
      renderPassRateChart(metrics)
      renderDailyCountChart(metrics)
      requestAnimationFrame(() => scrollChartsToEnd())
    })
  })
}

function setChartRange(days) {
  chartRange.value = days
}

function renderPassRateChart(metrics) {
  const canvas = document.getElementById('overviewPassRateCanvas')
  if (!canvas) return
  if (passRateChart) passRateChart.destroy()
  prepareChartCanvas(canvas, metrics)
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
      responsive: false,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: false }, ticks: { maxRotation: 45, minRotation: 0 } },
        y: { min: 0, max: 105, ticks: { callback: v => v + '%' } },
      }
    }
  })
}

function renderDailyCountChart(metrics) {
  const canvas = document.getElementById('overviewDailyCountCanvas')
  if (!canvas) return
  if (dailyCountChart) dailyCountChart.destroy()
  prepareChartCanvas(canvas, metrics)
  dailyCountChart = new Chart(canvas, {
    type: 'bar',
    data: {
      labels: trend.value.labels,
      datasets: [
        {
          label: '通过',
          data: trend.value.pass,
          backgroundColor: 'rgba(111,186,44,0.75)',
          borderColor: '#6fba2c',
          borderWidth: 1.5,
          borderRadius: 6,
          borderSkipped: false,
          barPercentage: 0.9,
          categoryPercentage: 0.7,
        },
        {
          label: '失败',
          data: trend.value.fail,
          backgroundColor: 'rgba(224,90,90,0.75)',
          borderColor: '#e05a5a',
          borderWidth: 1.5,
          borderRadius: 6,
          borderSkipped: false,
          barPercentage: 0.9,
          categoryPercentage: 0.7,
        },
      ]
    },
    options: {
      responsive: false,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom', labels: { usePointStyle: true, padding: 20 } },
        tooltip: {
          mode: 'index',
          intersect: false,
        },
      },
      scales: {
        x: {
          stacked: false,
          grid: { display: false },
        },
        y: {
          stacked: false,
          beginAtZero: true,
          ticks: { stepSize: 1, precision: 0 },
        },
      },
    }
  })
}

// ── Filter tabs ──
const statusAppTabs = computed(() => [
  { key: 'all', label: `全部 (${runs.value.length})` },
  { key: 'COMPLETED', label: '已完成' },
  { key: 'FAILED', label: '失败' },
  { key: 'STOPPED', label: '已停止' },
])

const filteredRuns = computed(() => {
  if (activeFilter.value === 'all') return runs.value
  return runs.value.filter(r => r.status === activeFilter.value)
})

const {
  PAGE_SIZE_OPTIONS, pageSize, currentPage, totalPages, pagedItems: pagedRuns, setPageSize, goPage
} = usePagination(filteredRuns, { options: [10, 50, 100] })

const displayRowCount = computed(() => {
  if (pagedRuns.value.length === 0) return 3
  return pagedRuns.value.length
})

const tableAreaMinHeight = computed(() => (
  TABLE_TOOLBAR_HEIGHT + TABLE_HEADER_HEIGHT + displayRowCount.value * TABLE_ROW_HEIGHT
))

// ── AppTable columns（百分比宽度，铺满容器）──
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

const hasActiveFilters = computed(() => (
  (dateRange.value && dateRange.value.length === 2)
  || filterRunId.value.trim()
  || filterTaskName.value.trim()
  || filterDevice.value.trim()
  || filterCreator.value.trim()
))

function clearFilters() {
  dateRange.value = []
  filterRunId.value = ''
  filterTaskName.value = ''
  filterDevice.value = ''
  filterCreator.value = ''
  currentPage.value = 1
  fetchReports()
}

function buildFilterQuery() {
  const query = {}
  if (dateRange.value && dateRange.value.length === 2) {
    query.start_date = dateRange.value[0]
    query.end_date = dateRange.value[1]
  }
  const runId = filterRunId.value.trim()
  const taskName = filterTaskName.value.trim()
  const device = filterDevice.value.trim()
  const creator = filterCreator.value.trim()
  if (runId) query.run_id = runId
  if (taskName) query.task_name = taskName
  if (device) query.device_serial = device
  if (creator) query.creator = creator
  return query
}

function openCaseBreakdown(type, tab = 'detail') {
  router.push({
    path: `/reports/cases/${type}`,
    query: { ...buildFilterQuery(), ...(tab !== 'detail' ? { tab } : {}) },
  })
}
</script>

<template>
  <div class="doc-page wb-shell">
    <WorkbenchHeader
      title="测试报告"
      subtitle="查看历史测试执行记录，点击 Run ID 进入详细报告"
      mark="📊"
    />

    <div class="doc-body">
      <!-- Filter bar -->
      <div class="filter-bar">
        <div class="filter-fields">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            :clearable="true"
            :unlink-panels="true"
            class="filter-date"
          />
          <el-input
            v-model="filterRunId"
            placeholder="Run ID"
            clearable
            class="filter-input"
          />
          <el-input
            v-model="filterTaskName"
            placeholder="任务名称"
            clearable
            class="filter-input"
          />
          <el-input
            v-model="filterDevice"
            placeholder="设备"
            clearable
            class="filter-input"
          />
          <el-input
            v-model="filterCreator"
            placeholder="创建人"
            clearable
            class="filter-input"
          />
        </div>
        <div class="filter-actions">
          <el-button class="wb-btn"
            v-if="hasActiveFilters"
            size="small"
            @click="clearFilters"
          >清空条件</el-button>
          <span v-if="summary" class="filter-summary">
            共 {{ summary.total_runs }} 次执行 · {{ summary.total_iterations }} 次迭代
          </span>
        </div>
      </div>

      <!-- KPI Summary Cards -->
      <div v-if="summary" class="kpi-row">
        <div class="kpi-card">
          <div class="kpi-accent accent-teal"></div>
          <div class="kpi-value">{{ summary.total_runs }}</div>
          <div class="kpi-label">总执行次数</div>
        </div>
        <div class="kpi-card kpi-card--clickable" @click="openCaseBreakdown('pass')">
          <div class="kpi-accent accent-green"></div>
          <div class="kpi-value num-pass">{{ summary.total_pass }}</div>
          <div class="kpi-label">✅ 通过</div>
        </div>
        <div class="kpi-card kpi-card--clickable" @click="openCaseBreakdown('fail', 'bugs')">
          <div class="kpi-accent accent-red"></div>
          <div class="kpi-value num-fail">{{ summary.total_fail }}</div>
          <div class="kpi-label">❌ 失败</div>
          <div v-if="bugSummary" class="kpi-sub kpi-sub--bug">
            <span class="kpi-sub-num kpi-sub-num--bug">{{ bugSummary.unique_issues }}</span> 类 BUG ·
            <span class="kpi-sub-num kpi-sub-num--occur">{{ bugSummary.total_occurrences }}</span> 次出现 ·
            <span class="kpi-sub-num kpi-sub-num--case">{{ bugSummary.affected_cases }}</span> 个用例
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-accent accent-yellow"></div>
          <div class="kpi-value" :class="summary.pass_rate >= 95 ? 'num-pass' : summary.pass_rate >= 80 ? 'num-warn' : 'num-fail'">
            {{ summary.pass_rate }}%
          </div>
          <div class="kpi-label">📊 总通过率</div>
          <div class="kpi-sub kpi-sub--iter">
            <span class="kpi-sub-num">{{ summary.total_iterations }}</span> 次迭代
          </div>
        </div>
      </div>

      <!-- Trend Charts -->
      <div v-if="trend && trend.labels?.length" class="chart-section">
        <div class="chart-toolbar">
          <span class="toolbar-label">图表范围</span>
          <div class="page-size-btns">
            <button
              v-for="opt in CHART_RANGE_OPTIONS"
              :key="opt.key"
              type="button"
              class="page-size-btn"
              :class="{ active: chartRange === opt.key }"
              @click="setChartRange(opt.key)"
            >{{ opt.label }}</button>
          </div>
          <span class="chart-hint">固定显示 {{ CHART_VISIBLE_DAYS }} 天 · 默认最近 {{ CHART_VISIBLE_DAYS }} 天 · 左滑查看更早（共 {{ trend.labels.length }} 天）</span>
        </div>
        <div class="chart-row">
        <AppCard color="brown" pattern="brown" class="chart-card">
          <h4 class="chart-title">通过率趋势</h4>
          <div id="chartScrollPass" class="chart-scroll" @scroll="syncChartScroll('pass')">
            <div id="chartInnerPass" class="chart-inner">
              <div class="chart-wrap"><canvas id="overviewPassRateCanvas"></canvas></div>
            </div>
          </div>
        </AppCard>
        <AppCard color="brown" pattern="brown" class="chart-card">
          <h4 class="chart-title">每日通过/失败</h4>
          <div id="chartScrollDaily" class="chart-scroll" @scroll="syncChartScroll('daily')">
            <div id="chartInnerDaily" class="chart-inner">
              <div class="chart-wrap"><canvas id="overviewDailyCountCanvas"></canvas></div>
            </div>
          </div>
        </AppCard>
        </div>
      </div>

      <!-- Filter AppTabs -->
      <AppTabs
        class="report-tabs"
        :style="{ minHeight: `${tableAreaMinHeight + 88}px` }"
        :items="statusTabs"
        v-model="activeFilter"
        :leaf-animation="true"
        :shadow="true"
      >
        <template v-for="tab in statusTabs" #[tab.key] :key="tab.key">
          <AppCard
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
                  <el-button class="wb-btn" size="small" :disabled="currentPage <= 1" @click="goPage(currentPage - 1)">上一页</el-button>
                  <el-button class="wb-btn" size="small" :disabled="currentPage >= totalPages" @click="goPage(currentPage + 1)">下一页</el-button>
                </div>
              </div>
            </div>
            <AppTable
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
            </AppTable>
          </AppCard>
        </template>
      </AppTabs>
    </div>
  </div>
</template>

<style scoped src="./index.css"></style>
