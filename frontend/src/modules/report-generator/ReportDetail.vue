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
import { useExpandCollapse } from '@/shared/composables/useExpandCollapse'
import { getRunReport, statusLabel, statusBadgeClass, iterBadgeClass, formatTime } from './api'

const route = useRoute()
const router = useRouter()
const runId = computed(() => String(route.params.runId))

const report = ref(null)
const loading = ref(false)
const activeTab = ref('cases')
const { expandedIds: expandedFailCases, toggle: toggleFailExpand } = useExpandCollapse()
const { expandedIds: expandedStepGroups, toggle: toggleStepGroupExpand } = useExpandCollapse()

const PAGE_SIZE_OPTIONS = [10, 20, 50, 100]
const TABLE_HEADER_HEIGHT = 45
const TABLE_ROW_HEIGHT = 41
const pageSize = ref(20)
const currentPage = ref(1)

onMounted(() => loadReport())
watch(runId, () => {
  currentPage.value = 1
  // useExpandCollapse resets on new report via re-mount
  loadReport()
})

async function loadReport() {
  if (!runId.value || runId.value === 'undefined') return
  loading.value = true
  try {
    const { data } = await getRunReport(runId.value)
    if (data.status) report.value = data.run
  } catch (e) { console.error(e); }
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

const stepDetails = computed(() => report.value?.step_details || [])

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
        <KpiCard :value="runMeta.case_count || 0" label="执行用例" color="var(--c-workflow)" shape="diamond">
          <div style="font-size:var(--app-size-xs);color:#999;margin-top:4px">{{ runMeta.loop_count || 0 }} 轮 × {{ runMeta.case_count || 0 }} 用例 = {{ runMeta.total_iterations || 0 }} 次迭代</div>
        </KpiCard>
        <KpiCard :value="runMeta.total_pass || 0" label="通过" color="var(--c-device)" shape="triangle" />
        <KpiCard :value="runMeta.total_fail || 0" label="失败" color="var(--c-runner)" shape="square" />
        <KpiCard :value="`${kpiPassRate}%`" label="通过率" color="var(--c-dashboard)" shape="circle" />
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
        
        
      >
        <!-- ═══ TAB: 用例执行明细 ═══ -->
        <template #cases>
          <AppCard color="" class="table-card">
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

            <!-- 步骤截图详情（失败步骤含图片记录） -->
            <StepScreenshotPanel v-if="stepDetails.length > 0" :steps="stepDetails" />
          </AppCard>
        </template>

        <!-- ═══ TAB: 失败分析 ═══ -->
        <template v-if="failedCases.length > 0 || failedSteps.length > 0" #failures>
          <!-- Step-level failures (from TaskCard.failed_steps) -->
          <div v-if="failedStepsByCase.length > 0" class="section-block">
            <h3 class="sec-title">
              🔍 步骤级失败详情
              <span class="sec-badge" style="background:var(--app-status-danger-text, #a03030);">{{ failedSteps.length }} 条</span>
              <span class="sec-badge sec-badge--muted">{{ failedStepsByCase.length }} 用例</span>
            </h3>
            <p class="sec-sub">按用例标题分类，点击展开查看具体失败步骤</p>
            <div v-for="(group, idx) in failedStepsByCase" :key="'fsg-' + group.key" class="fail-card">
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
            </div>
          </div>

          <!-- Iteration-level failures (from TestResult) -->
          <div v-if="failedCases.length > 0">
            <h3 class="sec-title" :style="failedSteps.length > 0 ? { marginTop: '16px' } : undefined">
              📋 迭代失败汇总
              <span class="sec-badge" style="background:var(--app-status-danger-text, #a03030);">{{ failedCases.length }} 用例</span>
            </h3>
            <p class="sec-sub">点击用例展开查看迭代失败详情</p>
            <div v-for="(c, idx) in failedCases" :key="'fail-' + c.case_id" class="fail-card">
              
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
              
            </div>
          </div>
        </template>

      </AppTabs>
    </div>
  </div>
</template>

<style scoped>
.doc-page{display:flex;flex-direction:column;height:100%;overflow-y:auto}
.doc-body{padding:16px 24px 48px;display:flex;flex-direction:column;gap:16px;width:100%}
.top-bar{display:flex;align-items:center;gap:12px;margin-bottom:4px;flex-wrap:wrap}
.run-meta{display:flex;align-items:center;gap:10px;font-size:var(--app-size-xs);color:#999;flex-wrap:wrap}
.kpi-row{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:4px}
.kpi-sub{font-size:var(--app-size-xs);color:#999;margin-top:2px}
.task-meta-bar{display:flex;flex-wrap:wrap;gap:10px;padding:12px 16px;background:#fff;border:2.5px solid var(--ink);border-radius:6px 10px 6px 10px;margin-bottom:4px;font-size:var(--app-size-xs)}.task-meta-item{display:flex;align-items:center;gap:6px}.meta-label{opacity:0.5;font-weight:600}.meta-value{font-weight:700}.full-width{width:100%}.conclusion-text{font-style:italic}
.detail-tabs :deep(.el-tabs__header){margin-bottom:0;padding:0 8px}.detail-tabs :deep(.el-tabs__nav){border:none!important;display:flex;gap:4px}.detail-tabs :deep(.el-tabs__item){padding:5px 14px;font-size:var(--app-size-xs);font-weight:700;border-radius:4px 8px 4px 8px;border:2px solid transparent;color:#999;height:auto;line-height:1.4}.detail-tabs :deep(.el-tabs__item:hover){color:var(--ink)}.detail-tabs :deep(.el-tabs__item.is-active){color:var(--ink);background:var(--c-dashboard);border-color:var(--ink)}.detail-tabs :deep(.el-tabs__active-bar){display:none}.detail-tabs :deep(.el-tabs__content){padding:12px 0 0}
.table-toolbar{display:flex;align-items:center;gap:10px;flex-wrap:wrap;padding:8px 16px 0}.page-size-btns{display:flex;gap:4px}.toolbar-label{font-size:var(--app-size-xs);font-weight:700;color:#999}.page-size-btn{padding:4px 10px;font-size:var(--app-size-xs);font-weight:700;color:#999;background:#fff;border:2px solid #e8ecf1;border-radius:4px 8px 4px 8px;cursor:pointer;font-family:inherit}.page-size-btn:hover{border-color:var(--ink);color:var(--ink)}.page-size-btn.active{background:#f8f6f2;border-color:var(--ink);color:var(--ink)}.page-info{font-size:var(--app-size-xs);color:#999;font-weight:600;white-space:nowrap;margin-left:auto}.page-nav{display:flex;gap:6px;margin-left:8px}.page-nav :deep(.el-button){padding:4px 10px;font-size:var(--app-size-xs);font-weight:700;border:2px solid var(--ink)!important;border-radius:4px 8px 4px 8px!important;background:#fff;color:var(--ink)}.page-nav :deep(.el-button:hover){background:var(--c-dashboard)}
.detail-table :deep(th){background:#f8f6f2!important;color:var(--ink)!important;font-weight:700!important;font-size:var(--app-size-xs)!important;text-transform:uppercase;letter-spacing:0.04em;border-bottom:2.5px solid var(--ink)!important}.detail-table :deep(td){border-bottom:1px solid #e8e4d8!important;color:var(--ink)}.detail-table :deep(tr:hover td){background:#fefdfb!important}
.mono{font-family:var(--app-font-mono);font-size:var(--app-size-xs);font-weight:600}.num-pass{color:#2d7a2d;font-weight:700}.num-fail{color:#a03030;font-weight:700}
.rate-cell{display:flex;align-items:center;gap:8px}.progress-bar{flex:1;height:8px;background:#f0ede8;border-radius:4px;overflow:hidden;border:1px solid var(--ink)}.p-pass{height:100%;background:var(--c-device);border-radius:3px}.p-fail{height:100%;background:var(--c-runner);border-radius:3px}.rate-text{font-size:var(--app-size-xs);font-weight:700;min-width:36px}.rate-ok{color:#2d7a2d}.rate-warn{color:#b08800}.rate-bad{color:#a03030}
.badge{font-size:var(--app-size-xs);font-weight:700;padding:2px 7px;border-radius:3px 6px 3px 6px;border:1.5px solid var(--ink);display:inline-block}.badge-pass{background:var(--app-status-success-bg);color:var(--app-status-success-text)}.badge-fail{background:var(--app-status-danger-bg);color:var(--app-status-danger-text)}.badge-stopped{background:var(--app-offline);color:var(--app-text-secondary)}.badge-warn{background:var(--app-status-warning-bg);color:#7a5a10}
/* 失败分析卡片 */
.fail-card{background:#fff;border:2.5px solid var(--c-runner);border-radius:6px 10px 6px 10px;margin-bottom:10px;overflow:hidden;box-shadow:2px 3px 0 rgba(0,0,0,0.04)}.fail-card :deep(.el-card){border:none!important;box-shadow:none!important;border-radius:0!important}.fail-card-header{display:flex;align-items:center;gap:10px;padding:12px 14px;cursor:pointer;font-size:var(--app-size-xs);font-weight:600;border-bottom:1.5px solid #e8e4d8}.fail-card-header:hover{background:#fefdfb}.expand-icon{font-size:var(--app-size-xs);transition:transform 0.2s;color:var(--ink);opacity:0.5}.expand-icon.open{transform:rotate(90deg)}.fail-case-title-wrap{flex:1;min-width:0}.fail-case-title{display:block;font-weight:700}.fail-case-id{font-family:var(--app-font-mono);font-size:var(--app-size-xs);color:#999}.fail-card-meta{font-size:var(--app-size-xs);color:#999;white-space:nowrap}.fail-expand-hint{font-size:var(--app-size-xs);color:var(--c-workflow);white-space:nowrap}
.expand-panel{padding:14px 16px;border-top:1.5px solid #e8e4d8}.expand-header{font-weight:700;font-size:var(--app-size-xs);margin-bottom:10px;color:var(--ink)}.fail-step-row{margin-bottom:10px;padding:10px 12px;background:#fefdfb;border:1.5px solid #e8e4d8;border-radius:4px 8px 4px 8px}
.fail-detail-row{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:8px}.fd-label{font-size:var(--app-size-xs);font-weight:700;opacity:0.4;text-transform:uppercase}.fd-value{font-size:var(--app-size-xs);font-weight:600}.fd-error{color:#a03030}.fail-step-row__head{display:flex;align-items:center;gap:8px;margin-bottom:4px}.fail-step-row__meta{font-size:var(--app-size-xs);color:#999}
.mini-table{width:100%;border-collapse:collapse;font-size:var(--app-size-xs);margin:8px 0}.mini-table th{background:#f8f6f2;font-weight:700;font-size:var(--app-size-xs);text-transform:uppercase;letter-spacing:0.04em;padding:6px 10px;text-align:left;border-bottom:2px solid var(--ink)}.mini-table td{padding:6px 10px;border-bottom:1px solid #e8e4d8}.row-fail td{color:#a03030}
.sec-title{font-family:'Patrick Hand',cursive;font-size:var(--app-size-md);font-weight:700;margin-top:12px;margin-bottom:8px;display:inline-block;position:relative}.sec-title::after{content:'';position:absolute;bottom:-2px;left:0;right:0;height:2px;background:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 80 3'%3E%3Cpath d='M0,1.5 Q20,0 40,2 Q60,3 80,1.5' stroke='%231e1e24' stroke-width='2' fill='none'/%3E%3C/svg%3E")repeat-x;background-size:40px 3px}.sec-badge{font-size:var(--app-size-xs);font-weight:700;padding:2px 8px;border-radius:3px 6px 3px 6px;border:1.5px solid var(--ink);margin-left:6px}.sec-sub{font-size:var(--app-size-xs);color:#999;margin-bottom:10px}
</style>
