<script setup>

import AppCard from "@/shared/components/AppCard.vue";
import AppTabs from "@/shared/components/AppTabs.vue";
import AppTable from "@/shared/components/AppTable.vue";
import StepScreenshotPanel from "@/shared/components/StepScreenshotPanel.vue";
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { animate, stagger } from 'animejs'
import WorkbenchHeader from '@/shared/components/WorkbenchHeader.vue'
import WorkbenchCrumbs from '@/shared/components/WorkbenchCrumbs.vue'
import KpiCard from '@/shared/components/KpiCard.vue'
import RateBar from '@/shared/components/RateBar.vue'
import ErrorState from '@/shared/components/patterns/ErrorState.vue'
import EmptyState from '@/shared/components/patterns/EmptyState.vue'
import { getTaskReport, formatTime } from './api'
import { REPORT_HEADER_GRADIENT, REPORT_HEADER_ICON } from './constants'

const route = useRoute()
const router = useRouter()
const taskId = computed(() => String(route.params.taskId))

const task = ref(null)
const loading = ref(false)
const error = ref('')
const activeTab = ref('cases')
const expandedCases = ref(new Set())
const expandedBugs = ref(new Set())

onMounted(() => loadReport())
watch(taskId, () => { expandedCases.value = new Set(); expandedBugs.value = new Set(); loadReport() })

async function loadReport() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await getTaskReport(taskId.value)
    if (data.status) task.value = data.task
    else error.value = data.message || '加载报告失败'
  } catch (e) {
    error.value = e?.response?.data?.message || e?.message || '加载报告失败'
  }
  loading.value = false
  await nextTick()
  animate('.task-report-table tbody tr', { opacity: [0, 1], translateY: [12, 0], delay: stagger(30), duration: 350, ease: 'outCubic' })
}

// ── Helpers ──
const taskMeta = computed(() => task.value || {})

const tabs = computed(() => {
  const items = [{ key: 'cases', label: '用例明细' }]
  const fails = task.value?.failed_steps?.length || 0
  if (fails > 0) items.push({ key: 'failures', label: `失败分析 (${fails})` })
  const runs = task.value?.linked_runs?.length || 0
  if (runs > 0) items.push({ key: 'history', label: `执行历史 (${runs})` })
  return items
})

const caseItems = computed(() => task.value?.case_items || [])

// KPI
const kpiPass = computed(() => task.value?.overall_pass || 0)
const kpiFail = computed(() => task.value?.overall_fail || 0)
const kpiTotal = computed(() => kpiPass.value + kpiFail.value)
const kpiRate = computed(() => task.value?.pass_rate || 0)

// APP性能统计
const perfStats = computed(() => {
  return task.value?.run?.summary?._perf || null
})

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

function stepTypeLabel(type) {
  const map = { click: '点击', long_click: '长按', swipe: '滑动',
    wait: '等待出现', wait_disappear: '等待消失',
    verify_text: '校验文字', poll_text: '轮询文本',
    start_app: '启动应用', kill_app: '关闭应用', sleep: '暂停',
    perf_element_time: '等待元素出现耗时',
    wait_toast: '等待Toast', if_element_appear: '如果出现', if_element_disappear: '如果消失',
    loop_n: '循环N次', loop_elements: '遍历元素' }
  return map[type] || type
}

function toggleCase(id) {
  const s = new Set(expandedCases.value)
  if (s.has(id)) s.delete(id); else s.add(id)
  expandedCases.value = s
}
function toggleBug(key) {
  const s = new Set(expandedBugs.value)
  if (s.has(key)) s.delete(key); else s.add(key)
  expandedBugs.value = s
}

// ── BUG entries (from failed_steps) ──
const bugEntries = computed(() => {
  const fs = task.value?.failed_steps || []
  return fs.map((f, i) => ({
    key: `${f.caseTitle}||${f.iteration}||${f.stepIndex}`,
    bugNum: i + 1,
    ...f,
  }))
})

