<script setup>

import AppCard from "@/shared/components/AppCard.vue";
import AppTabs from "@/shared/components/AppTabs.vue";
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import PageHeader from '@/shared/components/PageHeader.vue'
import KpiCard from '@/shared/components/KpiCard.vue'
import { getCaseBreakdown } from './api'

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
    if (resp.status) {
      data.value = resp
      expandedCases.value = new Set((resp.groups || []).map(g => g.case_title))
      expandedBugCases.value = new Set((resp.bug_summary?.cases || []).map(c => c.case_title))
    } else {
      data.value = null
    }
  } catch (e) {
    data.value = null
    console.error(e);
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

      <div v-if="data && !isPass" class="kpi-row" style="grid-template-columns:repeat(3,1fr)">
        <KpiCard :value="bugSummary?.unique_issues || 0" label="独立问题数" color="var(--c-runner)" shape="diamond" />
        <KpiCard :value="bugSummary?.total_occurrences || 0" label="问题出现次数" color="var(--c-dashboard)" shape="triangle" />
        <KpiCard :value="bugSummary?.affected_cases || 0" label="涉及用例" color="var(--c-workflow)" shape="square" />
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
.doc-page { display: flex; flex-direction: column; height: 100%; overflow-y: auto; }
.doc-body { padding: 16px 24px 48px; display: flex; flex-direction: column; gap: 16px; width: 100%; }

/* ── Top bar ── */
.top-bar { display: flex; align-items: center; gap: 12px; margin-bottom: 4px; flex-wrap: wrap; }
.summary-pill {
  font-size:var(--app-size-sm); font-weight: 600; color: var(--ink);
  background: var(--app-bg-card); border: 2px solid var(--ink); border-radius: 20px;
  padding: 4px 14px;
}

/* ── KPI cards ── */
.kpi-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-bottom: 4px; }

/* ── Case list ── */
.case-list { display: flex; flex-direction: column; gap: 10px; }

.case-group {
  background: var(--app-bg-card); border: 2.5px solid var(--ink);
  border-radius: 10px 16px 10px 16px; overflow: hidden;
  box-shadow: 3px 4px 0 rgba(0,0,0,0.06);
  transition: box-shadow 0.2s, transform 0.15s;
}
.case-group:hover { box-shadow: 4px 6px 0 rgba(0,0,0,0.1); transform: translateY(-1px); }
.case-group :deep(.el-card) { border: none !important; box-shadow: none !important; border-radius: 0 !important; }

.case-group .case-header {
  display: flex; align-items: center; gap: 12px; cursor: pointer;
  padding: 14px 16px; transition: background 0.15s;
}
.case-group .case-header:hover { background: #fefdfb; }

.expand-icon { font-size:var(--app-size-xs); transition: transform 0.2s; color: var(--ink); opacity: 0.5; width: 14px; text-align: center; }
.expand-icon.open { transform: rotate(90deg); }
.expand-icon--sm { font-size:var(--app-size-xs); }

.case-title-wrap { flex: 1; min-width: 0; display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.case-title { font-weight: 800; font-size:var(--app-size-sm); display: flex; align-items: center; gap: 6px; }
.case-title .case-icon { font-size:var(--app-size-md); }
.case-id { font-family: var(--app-font-mono); font-size: var(--app-size-xs); background: #f0f0f0; padding: 2px 7px; border-radius: 4px; color: #666; }
.case-meta { font-size:var(--app-size-xs); color: var(--app-ink-muted); white-space: nowrap; font-weight: 600; }

/* ── Task list ── */
.task-list { padding: 0 16px 14px; border-top: 1.5px solid #eee; }
.task-block { margin-top: 8px; border: 1.5px solid #e8e4d8; border-radius: 8px; overflow: hidden; background: #fefdfb; }
.task-header { display: flex; align-items: center; gap: 8px; padding: 10px 12px; font-size:var(--app-size-xs); }
.task-header--clickable { cursor: pointer; }
.task-header:hover { background: #f6f3ee; }
.task-info { flex: 1; min-width: 0; display: flex; align-items: center; gap: 6px; }
.task-id { font-family: var(--app-font-mono); font-size: var(--app-size-xs); font-weight: 700; color: var(--ink); }
.task-name { font-size:var(--app-size-xs); color: #888; }
.task-meta { font-size:var(--app-size-xs); color: #aaa; white-space: nowrap; }

/* ── Step rows ── */
.step-list { padding: 8px 12px 4px; }
.step-row {
  margin-bottom: 8px; padding: 10px 14px; background: var(--app-bg-card);
  border: 2px solid #f0e0e0; border-radius: 8px;
}
.step-head { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.step-meta { font-size:var(--app-size-xs); color: #888; }
.step-detail { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.detail-item { display: flex; flex-direction: column; gap: 2px; }
.detail-label { font-size:var(--app-size-xs); font-weight: 700; opacity: 0.5; text-transform: uppercase; letter-spacing: 0.5px; }
.detail-value { font-size:var(--app-size-xs); font-weight: 600; }
.detail-error { color: #c0392b; }

/* ── Badge ── */
.badge { font-size:var(--app-size-xs); font-weight: 700; padding: 2px 8px; border-radius: 4px; display: inline-block; }
.badge-fail { background: rgba(232,95,95,0.12); color: #c0392b; border: 1.5px solid #e8b0b0; }
.badge-pass { background: rgba(111,186,44,0.12); color: #5a9a20; border: 1.5px solid #b0d888; }

/* ── BUG list ── */
.bug-list { display: flex; flex-direction: column; gap: 10px; }
.bug-case-group {
  background: var(--app-bg-card); border: 2.5px solid #e85f5f;
  border-radius: 10px 16px 10px 16px; overflow: hidden;
  box-shadow: 3px 4px 0 rgba(232,95,95,0.12);
}
.bug-case-group :deep(.el-card) { border: none !important; box-shadow: none !important; border-radius: 0 !important; }

.issue-list { display: flex; flex-direction: column; gap: 8px; padding: 8px 0; }
.issue-row {
  background: var(--app-bg-card); border: 2px solid #f0c0c0;
  border-radius: 8px; overflow: hidden; margin: 0 12px;
}
.issue-head {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 14px; background: #fff0ee;
  border-bottom: 1.5px solid #f0c0c0;
}
.issue-count-badge {
  font-family: var(--app-font-mono); font-size: var(--app-size-xs); font-weight: 700;
  background: var(--app-bg-card); color: #c0392b;
  padding: 2px 8px; border-radius: 4px; border: 1.5px solid #e8b0b0;
}
.issue-type { font-size:var(--app-size-sm); font-weight: 700; color: var(--ink); }
.issue-body { padding: 12px 14px; }
.task-id-inline {
  font-family: var(--app-font-mono); font-size: var(--app-size-xs); font-weight: 600;
  background: var(--app-bg-subtle); padding: 1px 6px; border-radius: 3px;
  border: 1px solid #e8e4d8; margin-left: 4px;
}

/* ── Misc ── */
.empty-state { text-align: center; padding: 60px 20px; color: var(--app-ink-muted); }
.empty-state span { font-size:var(--app-size-2xl); display: block; margin-bottom: 12px; }
.loading-state { text-align: center; padding: 40px; color: var(--app-ink-muted); }
.num-pass { color: #4a9a20; font-weight: 800; }
.num-fail { color: #c0392b; font-weight: 800; }
</style>
