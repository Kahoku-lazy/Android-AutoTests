<script setup>

import AppCard from "@/shared/components/AppCard.vue";
import AppTabs from "@/shared/components/AppTabs.vue";
import AppTable from "@/shared/components/AppTable.vue";
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { animate, stagger } from 'animejs'
import PageHeader from '@/shared/components/PageHeader.vue'
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
  } catch (_) {}
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
        <div class="kpi-card">
          <div class="kpi-accent accent-teal"></div>
          <div class="kpi-value">{{ kpiTotal }}</div>
          <div class="kpi-label">总迭代次数</div>
          <div class="kpi-sub">{{ taskMeta.case_ids?.length || 0 }} 用例 × {{ taskMeta.loop_count || 0 }} 轮</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-accent accent-green"></div>
          <div class="kpi-value num-pass">{{ kpiPass }}</div>
          <div class="kpi-label">✅ 通过</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-accent accent-red"></div>
          <div class="kpi-value num-fail">{{ kpiFail }}</div>
          <div class="kpi-label">❌ 失败</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-accent accent-yellow"></div>
          <div class="kpi-value" :class="kpiRate >= 95 ? 'num-pass' : kpiRate >= 80 ? 'num-warn' : 'num-fail'">{{ kpiRate }}%</div>
          <div class="kpi-label">📊 通过率</div>
        </div>
      </div>

      <!-- APP性能统计 -->
      <div v-if="perfStats" class="perf-stats-section">
        <div class="perf-stats-title">⏱️ APP性能 — 等待元素出现耗时</div>
        <div class="perf-stats-grid">
          <div class="kpi-card perf-stat-item">
            <div class="kpi-accent accent-teal"></div>
            <div class="kpi-value">{{ perfStats.count }}</div>
            <div class="kpi-label">🔢 测量次数</div>
          </div>
          <div class="kpi-card perf-stat-item">
            <div class="kpi-accent accent-red"></div>
            <div class="kpi-value num-fail">{{ perfStats.max }}s</div>
            <div class="kpi-label">⬆ 最大耗时</div>
          </div>
          <div class="kpi-card perf-stat-item">
            <div class="kpi-accent accent-green"></div>
            <div class="kpi-value num-pass">{{ perfStats.min }}s</div>
            <div class="kpi-label">⬇ 最小耗时</div>
          </div>
          <div class="kpi-card perf-stat-item">
            <div class="kpi-accent accent-yellow"></div>
            <div class="kpi-value">{{ perfStats.avg }}s</div>
            <div class="kpi-label">📊 平均耗时</div>
          </div>
          <div class="kpi-card perf-stat-item">
            <div class="kpi-accent accent-blue"></div>
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

      <!-- AppTabs -->
      <AppTabs class="detail-tabs" :items="tabs" v-model="activeTab" :leaf-animation="true" :shadow="true">
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
                <span class="case-status-text" :style="{ color: ci.fail > 0 ? '#e85f5f' : '#89CFF0', background: ci.fail > 0 ? 'rgba(232,95,95,0.12)' : 'rgba(111,186,44,0.1)' }">
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
              <span class="case-id-badge" style="background:#e85f5f;">BUG-{{ String(entry.bugNum).padStart(3, '0') }}</span>
              <div class="case-title-area">
                <span class="case-title-text">{{ entry.caseTitle }}</span>
                <div class="bug-header-sub">第 {{ entry.iteration }} 轮 · 步骤 {{ entry.stepIndex + 1 }} 失败</div>
              </div>
              <span class="case-status-text" style="color:#e85f5f;background:rgba(232,95,95,0.12);">🔴 执行失败</span>
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
          <AppCard color="brown" class="table-card">
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
.detail-page { display: flex; flex-direction: column; height: 100%; overflow: hidden; }
.doc-body { flex: 1; min-height: 0; display: flex; flex-direction: column; gap: 16px; overflow-y: auto; padding-bottom: 40px; }

/* ── Top bar ── */
.top-bar { display: flex; align-items: center; gap: 12px; flex-shrink: 0; }

