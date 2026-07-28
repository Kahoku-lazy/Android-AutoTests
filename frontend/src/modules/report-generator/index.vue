<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { animate, stagger } from 'animejs'
// Card/Table/AppTabs → AppCard/AppTable/AppTabs
import AppCard from "@/shared/components/AppCard.vue";
import AppTable from "@/shared/components/AppTable.vue";
import AppTabs from "@/shared/components/AppTabs.vue";
import { usePagination } from '@/shared/composables/usePagination.js'
import WorkbenchHeader from '@/shared/components/WorkbenchHeader.vue'
import KpiCard from '@/shared/components/KpiCard.vue'
import EmptyState from '@/shared/components/patterns/EmptyState.vue'
import ErrorState from '@/shared/components/patterns/ErrorState.vue'
import RateBar from '@/shared/components/RateBar.vue'
import { listRuns, statusLabel, statusBadgeClass, formatTime } from './api.js'
import PassRateTrendChart from './components/PassRateTrendChart.vue'
import DailyPassFailChart from './components/DailyPassFailChart.vue'
import {
  CHART_RANGE_OPTIONS,
  CHART_VISIBLE_DAYS,
} from './constants.js'

const router = useRouter()

const runs = ref([])
const summary = ref(null)
const bugSummary = ref(null)
const loading = ref(false)
const error = ref(null)
const activeFilter = ref('all')
const dateRange = ref([])
const filterRunId = ref('')
const filterTaskName = ref('')
const filterDevice = ref('')
const filterCreator = ref('')

let filterDebounceTimer = null

const trend = ref(null)

const chartRange = ref(30)

onMounted(() => {
  fetchReports()
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
})

function setChartRange(days) {
  chartRange.value = days
}

async function fetchReports() {
  loading.value = true
  error.value = null
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
  } catch (e) {
    error.value = '加载报告失败，请检查服务状态'
    console.error(e)
  }
  loading.value = false
  await nextTick()
  animate('.report-table tbody tr', { opacity: [0, 1], translateY: [16, 0], delay: stagger(40), duration: 380, ease: 'outCubic' })
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