function runStatusLabel(s) {
  const map = { completed: '通过', failed: '失败', stopped: '已停止', running: '运行中' }
  return map[s] || s
}
function runStatusClass(s) {
  if (s === 'completed') return 'badge-pass'
  if (s === 'failed') return 'badge-fail'
  return 'badge-stopped'
}

function goBack() { router.push('/reports') }
</script>

<template>
  <div v-if="error" class="doc-page wb-shell task-report-page">
    <WorkbenchHeader
      title="任务报告 Task Report"
      :icon="REPORT_HEADER_ICON"
      :icon-gradient="REPORT_HEADER_GRADIENT"
    />
    <div class="doc-body">
      <WorkbenchCrumbs
        back-to="/reports"
        back-label="报告列表"
        :items="[
          { label: '测试报告', to: '/reports' },
          { label: '任务报告' },
        ]"
      />
      <ErrorState :message="error" @retry="loadReport" />
    </div>
  </div>
  <div v-else-if="task" class="doc-page wb-shell task-report-page">
    <WorkbenchHeader
      title="任务报告 Task Report"
      :subtitle="`${taskMeta.name || taskMeta.task_id} · ${taskMeta.device_serial || '未知设备'}`"
      :icon="REPORT_HEADER_ICON"
      :icon-gradient="REPORT_HEADER_GRADIENT"
    />

    <div class="doc-body">
      <WorkbenchCrumbs
        back-to="/reports"
        back-label="报告列表"
        :items="[
          { label: '测试报告', to: '/reports' },
          { label: taskMeta.name || taskMeta.task_id || '任务报告' },
        ]"
      />
      <!-- Top bar -->
      <div class="top-bar">
        <span class="badge" :class="outcomeBadgeClass(taskMeta.outcome)" style="margin-left:auto;">
          {{ outcomeLabel(taskMeta.outcome) }}
        </span>
      </div>

      <!-- KPI Cards -->
      <div class="kpi-row">
        <KpiCard :value="kpiTotal" label="总迭代次数" color="var(--c-workflow)" shape="diamond">
          <div class="kpi-sub">{{ taskMeta.case_ids?.length || 0 }} 用例 × {{ taskMeta.loop_count || 0 }} 轮</div>
        </KpiCard>
        <KpiCard :value="kpiPass" label="通过" color="var(--c-device)" shape="triangle" />
        <KpiCard :value="kpiFail" label="失败" color="var(--c-runner)" shape="square" />
        <KpiCard :value="`${kpiRate}%`" label="通过率" color="var(--c-dashboard)" shape="circle" />
      </div>

      <!-- APP性能统计 -->
      <div v-if="perfStats" class="perf-stats-section">
        <div class="perf-stats-title">⏱️ APP性能 — 等待元素出现耗时</div>
        <div class="perf-stats-grid">
          <KpiCard :value="perfStats.count" label="🔢 测量次数" color="var(--c-workflow)" shape="square" />
          <KpiCard :value="`${perfStats.max}s`" label="⬆ 最大耗时" color="var(--c-runner)" shape="triangle" />
          <KpiCard :value="`${perfStats.min}s`" label="⬇ 最小耗时" color="var(--c-device)" shape="triangle" />
          <KpiCard :value="`${perfStats.avg}s`" label="📊 平均耗时" color="var(--c-element)" shape="diamond" />
          <KpiCard :value="`${perfStats.median}s`" label="🎯 中位数" color="var(--c-dashboard)" shape="circle" />
        </div>
      </div>

      <!-- Task info -->
      <div class="task-meta-card">
        <div class="meta-item"><span class="meta-label">📋 任务名称</span><span class="meta-value">{{ taskMeta.name }}</span></div>
        <div class="meta-item"><span class="meta-label">👤 创建人</span><span class="meta-value">{{ taskMeta.creator }}</span></div>
        <div class="meta-item"><span class="meta-label">📱 设备</span><span class="meta-value">{{ taskMeta.device_serial }}</span></div>
        <div class="meta-item"><span class="meta-label">⚙ 模式</span><span class="meta-value">{{ taskMeta.mode === 'scheduled' ? '定时' : '即时' }}</span></div>
        <div class="meta-item"><span class="meta-label">🔁 轮次</span><span class="meta-value">{{ taskMeta.loop_count }} 轮 · 间隔 {{ taskMeta.interval_seconds || 5 }}s</span></div>
        <div v-if="taskMeta.round" class="meta-item"><span class="meta-label">🔄 重试</span><span class="meta-value">第 {{ taskMeta.round }} 轮</span></div>
        <div v-if="taskMeta.conclusion" class="meta-item full-width">
          <span class="meta-label">📝 结论</span>
          <span class="meta-value conclusion-text">{{ taskMeta.conclusion }}</span>
        </div>
      </div>

      <!-- 自动化执行步骤详情 -->
      <StepScreenshotPanel :steps="task?.step_details || []" />

      <!-- AppTabs -->
      <AppTabs class="detail-tabs" :items="tabs" v-model="activeTab"  >
        <!-- ═══ TAB: 用例明细 ═══ -->
        <template #cases>
          <div v-if="caseItems.length" class="case-list">
            <div v-for="ci in caseItems" :key="ci.id" class="case-card" :class="{ expanded: expandedCases.has(ci.id) }">
              <div class="case-header" role="button" tabindex="0" @click="toggleCase(ci.id)" @keydown.enter.prevent="toggleCase(ci.id)" @keydown.space.prevent="toggleCase(ci.id)">
                <span class="case-expand-icon">▶</span>
                <span class="case-id-badge">{{ ci.id }}</span>
                <div class="case-title-area">
                  <span class="case-title-text">{{ ci.title }}</span>
                </div>
                <span class="case-status-text" :style="{ color: ci.fail > 0 ? 'var(--app-error)' : 'var(--c-workflow)', background: ci.fail > 0 ? 'var(--rg-status-fail-bg)' : 'var(--rg-status-pass-bg)' }">
                  {{ ci.fail > 0 ? '🔴 有失败' : '✅ 全部通过' }}
                </span>
                <div class="case-stats">
                  <span class="stat-total">🔁 {{ ci.total || 0 }}</span>
                  <span class="stat-pass">✅ {{ ci.pass || 0 }}</span>
                  <span class="stat-fail">❌ {{ ci.fail || 0 }}</span>
                </div>
              </div>

              <div v-if="expandedCases.has(ci.id)" class="case-body">
                <div class="step-list">
                  <div v-for="(step, si) in (ci.steps || [])" :key="si" class="step-card step-done">
                    <div class="step-strip"></div>
                    <div class="step-body">
                      <div class="step-header-row">
                        <span class="step-index">步骤 {{ si + 1 }}</span>
                        <span class="step-type-tag">{{ stepTypeLabel(step.type) || step.type }}</span>
                      </div>
                      <div class="step-desc">{{ step.description }}</div>
                      <div v-if="step.xpath" class="step-xpath">{{ step.xpath }}</div>
                    </div>
                  </div>
                </div>
                <div v-if="!ci.steps?.length" class="step-empty">暂无可展示的步骤</div>
              </div>
            </div>
          </div>
          <EmptyState v-else icon="📋" text="暂无用例数据" />
        </template>

        <!-- ═══ TAB: 失败分析 ═══ -->
        <template v-if="bugEntries.length > 0" #failures>
          <div v-for="entry in bugEntries" :key="entry.key" class="case-card bug-card" :class="{ expanded: expandedBugs.has(entry.key) }">
            <div class="case-header" role="button" tabindex="0" @click="toggleBug(entry.key)" @keydown.enter.prevent="toggleBug(entry.key)" @keydown.space.prevent="toggleBug(entry.key)">
              <span class="case-expand-icon">▶</span>
              <span class="case-id-badge" style="background:var(--app-status-danger-text);">BUG-{{ String(entry.bugNum).padStart(3, '0') }}</span>
              <div class="case-title-area">
                <span class="case-title-text">{{ entry.caseTitle }}</span>
                <div class="bug-header-sub">第 {{ entry.iteration }} 轮 · 步骤 {{ entry.stepIndex + 1 }} 失败</div>
              </div>
              <span class="case-status-text" style="color:var(--app-status-danger-text);background:var(--rg-status-fail-bg);">🔴 执行失败</span>
            </div>
            <div v-if="expandedBugs.has(entry.key)" class="case-body">
              <div class="bug-meta">
                <span><span class="bug-meta-label">🐛 BUG 编号</span> <span class="bug-meta-value">BUG-{{ String(entry.bugNum).padStart(3, '0') }}</span></span>
                <span><span class="bug-meta-label">📋 关联用例</span> <span style="font-weight:700;">{{ entry.caseTitle }}</span></span>
                <span><span class="bug-meta-label">🔁 失败轮次</span> <span class="bug-meta-value">第 {{ entry.iteration }} 轮</span></span>
                <span><span class="bug-meta-label">❌ 失败步骤</span> <span class="bug-meta-value">步骤 {{ entry.stepIndex + 1 }} · {{ entry.stepType }}</span></span>
              </div>
              <div class="step-fail-reason">
                <strong>🔍 失败原因：</strong>{{ entry.result || '步骤执行失败' }}
              </div>
            </div>
          </div>
        </template>

        <!-- ═══ TAB: 执行历史 ═══ -->
        <template v-if="(taskMeta.linked_runs || []).length > 0" #history>
          <AppCard color="" class="table-card">
            <AppTable
              :columns="[
                { title: 'Run ID', dataIndex: 'run_id', width: '220px' },
                { title: '设备', dataIndex: 'device_serial', width: '130px' },
                { title: '轮次', dataIndex: 'loop_count', width: '60px', align: 'center' },
                { title: '总数', dataIndex: 'total', width: '60px', align: 'center' },
                { title: '通过', dataIndex: 'passed', width: '60px', align: 'center' },
                { title: '失败', dataIndex: 'failed', width: '60px', align: 'center' },
                { title: '通过率', dataIndex: 'rate_bar', width: '140px' },
                { title: '状态', dataIndex: 'status_badge', width: '80px' },
                { title: '耗时', dataIndex: 'duration', width: '80px' },
                { title: '时间', dataIndex: 'started_at', width: '140px' },
              ]"
              :data-source="taskMeta.linked_runs"
              row-key="run_id"
              :striped="true"
              :loading="loading"
              empty-text="暂无关联执行记录"
              class="task-report-table"
            >
              <template #cell-run_id="{ record }">
                <code class="mono">{{ record.run_id }}</code>
              </template>
              <template #cell-rate_bar="{ record }">
                <RateBar :rate="record.rate ?? 0" :show-fail="(record.failed ?? 0) > 0" />
              </template>
              <template #cell-status_badge="{ record }">
                <span class="badge" :class="runStatusClass(record.status)">{{ runStatusLabel(record.status) }}</span>
              </template>
              <template #cell-started_at="{ record }">
                <span class="time-text">{{ formatTime(record.started_at) }}</span>
              </template>
            </AppTable>
          </AppCard>
        </template>
      </AppTabs>
    </div>
  </div>
  <div v-else class="doc-page wb-shell task-report-page">
    <WorkbenchHeader
      title="任务报告 Task Report"
      :icon="REPORT_HEADER_ICON"
      :icon-gradient="REPORT_HEADER_GRADIENT"
    />
    <div class="doc-body">
      <WorkbenchCrumbs
        back-to="/reports"
        back-label="报告列表"
        :items="[
          { label: '测试报告', to: '/reports' },
          { label: '任务报告' },
        ]"
      />
      <EmptyState icon="🔍" text="任务未找到" hint="该任务可能已删除，或链接已失效">
        <el-button class="wb-btn" @click="router.push('/reports')">← 返回报告列表</el-button>
      </EmptyState>
    </div>
  </div>