/* ── KPI Cards ── */
.kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; flex-shrink: 0; }
.kpi-card {
  background: rgb(247,243,223); border-radius: 18px; padding: 18px 22px;
  border: 1.5px solid #c4b89e; position: relative; overflow: hidden;
  transition: transform 0.25s cubic-bezier(0.4,0,0.2,1);
}
.kpi-card:hover { transform: translateY(-2px); }
.kpi-accent { position: absolute; left: 0; top: 0; bottom: 0; width: 5px; border-radius: 0 3px 3px 0; }
.accent-teal { background: #19c8b9; }
.accent-green { background: #89CFF0; }
.accent-red { background: #e05a5a; }
.accent-yellow { background: #f5c31c; }
.kpi-value { font-size: 30px; font-weight: 900; color: #794f27; line-height: 1.1; }
.kpi-label { font-size: 12px; color: #9f927d; margin-top: 4px; font-weight: 600; }
.kpi-sub { font-size: 11px; color: #8a7b66; margin-top: 2px; }
.num-pass { color: #89CFF0; }
.num-fail { color: #e05a5a; }
.num-warn { color: #dba90e; }

/* ── Task meta bar ── */
.task-meta-bar {
  display: flex; flex-wrap: wrap; gap: 10px 24px;
  padding: 14px 20px;
  background: linear-gradient(135deg, #fef9ef 0%, #fdf0d5 100%);
  border-radius: 14px; border: 1px solid rgba(139,115,85,0.1);
  flex-shrink: 0;
}
.task-meta-item { display: flex; align-items: center; gap: 6px; font-size: 13px; }
.task-meta-item.full-width { flex-basis: 100%; }
.meta-label { color: #9f927d; font-weight: 500; white-space: nowrap; }
.meta-value { color: #4a3a28; font-weight: 600; }
.conclusion-text { line-height: 1.5; font-style: italic; }

/* ── AppTabs ── */
.detail-tabs { flex: 1; min-height: 0; display: flex; flex-direction: column; }
.detail-tabs :deep(.el-tabs) { flex: 1; min-height: 0; display: flex; flex-direction: column; overflow: hidden; }
.detail-tabs :deep(.el-tabs__content) { flex: 1; min-height: 0; overflow-x: hidden; overflow-y: auto; display: block; padding-top: 14px; }
.detail-tabs :deep(.el-tabs__inner) { min-height: min-content; }

/* ── Case cards ── */
.case-list { display: flex; flex-direction: column; gap: 10px; }
.case-card {
  background: rgb(247,243,223); border: 1px solid #e8e2d6;
  border-radius: 18px; overflow: hidden;
  transition: all 0.25s cubic-bezier(0.4,0,0.2,1);
  box-shadow: 0 1px 3px rgba(61,52,40,0.05);
}
.case-card:hover { transform: translateY(-1px); box-shadow: 0 4px 14px rgba(61,52,40,0.08); }
.case-card.expanded { border-color: #c4b89e; }
.case-card.bug-card { border-left: 4px solid #e85f5f; }

.case-header {
  display: flex; align-items: center; gap: 12px;
  padding: 14px 20px; cursor: pointer; user-select: none;
  transition: background 0.15s;
}
.case-header:hover { background: rgba(245,240,215,0.8); }
.case-expand-icon {
  font-size: 11px; color: #9f927d; width: 16px; flex-shrink: 0;
  transition: transform 0.25s cubic-bezier(0.4,0,0.2,1);
}
.case-card.expanded .case-expand-icon { transform: rotate(90deg); }

.case-id-badge {
  font-size: 11px; font-weight: 700; color: #fff; background: #19c8b9;
  padding: 3px 10px; border-radius: 50px; flex-shrink: 0;
}
.case-title-area { flex: 1; min-width: 0; }
.case-title-text { font-size: 15px; font-weight: 700; color: #4A3A28; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.bug-header-sub { font-size: 11px; color: #9f927d; margin-top: 2px; }
.case-status-text { font-size: 11px; font-weight: 600; padding: 2px 10px; border-radius: 50px; flex-shrink: 0; }
.case-stats { display: flex; gap: 14px; font-size: 12px; font-weight: 600; color: #725d42; flex-shrink: 0; }
.stat-total { color: #9f927d; }
.stat-pass { color: #89CFF0; }
.stat-fail { color: #e85f5f; }

/* ── Case body (step cards) ── */
.case-body { padding-bottom: 2px; }
.step-list { padding: 0 20px 16px 36px; display: flex; flex-direction: column; gap: 8px; }
.step-empty { padding: 20px 20px 16px 36px; color: #9f927d; font-size: 13px; text-align: center; }

.step-card {
  display: flex; align-items: stretch; border-radius: 12px;
  overflow: hidden; transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
  box-shadow: 0 2px 4px 0 rgba(61,52,40,0.06);
  border: 1px solid #e8e2d6;
}
.step-strip { width: 5px; flex-shrink: 0; border-radius: 5px 0 0 5px; }
.step-body { flex: 1; padding: 12px 16px; background: #fff; display: flex; flex-direction: column; gap: 4px; }
.step-header-row { display: flex; align-items: center; gap: 8px; }
.step-index { font-size: 12px; font-weight: 800; color: #9f927d; font-family: 'Cascadia Code', Consolas, monospace; }
.step-type-tag {
  font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 8px;
  background: rgba(139,115,85,0.08); color: #8b7355; text-transform: uppercase;
}
.step-desc { font-size: 13px; font-weight: 600; color: #725d42; line-height: 1.4; }
.step-xpath { font-size: 11px; color: #9f927d; font-family: 'Cascadia Code', Consolas, monospace; margin-top: 2px; }

.step-done .step-strip { background: #89CFF0; }
.step-done .step-body { background: rgba(111,186,44,0.03); }

/* ── BUG meta ── */
.bug-meta {
  display: flex; gap: 20px; flex-wrap: wrap;
  margin: 0 20px 10px; padding: 10px 14px;
  background: rgba(232,95,95,0.04); border-radius: 10px;
  border: 1px dashed rgba(232,95,95,0.2);
  font-size: 12px; font-weight: 600; color: #725d42;
}
.bug-meta-label { color: #9f927d; }
.bug-meta-value { color: #e85f5f; font-weight: 700; }
.step-fail-reason {
  font-size: 12px; font-weight: 600; color: #e85f5f;
  background: rgba(232,95,95,0.05); border-radius: 8px;
  border-left: 3px solid #e85f5f; line-height: 1.5;
}

/* ── AppTable card ── */
.table-card { overflow: hidden; }
.table-card :deep(.el-card__body) { padding: 0; border-radius: 14px; overflow: hidden; }

.task-report-table :deep(th) {
  font-size: 12px; font-weight: 700; color: #6b5b48; padding: 12px 14px;
  background: rgba(139,115,85,0.06); border-bottom: 2px solid rgba(139,115,85,0.12);
  text-transform: uppercase; letter-spacing: 0.3px; white-space: nowrap;
}
.task-report-table :deep(td) {
  padding: 10px 14px; font-size: 13px; color: #4a3a28;
  border-bottom: 1px dashed rgba(196,184,158,0.4); vertical-align: middle;
}
.task-report-table :deep(tr:hover td) { background: rgba(25,200,185,0.04); }

/* ── Misc ── */
.mono { font-family: 'SF Mono','Fira Code','Cascadia Code',Consolas,monospace; font-size: 10px; font-weight: 600; background: rgba(139,115,85,0.06); padding: 2px 6px; border-radius: 4px; }
.time-text { font-size: 12px; color: #8a7b66; white-space: nowrap; }

.rate-cell { display: flex; align-items: center; gap: 8px; }
.progress-bar { display: flex; height: 7px; border-radius: 50px; overflow: hidden; background: #f0ece2; flex: 1; max-width: 90px; }
.p-pass { background: #89CFF0; transition: width 0.5s ease; border-radius: 50px; }
.p-fail { background: #e05a5a; transition: width 0.5s ease; border-radius: 50px; }
.rate-text { font-weight: 700; font-size: 12px; min-width: 38px; text-align: right; }
.rate-ok { color: #89CFF0; }
.rate-warn { color: #dba90e; }
.rate-bad { color: #e05a5a; }

.badge { display: inline-flex; align-items: center; padding: 3px 10px; border-radius: 50px; font-size: 10px; font-weight: 700; letter-spacing: 0.02em; }
.badge-pass { background: rgba(111,186,44,0.12); color: #89CFF0; border: 1.5px solid rgba(111,186,44,0.25); }
.badge-fail { background: rgba(224,90,90,0.12); color: #e05a5a; border: 1.5px solid rgba(224,90,90,0.25); }
.badge-stopped { background: rgba(138,123,102,0.10); color: #8a7b66; border: 1.5px solid rgba(138,123,102,0.20); }

.empty-note { text-align: center; padding: 48px 24px; color: #9f927d; }
.empty-note span { font-size: 36px; display: block; margin-bottom: 12px; }
.not-found { text-align: center; color: #9f927d; padding: 80px 0; font-size: 15px; }
.not-found p { margin-bottom: 16px; }

@media (max-width: 900px) { .kpi-row { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 600px) { .kpi-row { grid-template-columns: 1fr; } }
</style>
