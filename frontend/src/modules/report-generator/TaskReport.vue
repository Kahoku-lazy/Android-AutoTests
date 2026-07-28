<script setup>

import AppCard from "@/shared/components/AppCard.vue";
import AppTabs from "@/shared/components/AppTabs.vue";
import AppTable from "@/shared/components/AppTable.vue";
import StepScreenshotPanel from "@/shared/components/StepScreenshotPanel.vue";
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { animate, stagger } from 'animejs'
import PageHeader from '@/shared/components/PageHeader.vue'
import KpiCard from '@/shared/components/KpiCard.vue'
import { getTaskReport, formatTime } from './api.js'

const route = useRoute()
const router = useRouter()
const taskId = computed(() => String(route.params.taskId))

const task = ref(null)
const loading = ref(false)
const activeTab = ref('cases')
const expandedCases = ref(new Set())
const expandedBugs = ref(new Set())

onMounted(() => loadReport())
watch(taskId, () => { expandedCases.value = new Set(); expandedBugs.value = new Set(); loadReport() })

async function loadReport() {
  loading.value = true
  try {
    const { data } = await getTaskReport(taskId.value)
    if (data.ok) task.value = data.task
  } catch (e) { console.error(e); }
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
  const map = { COMPLETED: '通过', FAILED: '失败', STOPPED: '已停止', RUNNING: '运行中' }
  return map[s] || s
}
function runStatusClass(s) {
  if (s === 'COMPLETED') return 'badge-pass'
  if (s === 'FAILED') return 'badge-fail'
  return 'badge-stopped'
}

function goBack() { router.push('/reports') }
function goRunner() { router.push('/runner') }
</script>

<template>
  <div v-if="task" class="doc-page detail-page">
    <PageHeader
      title="任务报告 Task Report"
      :subtitle="`${taskMeta.name || taskMeta.task_id} · ${taskMeta.device_serial || '未知设备'}`"
      color="app-yellow"
    />

    <div class="doc-body">
      <!-- Top bar -->
      <div class="top-bar">
        <el-button size="small" @click="goBack">← 报告列表</el-button>
        <el-button size="small" @click="goRunner">← 执行引擎</el-button>
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
          <div class="kpi-card perf-stat-item">
            <div class="kpi-dot"></div>
            <div class="kpi-value">{{ perfStats.count }}</div>
            <div class="kpi-label">🔢 测量次数</div>
          </div>
          <div class="kpi-card perf-stat-item">
            <div class="kpi-dot"></div>
            <div class="kpi-value num-fail">{{ perfStats.max }}s</div>
            <div class="kpi-label">⬆ 最大耗时</div>
          </div>
          <div class="kpi-card perf-stat-item">
            <div class="kpi-dot"></div>
            <div class="kpi-value num-pass">{{ perfStats.min }}s</div>
            <div class="kpi-label">⬇ 最小耗时</div>
          </div>
          <div class="kpi-card perf-stat-item">
            <div class="kpi-dot"></div>
            <div class="kpi-value">{{ perfStats.avg }}s</div>
            <div class="kpi-label">📊 平均耗时</div>
          </div>
          <div class="kpi-card perf-stat-item">
            <div class="kpi-dot"></div>
            <div class="kpi-value">{{ perfStats.median }}s</div>
            <div class="kpi-label">🎯 中位数</div>
          </div>
        </div>
      </div>

      <!-- Task info -->
      <div class="task-meta-bar">
        <div class="task-meta-item"><span class="meta-label">📋 任务名称</span><span class="meta-value">{{ taskMeta.name }}</span></div>
        <div class="task-meta-item"><span class="meta-label">👤 创建人</span><span class="meta-value">{{ taskMeta.creator }}</span></div>
        <div class="task-meta-item"><span class="meta-label">📱 设备</span><span class="meta-value">{{ taskMeta.device_serial }}</span></div>
        <div class="task-meta-item"><span class="meta-label">⚙ 模式</span><span class="meta-value">{{ taskMeta.mode === 'scheduled' ? '定时' : '即时' }}</span></div>
        <div class="task-meta-item"><span class="meta-label">🔁 轮次</span><span class="meta-value">{{ taskMeta.loop_count }} 轮 · 间隔 {{ taskMeta.interval_seconds || 5 }}s</span></div>
        <div v-if="taskMeta.round" class="task-meta-item"><span class="meta-label">🔄 重试</span><span class="meta-value">第 {{ taskMeta.round }} 轮</span></div>
        <div v-if="taskMeta.conclusion" class="task-meta-item full-width">
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
              <div class="case-header" @click="toggleCase(ci.id)">
                <span class="case-expand-icon">▶</span>
                <span class="case-id-badge">{{ ci.id }}</span>
                <div class="case-title-area">
                  <span class="case-title-text">{{ ci.title }}</span>
                </div>
                <span class="case-status-text" :style="{ color: ci.fail > 0 ? '#e85f5f' : 'var(--c-workflow)', background: ci.fail > 0 ? 'rgba(232,95,95,0.12)' : 'rgba(111,186,44,0.1)' }">
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
          <div v-else class="empty-note"><span>📋</span><p>暂无用例数据</p></div>
        </template>

        <!-- ═══ TAB: 失败分析 ═══ -->
        <template v-if="bugEntries.length > 0" #failures>
          <div v-for="entry in bugEntries" :key="entry.key" class="case-card bug-card" :class="{ expanded: expandedBugs.has(entry.key) }">
            <div class="case-header" @click="toggleBug(entry.key)">
              <span class="case-expand-icon">▶</span>
              <span class="case-id-badge" style="background:var(--app-status-danger-text, #a03030);">BUG-{{ String(entry.bugNum).padStart(3, '0') }}</span>
              <div class="case-title-area">
                <span class="case-title-text">{{ entry.caseTitle }}</span>
                <div class="bug-header-sub">第 {{ entry.iteration }} 轮 · 步骤 {{ entry.stepIndex + 1 }} 失败</div>
              </div>
              <span class="case-status-text" style="color:var(--app-status-danger-text, #a03030);background:rgba(232,95,95,0.12);">🔴 执行失败</span>
            </div>
            <div v-if="expandedBugs.has(entry.key)" class="case-body">
              <div class="bug-meta">
                <span><span class="bug-meta-label">🐛 BUG 编号</span> <span class="bug-meta-value">BUG-{{ String(entry.bugNum).padStart(3, '0') }}</span></span>
                <span><span class="bug-meta-label">📋 关联用例</span> <span style="font-weight:700;">{{ entry.caseTitle }}</span></span>
                <span><span class="bug-meta-label">🔁 失败轮次</span> <span class="bug-meta-value">第 {{ entry.iteration }} 轮</span></span>
                <span><span class="bug-meta-label">❌ 失败步骤</span> <span class="bug-meta-value">步骤 {{ entry.stepIndex + 1 }} · {{ entry.stepType }}</span></span>
              </div>
              <div class="step-fail-reason" style="margin: 0 22px 12px; padding: 8px 12px;">
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
                <div class="rate-cell">
                  <div class="progress-bar">
                    <div class="p-pass" :style="{ width: record.rate + '%' }"></div>
                    <div v-if="record.failed > 0" class="p-fail" :style="{ width: (100 - record.rate) + '%' }"></div>
                  </div>
                  <span class="rate-text" :class="{ 'rate-ok': record.rate >= 95, 'rate-warn': record.rate >= 80 && record.rate < 95, 'rate-bad': record.rate < 80 }">{{ record.rate }}%</span>
                </div>
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
  <div v-else class="not-found">
    <p>任务未找到</p>
    <el-button @click="router.push('/reports')">← 返回报告列表</el-button>
  </div>