</template>

<style scoped>
.doc-page{display:flex;flex-direction:column} /* height / overflow 由外壳 :deep(.doc-page) 承担 */
.task-report-page .doc-body{padding:var(--app-space-md) var(--app-space-lg) var(--app-space-2xl);display:flex;flex-direction:column;gap:var(--app-space-md);width:100%}
/* 模块私有色值登记（tokens.css 未登记该值）：用例状态标签的通过/失败底色 */
.case-status-text{--rg-status-pass-bg:var(--color-lime-45-a10) /* -> --color-lime-45-a10 */;--rg-status-fail-bg:var(--color-red-69-a10)}
.top-bar{display:flex;align-items:center;gap:12px;margin-bottom:var(--app-space-xs);flex-wrap:wrap}
.kpi-row{display:grid;grid-template-columns:var(--layout-kpi-cols);gap:12px;margin-bottom:var(--app-space-xs)}
.task-meta-card{display:flex;flex-wrap:wrap;gap:10px;padding:12px var(--app-space-md);background:var(--app-bg-card);border:2.5px solid var(--ink);border-radius: var(--app-radius-md);margin-bottom:var(--app-space-xs);font-size:var(--app-size-xs)}.meta-item{display:flex;align-items:center;gap:6px}.meta-label{opacity:0.5;font-weight:600}.meta-value{font-weight:700}
.detail-tabs :deep(.el-tabs__header){margin-bottom:0}.detail-tabs :deep(.el-tabs__nav){border:none!important;display:flex;gap:var(--app-space-xs)}.detail-tabs :deep(.el-tabs__item){padding:5px 14px;font-size:var(--app-size-xs);font-weight:700;border-radius: var(--app-radius-sm);border:2px solid transparent;color:var(--app-text-secondary);height:auto;line-height:1.4}.detail-tabs :deep(.el-tabs__item:hover){color:var(--ink)}.detail-tabs :deep(.el-tabs__item.is-active){color:var(--ink);background:var(--c-dashboard);border-color:var(--ink)}.detail-tabs :deep(.el-tabs__active-bar){display:none}
.badge{font-size:var(--app-size-xs);font-weight:700;padding:2px 7px;border-radius: var(--el-border-radius-small);border:1.5px solid var(--ink);display:inline-block}.badge-pass{background:var(--app-status-success-bg);color:var(--app-status-success-text)}.badge-fail{background:var(--app-status-danger-bg);color:var(--app-status-danger-text)}.badge-stopped{background:var(--app-offline);color:var(--app-text-secondary)}
/* ── 用例明细 / 失败分析：卡片、步骤与失败原因
   frontend-l2-page-region「No L2 declaration without a consumer」：
   模板引用的每个类都必须有本作用域（[data-v-*]）的规则，兄弟组件的 scoped 规则作用不到本组件 ── */
