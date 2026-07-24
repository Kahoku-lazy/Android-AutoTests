<script setup>

import AppCard from "@/shared/components/AppCard.vue";
import AppTabs from "@/shared/components/AppTabs.vue";
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import PageHeader from '@/shared/components/PageHeader.vue'
import { getCaseBreakdown } from './api.js'

const route = useRoute()
const router = useRouter()

const resultType = computed(() => String(route.params.resultType || 'pass'))
const isPass = computed(() => resultType.value === 'pass')

const loading = ref(false)
const data = ref(null)
const expandedCases = ref(new Set())
const expandedTasks = ref(new Set())
const expandedBugCases = ref(new Set())
const activeTab = ref('detail')

const pageTitle = computed(() => {
  if (!isPass.value && activeTab.value === 'bugs') return 'BUG 问题汇总'
  return isPass.value ? '已通过用例' : '执行失败用例'
})
const pageSubtitle = computed(() => {
  if (!isPass.value && activeTab.value === 'bugs') {
    return '相同用例的失败问题合并统计，相同问题记录次数，不同问题分别罗列'
  }
  return isPass.value
    ? '按用例名称 → 任务 ID 查看通过记录'
    : '按用例名称 → 任务 ID → 步骤失败详情查看'
})

const viewAppTabs = computed(() => {
  if (isPass.value) return []
  const bugs = bugSummary.value?.unique_issues || 0
  return [
    { key: 'bugs', label: `BUG 问题汇总 (${bugs})` },
    { key: 'detail', label: '失败明细' },
  ]
})

const groups = computed(() => data.value?.groups || [])
const bugSummary = computed(() => data.value?.bug_summary || null)
const bugCases = computed(() => bugSummary.value?.cases || [])
const totalCount = computed(() => data.value?.total || 0)

function filterParamsFromQuery() {
  const q = route.query
  const params = {}
  if (q.start_date) params.start_date = q.start_date
  if (q.end_date) params.end_date = q.end_date
  if (q.run_id) params.run_id = q.run_id
  if (q.task_name) params.task_name = q.task_name
  if (q.device_serial) params.device_serial = q.device_serial
  if (q.creator) params.creator = q.creator
  return params
}

async function loadData() {
  if (!['pass', 'fail'].includes(resultType.value)) {
    router.replace('/reports')
    return
  }
  const tab = route.query.tab
  activeTab.value = (tab === 'bugs' && resultType.value === 'fail') ? 'bugs' : 'detail'
  loading.value = true
  expandedCases.value = new Set()
  expandedTasks.value = new Set()
  expandedBugCases.value = new Set()
  try {
    const { data: resp } = await getCaseBreakdown(resultType.value, filterParamsFromQuery())
    if (resp.ok) {
      data.value = resp
      expandedCases.value = new Set((resp.groups || []).map(g => g.case_title))
      expandedBugCases.value = new Set((resp.bug_summary?.cases || []).map(c => c.case_title))
    } else {
      data.value = null
    }
  } catch (_) {
    data.value = null
  }
  loading.value = false
}

onMounted(loadData)
watch(() => [route.params.resultType, route.query], loadData, { deep: true })

function goBack() { router.push('/reports') }

function toggleCase(key) {
  const s = new Set(expandedCases.value)
  if (s.has(key)) s.delete(key)
  else s.add(key)
  expandedCases.value = s
}

function toggleTask(key) {
  const s = new Set(expandedTasks.value)
  if (s.has(key)) s.delete(key)
  else s.add(key)
  expandedTasks.value = s
}

function taskKey(caseTitle, taskId) {
  return `${caseTitle}::${taskId}`
}

function toggleBugCase(key) {
  const s = new Set(expandedBugCases.value)
  if (s.has(key)) s.delete(key)
  else s.add(key)
  expandedBugCases.value = s
}