</template>

<style scoped>
.doc-page{display:flex;flex-direction:column;height:100%;overflow-y:auto}
.doc-body{padding:16px 24px 48px;display:flex;flex-direction:column;gap:16px;width:100%}
.top-bar{display:flex;align-items:center;gap:12px;margin-bottom:4px;flex-wrap:wrap}.run-meta{display:flex;align-items:center;gap:10px;font-size:var(--app-size-xs);color:#999;flex-wrap:wrap}
.kpi-row{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:4px}
.task-meta-card{display:flex;flex-wrap:wrap;gap:10px;padding:12px 16px;background:#fff;border:2.5px solid var(--ink);border-radius:6px 10px 6px 10px;margin-bottom:4px;font-size:var(--app-size-xs)}.meta-item{display:flex;align-items:center;gap:6px}.meta-label{opacity:0.5;font-weight:600}.meta-value{font-weight:700}
.detail-tabs :deep(.el-tabs__header){margin-bottom:0}.detail-tabs :deep(.el-tabs__nav){border:none!important;display:flex;gap:4px}.detail-tabs :deep(.el-tabs__item){padding:5px 14px;font-size:var(--app-size-xs);font-weight:700;border-radius:4px 8px 4px 8px;border:2px solid transparent;color:#999;height:auto;line-height:1.4}.detail-tabs :deep(.el-tabs__item:hover){color:var(--ink)}.detail-tabs :deep(.el-tabs__item.is-active){color:var(--ink);background:var(--c-dashboard);border-color:var(--ink)}.detail-tabs :deep(.el-tabs__active-bar){display:none}
.badge{font-size:var(--app-size-xs);font-weight:700;padding:2px 7px;border-radius:3px 6px 3px 6px;border:1.5px solid var(--ink);display:inline-block}.badge-pass{background:var(--app-status-success-bg);color:var(--app-status-success-text)}.badge-fail{background:var(--app-status-danger-bg);color:var(--app-status-danger-text)}.badge-stopped{background:var(--app-offline);color:var(--app-text-secondary)}
</style>