.kpi-sub { font-size: var(--app-size-xs); color: var(--app-text-secondary); margin-top: var(--app-space-xs); }
.perf-stats-section { display: flex; flex-direction: column; gap: var(--app-space-sm); }
.perf-stats-title { font-size: var(--app-size-sm); font-weight: 700; color: var(--ink); }
.perf-stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: var(--app-space-md); }
.table-card, .task-report-table { width: 100%; min-width: 0; }

.case-list { display: flex; flex-direction: column; gap: var(--app-space-sm); }
.case-card { background: var(--app-bg-card); border: 2px solid var(--ink); border-radius: var(--app-radius-md); overflow: hidden; }
.case-card.expanded { box-shadow: var(--app-shadow-sm); }
.case-header { display: flex; align-items: center; gap: var(--app-space-sm); padding: var(--app-space-sm) var(--app-space-md); cursor: pointer; border-left: 4px solid var(--c-workflow); }
.case-card.bug-card .case-header { border-left-color: var(--app-status-danger); }
.case-header:hover { background: var(--app-bg-subtle); }
.case-expand-icon { font-size: var(--app-size-xs); color: var(--app-text-secondary); transition: transform var(--app-duration) var(--app-ease); }
.case-card.expanded .case-expand-icon { transform: rotate(90deg); }
.case-id-badge { font-family: var(--app-font-mono); font-size: var(--app-size-xs); font-weight: 700; color: var(--app-text-inverse); background: var(--c-element); padding: 2px var(--app-space-sm); border-radius: var(--app-radius-sm); }
.case-title-area { display: flex; flex-direction: column; gap: var(--app-space-xs); flex: 1; min-width: 0; }
.case-title-text { font-weight: 700; color: var(--ink); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.case-status-text { font-size: var(--app-size-xs); font-weight: 700; padding: 2px var(--app-space-sm); border-radius: var(--app-radius-sm); white-space: nowrap; }
.case-stats { display: flex; gap: var(--app-space-sm); font-size: var(--app-size-xs); font-weight: 700; color: var(--app-text-secondary); white-space: nowrap; }
.stat-total { color: var(--ink); }
.stat-pass { color: var(--app-status-success-text); }
.stat-fail { color: var(--app-status-danger-text); }
.case-body { border-top: 1.5px solid var(--app-border-light); padding: var(--app-space-md); background: var(--paper); }

.step-list { display: flex; flex-direction: column; gap: var(--app-space-sm); }
.step-card { display: flex; gap: var(--app-space-sm); background: var(--app-bg-card); border: 1.5px solid var(--app-border-light); border-radius: var(--app-radius-sm); padding: var(--app-space-sm) var(--app-space-md); }
.step-strip { width: 4px; flex: 0 0 4px; background: var(--c-workflow); border-radius: var(--app-radius-sm); }
.step-card.step-done .step-strip { background: var(--c-device); }
.step-body { display: flex; flex-direction: column; gap: var(--app-space-xs); min-width: 0; }
.step-header-row { display: flex; align-items: center; gap: var(--app-space-sm); }
.step-index { font-size: var(--app-size-xs); font-weight: 700; color: var(--ink); }
.step-type-tag { font-size: var(--app-size-xs); font-weight: 700; padding: 2px var(--app-space-sm); border: 1.5px solid var(--ink); border-radius: var(--app-radius-sm); background: var(--app-bg-subtle); }
.step-desc { font-size: var(--app-size-sm); color: var(--ink); }
.step-xpath { font-family: var(--app-font-mono); font-size: var(--app-size-xs); color: var(--app-text-secondary); word-break: break-all; }
.step-empty { font-size: var(--app-size-xs); color: var(--app-text-secondary); }

.bug-card { border-color: var(--app-status-danger); }
.bug-header-sub { font-size: var(--app-size-xs); color: var(--app-text-secondary); }
.bug-meta { display: flex; flex-wrap: wrap; gap: var(--app-space-sm) var(--app-space-lg); font-size: var(--app-size-xs); color: var(--ink); margin-bottom: var(--app-space-sm); }
.bug-meta-label { color: var(--app-text-secondary); font-weight: 600; }
.bug-meta-value { font-weight: 700; }
.step-fail-reason { background: var(--app-status-danger-bg); border: 1.5px solid var(--app-status-danger); border-radius: var(--app-radius-sm); color: var(--app-status-danger-text); font-size: var(--app-size-xs); padding: var(--app-space-sm) var(--app-space-md); }

.mono { font-family: var(--app-font-mono); font-size: var(--app-size-xs); }
.time-text { font-size: var(--app-size-xs); color: var(--app-text-secondary); }
.full-width { flex-basis: 100%; }
.conclusion-text { font-weight: 700; white-space: pre-wrap; }

/* 减少动效：关闭位移 / 旋转 / 缩放（颜色过渡不受影响） */
@media (prefers-reduced-motion: reduce) {
  .case-expand-icon { transition: none; }
}
</style>