function stepTypeLabel(type) {
  const map = {
    click: '点击', long_click: '长按', swipe: '滑动',
    wait: '等待出现', wait_disappear: '等待消失',
    verify_text: '校验文字', poll_text: '轮询文本',
    start_app: '启动应用', kill_app: '关闭应用', sleep: '暂停',
    perf_element_time: '等待元素出现耗时',
    wait_toast: '等待Toast', if_element_appear: '如果出现', if_element_disappear: '如果消失',
    loop_n: '循环N次', loop_elements: '遍历元素',
    iteration: '迭代失败',
  }
  return map[type] || type || '—'
}
</script>

<template>
  <div class="doc-page detail-page">
    <PageHeader
      :title="pageTitle"
      :subtitle="pageSubtitle"
      color="app-yellow"
    />

    <div class="doc-body">
      <div class="top-bar">
        <el-button size="small" @click="goBack">← 报告列表</el-button>
        <div v-if="data" class="summary-pill">
          <span :class="isPass ? 'num-pass' : 'num-fail'">{{ totalCount }}</span>
          次{{ isPass ? '通过' : '失败' }}
          · {{ groups.length }} 个用例
        </div>
      </div>

      <div v-if="data && !isPass" class="bug-kpi-row">
        <div class="bug-kpi-card">
          <div class="bug-kpi-value">{{ bugSummary?.unique_issues || 0 }}</div>
          <div class="bug-kpi-label">独立问题数</div>
        </div>
        <div class="bug-kpi-card">
          <div class="bug-kpi-value">{{ bugSummary?.total_occurrences || 0 }}</div>
          <div class="bug-kpi-label">问题出现次数</div>
        </div>
        <div class="bug-kpi-card">
          <div class="bug-kpi-value">{{ bugSummary?.affected_cases || 0 }}</div>
          <div class="bug-kpi-label">涉及用例</div>
        </div>
      </div>

      <AppTabs
        v-if="viewAppTabs.length"
        class="view-tabs"
        :items="viewAppTabs"
        v-model="activeTab"
        
        
      >
        <template #bugs>
          <div v-if="loading" class="loading-state">加载中…</div>
          <div v-else-if="!bugCases.length" class="empty-state">
            <span>🐛</span>
            <p>暂无 BUG 问题记录</p>
          </div>
          <div v-else class="bug-list">
            <div v-for="(bc, idx) in bugCases" :key="'bug-' + idx" class="bug-case-group">
              <AppCard color="red">
                <div
                  class="case-header"
                  role="button"
                  tabindex="0"
                  @click="toggleBugCase(bc.case_title)"
                  @keyup.enter="toggleBugCase(bc.case_title)"
                >
                  <span class="expand-icon" :class="{ open: expandedBugCases.has(bc.case_title) }">▶</span>
                  <div class="case-title-wrap">
                    <strong class="case-title">{{ bc.case_title }}</strong>
                    <code v-if="bc.case_id && bc.case_id !== bc.case_title" class="case-id">{{ bc.case_id }}</code>
                  </div>
                  <span class="case-meta">{{ bc.issue_count }} 类问题 · {{ bc.total_occurrences }} 次</span>
                </div>
                <div v-if="expandedBugCases.has(bc.case_title)" class="issue-list">
                  <div v-for="(issue, ii) in bc.issues" :key="ii" class="issue-row">
                    <div class="issue-head">
                      <span class="issue-count-badge">×{{ issue.count }}</span>
                      <span class="badge badge-fail">FAIL</span>
                      <span class="issue-type">{{ stepTypeLabel(issue.step_type) }}</span>
                    </div>
                    <div class="issue-body">
                      <div class="detail-item">
                        <span class="detail-label">问题描述</span>
                        <span class="detail-value">{{ issue.description || '—' }}</span>
                      </div>
                      <div class="detail-item">
                        <span class="detail-label">失败原因</span>
                        <span class="detail-value detail-error">{{ issue.result || '未知错误' }}</span>
                      </div>
                      <div class="detail-item">
                        <span class="detail-label">关联任务</span>
                        <span class="detail-value">
                          {{ issue.task_count }} 个任务
                          <code v-for="tid in issue.task_ids" :key="tid" class="task-id-inline">{{ tid }}</code>
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </AppCard>
            </div>
          </div>
        </template>
        <template #detail>
          <div v-if="loading" class="loading-state">加载中…</div>
          <div v-else-if="groups.length === 0" class="empty-state">
            <span>❌</span>
            <p>当前筛选条件下暂无失败记录</p>
            <el-button size="small" @click="goBack">返回报告列表</el-button>
          </div>
          <div v-else class="case-list">
            <div v-for="(group, idx) in groups" :key="group.case_id + '-' + idx" class="case-group">
              <AppCard color="red">
                <div
                  class="case-header"
                  role="button"
                  tabindex="0"
                  @click="toggleCase(group.case_title)"
                  @keyup.enter="toggleCase(group.case_title)"
                >
                  <span class="expand-icon" :class="{ open: expandedCases.has(group.case_title) }">▶</span>
                  <div class="case-title-wrap">
                    <strong class="case-title">{{ group.case_title }}</strong>
                    <code v-if="group.case_id && group.case_id !== group.case_title" class="case-id">{{ group.case_id }}</code>
                  </div>
                  <span class="case-meta">{{ group.count }} 次 · {{ group.tasks.length }} 个任务</span>
                </div>

                <div v-if="expandedCases.has(group.case_title)" class="task-list">
                  <div
                    v-for="task in group.tasks"
                    :key="taskKey(group.case_title, task.task_id)"
                    class="task-block"
                  >
                    <div
                      class="task-header"
                      :class="{ 'task-header--clickable': task.failed_steps?.length }"
                      :role="task.failed_steps?.length ? 'button' : undefined"
                      :tabindex="task.failed_steps?.length ? 0 : undefined"
                      @click="task.failed_steps?.length && toggleTask(taskKey(group.case_title, task.task_id))"
                      @keyup.enter="task.failed_steps?.length && toggleTask(taskKey(group.case_title, task.task_id))"
                    >
                      <span
                        v-if="task.failed_steps?.length"
                        class="expand-icon expand-icon--sm"
                        :class="{ open: expandedTasks.has(taskKey(group.case_title, task.task_id)) }"
                      >▶</span>
                      <div class="task-info">
                        <code class="task-id">{{ task.task_id }}</code>
                        <span v-if="task.task_name && task.task_name !== task.task_id" class="task-name">{{ task.task_name }}</span>
                      </div>
                      <span class="task-meta">
                        {{ task.count }} 次失败
                        <template v-if="task.failed_steps?.length">
                          · {{ task.failed_steps.length }} 条步骤
                        </template>
                      </span>
                    </div>

                    <div
                      v-if="expandedTasks.has(taskKey(group.case_title, task.task_id)) && task.failed_steps?.length"
                      class="step-list"
                    >
                      <div
                        v-for="(step, si) in task.failed_steps"
                        :key="taskKey(group.case_title, task.task_id) + '-s-' + si"
                        class="step-row"
                      >
                        <div class="step-head">
                          <span class="badge badge-fail">FAIL</span>
                          <span class="step-meta">
                            第 {{ step.iteration }} 轮
                            <template v-if="step.stepIndex >= 0"> · 步骤 {{ step.stepIndex + 1 }}</template>
                            · {{ stepTypeLabel(step.stepType) }}
                          </span>
                        </div>
                        <div class="step-detail">
                          <div class="detail-item">
                            <span class="detail-label">步骤描述</span>
                            <span class="detail-value">{{ step.description || '—' }}</span>
                          </div>
                          <div class="detail-item">
                            <span class="detail-label">失败原因</span>
                            <span class="detail-value detail-error">{{ step.result || '未知错误' }}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </AppCard>
            </div>
          </div>
        </template>
      </AppTabs>

      <template v-else>
      <div v-if="loading" class="loading-state">加载中…</div>

      <div v-else-if="groups.length === 0" class="empty-state">
        <span>{{ isPass ? '✅' : '❌' }}</span>
        <p>当前筛选条件下暂无{{ isPass ? '通过' : '失败' }}记录</p>
        <el-button size="small" @click="goBack">返回报告列表</el-button>
      </div>

      <div v-else class="case-list">
        <div v-for="(group, idx) in groups" :key="group.case_id + '-' + idx" class="case-group">
          <AppCard :color="isPass ? 'green' : 'red'">
            <div
              class="case-header"
              role="button"
              tabindex="0"
              @click="toggleCase(group.case_title)"
              @keyup.enter="toggleCase(group.case_title)"
            >
              <span class="expand-icon" :class="{ open: expandedCases.has(group.case_title) }">▶</span>
              <div class="case-title-wrap">
                <strong class="case-title">{{ group.case_title }}</strong>
                <code v-if="group.case_id && group.case_id !== group.case_title" class="case-id">{{ group.case_id }}</code>
              </div>
              <span class="case-meta">{{ group.count }} 次 · {{ group.tasks.length }} 个任务</span>
            </div>

            <div v-if="expandedCases.has(group.case_title)" class="task-list">
              <div
                v-for="task in group.tasks"
                :key="taskKey(group.case_title, task.task_id)"
                class="task-block"
              >
                <div
                  class="task-header"
                  :class="{ 'task-header--clickable': !isPass && task.failed_steps?.length }"
                  :role="!isPass && task.failed_steps?.length ? 'button' : undefined"
                  :tabindex="!isPass && task.failed_steps?.length ? 0 : undefined"
                  @click="!isPass && task.failed_steps?.length && toggleTask(taskKey(group.case_title, task.task_id))"
                  @keyup.enter="!isPass && task.failed_steps?.length && toggleTask(taskKey(group.case_title, task.task_id))"
                >
                  <span
                    v-if="!isPass && task.failed_steps?.length"
                    class="expand-icon expand-icon--sm"
                    :class="{ open: expandedTasks.has(taskKey(group.case_title, task.task_id)) }"
                  >▶</span>
                  <div class="task-info">
                    <code class="task-id">{{ task.task_id }}</code>
                    <span v-if="task.task_name && task.task_name !== task.task_id" class="task-name">{{ task.task_name }}</span>
                  </div>
                  <span class="task-meta">
                    {{ task.count }} 次{{ isPass ? '通过' : '失败' }}
                    <template v-if="!isPass && task.failed_steps?.length">
                      · {{ task.failed_steps.length }} 条步骤
                    </template>
                  </span>
                </div>

                <div
                  v-if="!isPass && expandedTasks.has(taskKey(group.case_title, task.task_id)) && task.failed_steps?.length"
                  class="step-list"
                >
                  <div
                    v-for="(step, si) in task.failed_steps"
                    :key="taskKey(group.case_title, task.task_id) + '-s-' + si"
                    class="step-row"
                  >
                    <div class="step-head">
                      <span class="badge badge-fail">FAIL</span>
                      <span class="step-meta">
                        第 {{ step.iteration }} 轮
                        <template v-if="step.stepIndex >= 0"> · 步骤 {{ step.stepIndex + 1 }}</template>
                        · {{ stepTypeLabel(step.stepType) }}
                      </span>
                    </div>
                    <div class="step-detail">
                      <div class="detail-item">
                        <span class="detail-label">步骤描述</span>
                        <span class="detail-value">{{ step.description || '—' }}</span>
                      </div>
                      <div class="detail-item">
                        <span class="detail-label">失败原因</span>
                        <span class="detail-value detail-error">{{ step.result || '未知错误' }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </AppCard>
        </div>
      </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.doc-page{display:flex;flex-direction:column;height:100%;overflow-y:auto}
.doc-body{padding:16px 20px 32px;display:flex;flex-direction:column;gap:14px;max-width:1200px;margin:0 auto;width:100%}
.top-bar{display:flex;align-items:center;gap:12px;margin-bottom:4px;flex-wrap:wrap}.top-bar .run-meta{display:flex;align-items:center;gap:10px;font-size:var(--app-size-xs);color:#999;flex-wrap:wrap}
.breakdown-tabs :deep(.el-tabs__header){margin-bottom:0}.breakdown-tabs :deep(.el-tabs__nav){border:none!important;display:flex;gap:4px}.breakdown-tabs :deep(.el-tabs__item){padding:5px 14px;font-size:var(--app-size-xs);font-weight:700;border-radius:4px 8px 4px 8px;border:2px solid transparent;color:#999;height:auto;line-height:1.4}.breakdown-tabs :deep(.el-tabs__item:hover){color:var(--ink)}.breakdown-tabs :deep(.el-tabs__item.is-active){color:var(--ink);background:var(--c-dashboard);border-color:var(--ink)}.breakdown-tabs :deep(.el-tabs__active-bar){display:none}
.kpi-row{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:4px}.kpi-card{text-align:center;padding:12px 10px 16px;background:#fff;border:3px solid var(--ink);border-radius:4px 10px 6px 8px;box-shadow:2px 3px 0 rgba(0,0,0,0.04);position:relative}.kpi-value{font-family:'Patrick Hand',cursive;font-size:var(--app-size-xl);font-weight:700;line-height:1}.kpi-label{font-size:var(--app-size-xs);font-weight:700;opacity:0.4;text-transform:uppercase;margin-top:2px}.kpi-card::after{content:'~';position:absolute;bottom:2px;right:8px;font-family:'Patrick Hand',cursive;font-size:var(--app-size-md);opacity:0.12}
.summary-bar{display:flex;flex-wrap:wrap;gap:10px;padding:10px 14px;background:#fff;border:2.5px solid var(--ink);border-radius:6px 10px 6px 10px;margin-bottom:4px;font-size:var(--app-size-xs);font-weight:600;color:var(--ink)}
.case-card{background:#fff;border:2.5px solid var(--ink);border-radius:6px 10px 6px 10px;padding:14px 16px;margin-bottom:8px}.case-card:hover{border-color:var(--c-device)}
.case-header{display:flex;align-items:center;justify-content:space-between;cursor:pointer;font-size:var(--app-size-xs);font-weight:700;margin-bottom:4px}.case-body{margin-top:8px;padding-top:8px;border-top:1.5px solid #e8e4d8;font-size:var(--app-size-xs)}.case-id{font-family:var(--app-font-mono);font-size:var(--app-size-xs);font-weight:600}
.bug-card{border-color:var(--c-runner)!important}.bug-card:hover{border-color:var(--c-runner)!important}
.badge{font-size:var(--app-size-xs);font-weight:700;padding:2px 7px;border-radius:3px 6px 3px 6px;border:1.5px solid var(--ink);display:inline-block}.badge-pass{background:var(--app-status-success-bg);color:var(--app-status-success-text)}.badge-fail{background:var(--app-status-danger-bg);color:var(--app-status-danger-text)}.badge-stopped{background:var(--app-offline);color:var(--app-text-secondary)}
.mono{font-family:var(--app-font-mono);font-size:var(--app-size-xs);font-weight:600}
.bug-kpi-row{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:4px}.bug-kpi-card{text-align:center;padding:12px 10px 16px;background:#fff;border:3px solid var(--ink);border-radius:4px 10px 6px 8px;box-shadow:2px 3px 0 rgba(0,0,0,0.04);position:relative}.bug-kpi-value{font-family:'Patrick Hand',cursive;font-size:var(--app-size-xl);font-weight:700;line-height:1}.bug-kpi-label{font-size:var(--app-size-xs);font-weight:700;opacity:0.4;text-transform:uppercase;margin-top:2px}.bug-kpi-card::after{content:'~';position:absolute;bottom:2px;right:8px;font-family:'Patrick Hand',cursive;font-size:var(--app-size-md);opacity:0.12}.num-pass{color:#2d7a2d;font-weight:700}.num-fail{color:#a03030;font-weight:700}
/* 用例列表 */
.case-list{display:flex;flex-direction:column;gap:8px}.case-list>.info-card,.case-list>[class*=case]{background:#fff;border:2.5px solid var(--ink);border-radius:6px 10px 6px 10px;padding:14px 16px;box-shadow:2px 3px 0 rgba(0,0,0,0.04)}.case-list .case-header{display:flex;align-items:center;gap:10px;cursor:pointer;font-weight:700;font-size:var(--app-size-xs)}.case-list .case-body{margin-top:10px;padding-top:10px;border-top:1.5px solid #e8e4d8}
/* 展开后的任务/步骤列表 */
.case-group{background:#fff;border:2.5px solid var(--c-runner);border-radius:6px 10px 6px 10px;overflow:hidden;margin-bottom:8px;box-shadow:2px 3px 0 rgba(0,0,0,0.04)}.case-group :deep(.el-card){border:none!important;box-shadow:none!important;border-radius:0!important}.case-group .case-header{padding:12px 14px}.case-group .case-header:hover{background:#fefdfb}.expand-icon{font-size:var(--app-size-xs);transition:transform 0.2s;color:var(--ink);opacity:0.5}.expand-icon.open{transform:rotate(90deg)}.expand-icon--sm{font-size:var(--app-size-xs)}.case-title-wrap{flex:1;min-width:0}.case-title{display:block;font-weight:700}.case-meta{font-size:var(--app-size-xs);color:#999;white-space:nowrap}
.task-list{padding:0 14px 14px;border-top:1.5px solid #e8e4d8}.task-block{margin-top:10px;border:1.5px solid #e8e4d8;border-radius:4px 8px 4px 8px;overflow:hidden}.task-header{display:flex;align-items:center;gap:8px;padding:8px 12px;background:#fefdfb;font-size:var(--app-size-xs)}.task-header--clickable{cursor:pointer}.task-header:hover{background:#f8f6f2}.task-info{flex:1;min-width:0}.task-id{font-family:var(--app-font-mono);font-size:var(--app-size-xs);font-weight:600}.task-name{font-size:var(--app-size-xs);margin-left:6px}.task-meta{font-size:var(--app-size-xs);color:#999;white-space:nowrap}
.step-list{padding:8px 12px}.step-row{margin-bottom:8px;padding:10px 12px;background:#fff;border:1.5px solid #e8e4d8;border-radius:4px 8px 4px 8px}.step-head{display:flex;align-items:center;gap:8px;margin-bottom:4px}.step-meta{font-size:var(--app-size-xs);color:#999}.step-detail{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:6px}.detail-item{display:flex;flex-direction:column;gap:2px}.detail-label{font-size:var(--app-size-xs);font-weight:700;opacity:0.4;text-transform:uppercase}.detail-value{font-size:var(--app-size-xs);font-weight:600}.detail-error{color:#a03030}
/* BUG 迭代失败列表 */
.issue-list{display:flex;flex-direction:column;gap:8px;padding:8px 0}.issue-row{background:#fff;border:2px solid var(--c-runner);border-radius:4px 8px 4px 8px;overflow:hidden}.issue-head{display:flex;align-items:center;gap:8px;padding:10px 14px;background:#FFE0DB;border-bottom:1.5px solid var(--c-runner)}.issue-count-badge{font-family:var(--app-font-mono);font-size:var(--app-size-xs);font-weight:700;background:#fff;color:var(--c-runner);padding:1px 7px;border-radius:3px 6px 3px 6px;border:1.5px solid var(--c-runner)}.issue-type{font-size:var(--app-size-xs);font-weight:700}.issue-body{padding:12px 14px}.task-id-inline{font-family:var(--app-font-mono);font-size:var(--app-size-xs);font-weight:600;background:#f8f6f2;padding:1px 5px;border-radius:3px;border:1px solid #e8e4d8}
</style>