// ── AppTable columns（报告表 11 列，使用最小宽度避免数据挤压）──
const columns = [
  { title: 'Run ID', dataIndex: 'run_id', minWidth: 220 },
  { title: '设备', dataIndex: 'device_serial', minWidth: 140 },
  { title: '任务名称', dataIndex: 'task_name', minWidth: 220 },
  { title: '创建人', dataIndex: 'creator', minWidth: 100 },
  { title: '用例数', dataIndex: 'case_count', minWidth: 78, align: 'center' },
  { title: '通过', dataIndex: 'passed', minWidth: 70, align: 'center' },
  { title: '失败', dataIndex: 'failed', minWidth: 70, align: 'center' },
  { title: '通过率', dataIndex: 'rate', minWidth: 160 },
  { title: '状态', dataIndex: 'status', minWidth: 100, align: 'center' },
  { title: '耗时', dataIndex: 'duration', minWidth: 90, align: 'center' },
  { title: '时间', dataIndex: 'started_at', minWidth: 150 },
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
      icon="file-bar-chart"
      icon-gradient="linear-gradient(135deg,#999,#8b7f8f)"
    />

    <div class="doc-body">
      <!-- 统计概览 -->
      <section class="doc-section report-stats">
        <div class="doc-section__header">
          <h3 class="doc-section__title">统计概览 <span class="doc-tag">Overview</span></h3>
          <span class="doc-section__label">测试执行统计与趋势总览</span>
        </div>
        <div class="filter-bar">
          <el-date-picker v-model="dateRange" type="daterange" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期" value-format="YYYY-MM-DD" :clearable="true" :unlink-panels="true" class="filter-date" />
          <el-input v-model="filterRunId" placeholder="Run ID" clearable class="filter-input" />
          <el-input v-model="filterTaskName" placeholder="任务名称" clearable class="filter-input" />
          <el-input v-model="filterDevice" placeholder="设备" clearable class="filter-input" />
          <el-input v-model="filterCreator" placeholder="创建人" clearable class="filter-input" />
          <el-button class="btn-sm" v-if="hasActiveFilters" size="small" @click="clearFilters">清空条件</el-button>
          <span v-if="summary" class="filter-summary">共 {{ summary.total_runs }} 次执行 · {{ summary.total_iterations }} 次迭代</span>
        </div>

      <!-- KPI -->
      <div v-if="summary" class="kpi-row">
        <KpiCard :value="summary.total_runs" label="总执行次数" color="var(--c-workflow)" shape="diamond" />
        <KpiCard :value="summary.total_pass" label="通过" color="var(--c-device)" shape="triangle" @click="openCaseBreakdown('pass')" />
        <KpiCard :value="summary.total_fail" label="失败" color="var(--c-runner)" shape="square" @click="openCaseBreakdown('fail','bugs')">
          <div v-if="bugSummary" style="font-size:var(--app-size-xs);color:#999;margin-top:4px">{{ bugSummary.unique_issues }} 类 · {{ bugSummary.total_occurrences }} 次 · {{ bugSummary.affected_cases }} 用例</div>
        </KpiCard>
        <KpiCard :value="`${summary.pass_rate}%`" label="通过率" color="var(--c-dashboard)" shape="circle">
          <div style="font-size:var(--app-size-xs);color:#999;margin-top:4px">{{ summary.total_iterations }} 次迭代</div>
        </KpiCard>
      </div>
      <div style="font-size:var(--app-size-xs);opacity:0.3;text-align:right">最近更新: {{ lastUpdated || '暂无数据' }}</div>
      </section>

      <!-- 数据图表 -->
      <section v-if="trend && trend.labels?.length" class="doc-section report-charts">
        <div class="doc-section__header">
          <h3 class="doc-section__title">数据图表 <span class="doc-tag">Trends</span></h3>
          <span class="doc-section__label">近 {{ CHART_VISIBLE_DAYS }} 天执行通过率与成功/失败分布</span>
        </div>
        <div class="chart-section">
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
          <span class="chart-hint">默认展示最近 {{ CHART_VISIBLE_DAYS }} 天 · 拖动滑块或图内滑动查看更早（共 {{ trend.labels.length }} 天）</span>
        </div>
        <div class="chart-row">
          <AppCard class="chart-card">
            <h4 class="chart-title">通过率趋势</h4>
            <PassRateTrendChart
              :labels="trend.labels"
              :rate="trend.rate"
              :visible-days="CHART_VISIBLE_DAYS"
            />
          </AppCard>
          <AppCard class="chart-card">
            <h4 class="chart-title">每日通过/失败</h4>
            <DailyPassFailChart
              :labels="trend.labels"
              :pass="trend.pass"
              :fail="trend.fail"
              :visible-days="CHART_VISIBLE_DAYS"
            />
          </AppCard>
        </div>
        </div>
      </section>

      <!-- 测试报告 -->
      <section class="doc-section report-table-section" style="padding:0">
        <div class="doc-section__header" style="padding:14px 16px 0">
          <h3 class="doc-section__title">测试报告 <span class="doc-tag">Reports</span></h3>
        </div>
        <ErrorState v-if="error && !loading" :message="error" @retry="fetchReports" />
      <AppTabs
        class="report-tabs"
        :items="statusAppTabs"
        v-model="activeFilter"
        :leaf-animation="true"
        :shadow="true"
      >
        <template v-for="tab in statusAppTabs" #[tab.key] :key="tab.key">
          <AppCard class="table-card">
            <div class="table-toolbar">
              <span class="toolbar-label">显示行数</span>
              <div class="page-size-btns">
                <button v-for="n in PAGE_SIZE_OPTIONS" :key="n" type="button" class="page-size-btn" :class="{active:pageSize===n}" @click="setPageSize(n)">{{ n }}</button>
              </div>
              <span v-if="filteredRuns.length>0" class="page-info">第 {{ currentPage }} / {{ totalPages }} 页 · 共 {{ filteredRuns.length }} 条</span>
              <div v-if="totalPages>1" class="page-nav">
                <button class="page-nav-btn" :disabled="currentPage<=1" @click="goPage(currentPage-1)">上一页</button>
                <button class="page-nav-btn" :disabled="currentPage>=totalPages" @click="goPage(currentPage+1)">下一页</button>
              </div>
            </div>
            <AppTable
              :columns="columns"
              :data-source="pagedRuns"
              row-key="run_id"
              :striped="false"
              :border="true"
              :loading="loading"
              empty-text="暂无执行记录，请先执行测试"
              class="report-table report-table--flow"
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
                <RateBar :rate="record.rate" :show-fail="record.failed > 0" />
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
                <EmptyState icon="📋" text="暂无执行记录" hint="请先在执行引擎中运行测试，完成后将自动生成报告" />
              </template>
            </AppTable>
          </AppCard>
        </template>
      </AppTabs>
      </section>
    </div>
  </div>
</template>

<style scoped>
/* Doodle Craft — 测试报告 */
.doc-page{display:flex;flex-direction:column;height:100%;overflow:hidden!important}
.doc-body{flex:1 1 0;min-height:0;overflow-y:auto!important;padding:16px 20px 32px;display:flex;flex-direction:column;gap:14px}

/* 分区卡片 — doc-section 统一样式 */
.doc-section{background:#fff;border:2.5px solid var(--ink);border-radius:6px 10px 6px 10px;padding:16px 18px;box-shadow:2px 3px 0 rgba(0,0,0,0.04)}
.doc-section__header{margin-bottom:12px}
.doc-section__title{font-family:'Patrick Hand',cursive;font-size:22px;font-weight:700;display:inline-block;position:relative;margin-bottom:6px}
.doc-section__title::after{content:'';position:absolute;bottom:-2px;left:0;right:0;height:2.5px;background:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 80 3'%3E%3Cpath d='M0,1.5 Q20,0 40,2 Q60,3 80,1.5' stroke='%231e1e24' stroke-width='2' fill='none'/%3E%3C/svg%3E")repeat-x;background-size:40px 3px}
.doc-section__title .doc-tag{font-size:var(--app-size-xs);padding:1px 8px;border-radius:4px 8px 4px 8px;background:#fff;color:#999;border:1.5px solid #e8ecf1;font-weight:700;margin-left:8px}
.doc-section__label{color:#999;font-size:var(--app-size-xs);margin-top:2px}

/* KPI 网格 — 渲染由 shared/KpiCard.vue 接管 */
.kpi-row{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:8px}
@media(max-width:800px){.kpi-row{grid-template-columns:repeat(2,1fr)}}

/* 筛选栏 */
.filter-bar{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:10px}
.filter-date{width:220px}.filter-input{width:140px}
.filter-summary{font-size:11px;color:#999;font-weight:600;white-space:nowrap;margin-left:auto}
.btn-sm{padding:4px 10px;font-size:11px;font-weight:700;border:2px solid var(--ink);border-radius:4px 8px 4px 8px;background:#fff;color:var(--ink);cursor:pointer;font-family:inherit;transition:all 0.12s}
.btn-sm:hover{background:var(--c-report)}

/* 图表 */
.chart-section{display:flex;flex-direction:column;gap:12px}
.chart-toolbar{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.toolbar-label{font-size:12px;font-weight:700;color:#999}
.page-size-btns{display:flex;gap:4px}
.page-size-btn{padding:4px 10px;font-size:11px;font-weight:700;color:#999;background:#fff;border:2px solid #e8ecf1;border-radius:4px 8px 4px 8px;cursor:pointer;font-family:inherit;transition:all 0.12s}
.page-size-btn:hover{border-color:var(--ink);color:var(--ink)}
.page-size-btn.active{background:#f8f6f2;border-color:var(--ink);color:var(--ink)}
.chart-row{display:grid;grid-template-columns:1.5fr 1fr;gap:14px}
@media(max-width:900px){.chart-row{grid-template-columns:1fr}}
.chart-card{padding:0}.chart-title{font-size:15px;font-weight:700;margin-bottom:8px}

/* 表格工具栏（单行） */
.table-toolbar{display:flex;align-items:center;gap:10px;flex-wrap:wrap;padding:8px 16px 0}
.page-info{font-size:11px;color:#999;font-weight:600;white-space:nowrap;margin-left:auto}
.page-nav{display:flex;gap:6px;margin-left:8px}
.page-nav-btn{padding:4px 10px;font-size:10px;font-weight:700;color:var(--ink);background:#fff;border:2px solid var(--ink);border-radius:4px 8px 4px 8px;cursor:pointer;font-family:inherit;transition:all 0.12s}
.page-nav-btn:hover{background:var(--c-report)}
.page-nav-btn:disabled{opacity:0.3;cursor:default}

/* 报告表格 */
.report-tabs{flex:1 1 0;min-height:0;display:flex;flex-direction:column}
.report-tabs :deep(.el-tabs__header){margin-bottom:0;padding:0 16px}
.report-tabs :deep(.el-tabs__nav){border:none!important;display:flex;gap:4px}
.report-tabs :deep(.el-tabs__item){padding:5px 14px;font-size:11px;font-weight:700;border-radius:4px 8px 4px 8px;border:2px solid transparent;color:#999;height:auto;line-height:1.4}
.report-tabs :deep(.el-tabs__item:hover){color:var(--ink)}
.report-tabs :deep(.el-tabs__item.is-active){color:var(--ink);background:var(--c-report);border-color:var(--ink)}
.report-tabs :deep(.el-tabs__active-bar){display:none}
.report-tabs :deep(.el-tabs__content){flex:1;min-height:0;overflow-y:auto;overflow-x:hidden;padding:12px 0 0}
.table-card{background:#fff;border:2.5px solid var(--c-report);border-radius:6px 10px 6px 10px;overflow:hidden;margin:0 16px 14px}

.report-table{width:100%}
.report-table :deep(.el-table__header th){background:#f8f6f2!important;color:var(--ink)!important;font-weight:700!important;font-size:11px!important;text-transform:uppercase;letter-spacing:0.04em;border-bottom:2.5px solid var(--ink)!important}
.report-table :deep(.el-table__body td){border-bottom:1px solid #e8e4d8!important;color:var(--ink)}
.report-table :deep(.el-table__body tr:hover td){background:#fefdfb!important}

.run-link{cursor:pointer;text-decoration:none;color:var(--ink)}
.cell-run-id{font-family:'JetBrains Mono',monospace;font-size:12px;font-weight:600;text-decoration:underline}
.badge{font-size:10px;font-weight:700;padding:2px 7px;border-radius:3px 6px 3px 6px;border:1.5px solid var(--ink);display:inline-block}
.status-ok{background:#C8F5D0;color:#2d7a2d}.status-fail{background:#FFE0DB;color:#a03030}.status-stopped{background:#f0ede8;color:#999}
</style>
