<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { animate, stagger } from 'animejs'
import AppCard from "@/shared/components/AppCard.vue";
import AppTable from "@/shared/components/AppTable.vue";
import AppTabs from "@/shared/components/AppTabs.vue";
import { usePagination } from '@/shared/composables/usePagination'
import WorkbenchHeader from '@/shared/components/WorkbenchHeader.vue'
import KpiCard from '@/shared/components/KpiCard.vue'
import EmptyState from '@/shared/components/patterns/EmptyState.vue'
import ErrorState from '@/shared/components/patterns/ErrorState.vue'
import { listRuns, statusLabel, statusBadgeClass, formatTime } from './api'
import PassRateTrendChart from './components/PassRateTrendChart.vue'
import DailyPassFailChart from './components/DailyPassFailChart.vue'
import {
  CHART_RANGE_OPTIONS,
  CHART_VISIBLE_DAYS,
  EMPTY_TEXT,
  PAGE_HEADER,
  PAGE_SIZE_OPTIONS,
  TABLE_COLUMNS,
} from './constants'

const runs = ref([])
const summary = ref(null)
const loading = ref(false)
const error = ref(null)
const lastUpdated = computed(() => {
  if (!runs.value.length) return ''
  const latest = runs.value.reduce((a, b) =>
    new Date(a.started_at) > new Date(b.started_at) ? a : b
  )
  return formatTime(latest.started_at)
})
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
    if (data.status) {
      runs.value = data.runs || []
      summary.value = data.summary || null
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

const statusAppTabs = computed(() => [
  { key: 'all', label: `全部 (${runs.value.length})` },
  { key: 'completed', label: '已完成' },
  { key: 'failed', label: '失败' },
  { key: 'stopped', label: '已停止' },
])

const filteredRuns = computed(() => {
  if (activeFilter.value === 'all') return runs.value
  if (activeFilter.value === 'completed') {
    return runs.value.filter(r => r.status === 'completed' || r.status === 'success')
  }
  return runs.value.filter(r => r.status === activeFilter.value)
})

const {
  pageSize, currentPage, totalPages, pagedItems: pagedRuns, setPageSize, goPage
} = usePagination(filteredRuns, { options: PAGE_SIZE_OPTIONS })

const columns = TABLE_COLUMNS

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
</script>

<template>
  <div class="doc-page doc-page--fixed wb-shell report-workbench">
    <WorkbenchHeader
      :title="PAGE_HEADER.title"
      :subtitle="PAGE_HEADER.subtitle"
      :icon="PAGE_HEADER.icon"
      :icon-gradient="PAGE_HEADER.iconGradient"
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
          <el-input v-model="filterRunId" placeholder="任务 ID" clearable class="filter-input" />
          <el-input v-model="filterTaskName" placeholder="任务名称" clearable class="filter-input" />
          <el-input v-model="filterDevice" placeholder="设备" clearable class="filter-input" />
          <el-input v-model="filterCreator" placeholder="创建人" clearable class="filter-input" />
          <el-button class="btn-sm" v-if="hasActiveFilters" size="small" @click="clearFilters">清空条件</el-button>
          <span v-if="summary" class="filter-summary">共 {{ summary.total_runs }} 次执行</span>
        </div>

      <!-- KPI -->
      <div v-if="summary" class="kpi-row">
        <KpiCard :value="summary.total_runs" label="总执行次数" color="var(--c-workflow)" shape="diamond" />
        <KpiCard :value="summary.total_pass" label="通过" color="var(--c-device)" shape="triangle" />
        <KpiCard :value="summary.total_fail" label="失败" color="var(--c-runner)" shape="square" />
        <KpiCard :value="`${summary.pass_rate}%`" label="通过率" color="var(--c-dashboard)" shape="circle" />
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
      <section class="doc-section report-table-section">
        <div class="doc-section__header">
          <h3 class="doc-section__title">测试报告 <span class="doc-tag">Reports</span></h3>
        </div>
        <ErrorState v-if="error && !loading" :message="error" @retry="fetchReports" />
      <AppTabs
        class="report-tabs"
        :items="statusAppTabs"
        v-model="activeFilter"
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
              :empty-text="EMPTY_TEXT.noData"
              accent="var(--c-report)"
              class="report-table report-table--flow"
            >
              <template #cell-run_id="{ record }">
                <code class="cell-run-id">{{ record.run_id }}</code>
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
                <EmptyState icon="📋" :text="EMPTY_TEXT.noRecords" :hint="EMPTY_TEXT.hint" />
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
.doc-page{display:flex;flex-direction:column;overflow:hidden!important} /* height 由外壳 :deep(.doc-page) 承担；overflow:hidden 带 !important 且实际生效，保留 */
.report-workbench .doc-body{flex:1 1 0;min-height:0;overflow-y:auto!important;padding:var(--app-space-md) var(--app-space-lg) var(--app-space-xl);display:flex;flex-direction:column;gap:var(--app-space-md)}
/* 模块私有色值登记（tokens.css 未登记该值）：表格行 hover 底色
   （原 --rg-shadow-soft 随分区卡皮肤收敛到全局 .doc-section 而成为零消费方，已删除） */
.report-workbench{--rg-hover-bg:var(--color-white) /* -> --color-white */}

/* 分区卡片：皮肤全取全局 .doc-section（背景/描边/圆角/阴影/内边距/标题字号字重，见 style.css:207-271）
   本页只保留真实差异 —— 标题的手绘波浪下划线装饰；覆写一律限定在 .report-workbench 作用域内
   （frontend-l3-container「共享骨架块不得无作用域重定义」） */
.report-workbench .doc-section__title{display:inline-block;position:relative}
.report-workbench .doc-section__title::after{content:'';position:absolute;bottom:-2px;left:0;right:0;height:2.5px;background:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 80 3'%3E%3Cpath d='M0,1.5 Q20,0 40,2 Q60,3 80,1.5' stroke='%231e1e24' stroke-width='2' fill='none'/%3E%3C/svg%3E")repeat-x;background-size:40px 3px}

/* 测试报告分区：表格贴边，内边距由本页类表达（不再用行内 style 覆写骨架块） */
.report-workbench .report-table-section{padding:0}
.report-workbench .report-table-section .doc-section__header{padding:var(--app-space-sm) var(--app-space-md) 0;margin-bottom:0}

/* KPI 网格 — 渲染由 shared/KpiCard.vue 接管 */
.kpi-row{display:grid;grid-template-columns:var(--layout-kpi-cols);gap:12px;margin-bottom:var(--app-space-sm)}
@media(max-width:800px){.kpi-row{grid-template-columns:repeat(2,1fr)}}

/* 筛选栏 */
.filter-bar{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:10px}
.filter-date{width:220px}.filter-input{width:140px}
.filter-summary{font-size:var(--app-size-xs);color:var(--app-text-secondary);font-weight:600;white-space:nowrap;margin-left:auto}
.btn-sm{padding:var(--app-space-xs) 10px;font-size:var(--app-size-xs);font-weight:700;border:2px solid var(--ink);border-radius: var(--app-radius-sm);background:var(--app-bg-card);color:var(--ink);cursor:pointer;font-family:inherit;transition:all var(--app-duration-fast)}
.btn-sm:hover{background:var(--c-report)}

/* 图表 */
.chart-section{display:flex;flex-direction:column;gap:12px}
.chart-toolbar{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.toolbar-label{font-size:var(--app-size-xs);font-weight:700;color:var(--app-text-secondary)}
.page-size-btns{display:flex;gap:var(--app-space-xs)}
.page-size-btn{padding:var(--app-space-xs) 10px;font-size:var(--app-size-xs);font-weight:700;color:var(--app-text-secondary);background:var(--app-bg-card);border:2px solid var(--app-border-light);border-radius: var(--app-radius-sm);cursor:pointer;font-family:inherit;transition:all var(--app-duration-fast)}
.page-size-btn:hover{border-color:var(--ink);color:var(--ink)}
.page-size-btn.active{background:var(--app-bg-subtle);border-color:var(--ink);color:var(--ink)}
.chart-row{display:grid;grid-template-columns:var(--layout-ratio-chart);gap:var(--app-space-md)}
@media(max-width:900px){.chart-row{grid-template-columns:1fr}}
.chart-card{padding:0}.chart-title{font-size:var(--app-size-sm);font-weight:700;margin-bottom:var(--app-space-sm)}

/* 表格工具栏（单行） */
.table-toolbar{display:flex;align-items:center;gap:10px;flex-wrap:wrap;padding:var(--app-space-sm) var(--app-space-md) 0}
.page-info{font-size:var(--app-size-xs);color:var(--app-text-secondary);font-weight:600;white-space:nowrap;margin-left:auto}
.page-nav{display:flex;gap:6px;margin-left:var(--app-space-sm)}
.page-nav-btn{padding:var(--app-space-xs) 10px;font-size:var(--app-size-xs);font-weight:700;color:var(--ink);background:var(--app-bg-card);border:2px solid var(--ink);border-radius: var(--app-radius-sm);cursor:pointer;font-family:inherit;transition:all var(--app-duration-fast)}
.page-nav-btn:hover{background:var(--c-report)}
.page-nav-btn:disabled{opacity:0.3;cursor:default}

/* 报告表格 */
.report-tabs{flex:1 1 0;min-height:0;display:flex;flex-direction:column}
.report-tabs :deep(.el-tabs__header){margin-bottom:0;padding:0 var(--app-space-md)}
.report-tabs :deep(.el-tabs__nav){border:none!important;display:flex;gap:var(--app-space-xs)}
.report-tabs :deep(.el-tabs__item){padding:5px 14px;font-size:var(--app-size-xs);font-weight:700;border-radius: var(--app-radius-sm);border:2px solid transparent;color:var(--app-text-secondary);height:auto;line-height:1.4}
.report-tabs :deep(.el-tabs__item:hover){color:var(--ink)}
.report-tabs :deep(.el-tabs__item.is-active){color:var(--ink);background:var(--c-report);border-color:var(--ink)}
.report-tabs :deep(.el-tabs__active-bar){display:none}
.report-tabs :deep(.el-tabs__content){flex:1;min-height:0;overflow-y:auto;overflow-x:hidden;padding:12px 0 0}
.table-card{background:var(--app-bg-card);border:2.5px solid var(--c-report);border-radius: var(--app-radius-md);overflow:hidden;margin:0 var(--app-space-md) 14px}

.report-table{width:100%}
.report-table :deep(.el-table__header th){background:var(--app-bg-subtle)!important;color:var(--ink)!important;font-weight:700!important;font-size:var(--app-size-xs)!important;text-transform:uppercase;letter-spacing:0.04em;border-bottom:2.5px solid var(--ink)!important}
.report-table :deep(.el-table__body td){border-bottom:1px solid var(--el-border-color-light)!important;color:var(--ink)}
.report-table :deep(.el-table__body tr:hover td){background:var(--rg-hover-bg)!important}

.cell-run-id{font-family:var(--app-font-mono);font-size:var(--app-size-xs);font-weight:600}
.badge{font-size:var(--app-size-xs);font-weight:700;padding:2px 7px;border-radius: var(--el-border-radius-small);border:1.5px solid var(--ink);display:inline-block}
.badge-pass{background:var(--app-status-success-bg);color:var(--app-status-success-text)}
.badge-fail{background:var(--app-status-danger-bg);color:var(--app-status-danger-text)}
.badge-running{background:var(--app-pending);color:var(--app-pending-text)}
.badge-stopped{background:var(--app-offline);color:var(--app-text-secondary)}
</style>
