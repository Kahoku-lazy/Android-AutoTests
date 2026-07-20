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
    click: '点击', wait: '等待出现', verify_text: '校验文字',
    iteration: '迭代失败', sleep: '暂停', start_app: '启动应用',
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
        :leaf-animation="true"
        :shadow="true"
      >
        <template #bugs>
          <div v-if="loading" class="loading-state">加载中…</div>
          <div v-else-if="!bugCases.length" class="empty-state">
            <span>🐛</span>
            <p>暂无 BUG 问题记录</p>
          </div>
          <div v-else class="bug-list">
            <div v-for="(bc, idx) in bugCases" :key="'bug-' + idx" class="bug-case-group">
              <AppCard color="red" pattern="red">
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
              <AppCard color="red" pattern="red">
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
          <AppCard :color="isPass ? 'green' : 'red'" :pattern="isPass ? 'green' : 'red'">
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
  padding: 0 4px 24px;
}
.top-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
.summary-pill {
  font-size: 13px;
  color: #8a7b66;
  font-weight: 600;
}
.num-pass { color: #6fba2c; font-weight: 800; }
.num-fail { color: #e05a5a; font-weight: 800; }

.bug-kpi-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}
.bug-kpi-card {
  background: rgb(247,243,223);
  border-radius: 14px;
  padding: 14px 18px;
  border: 1.5px solid rgba(224, 90, 90, 0.25);
  text-align: center;
}
.bug-kpi-value {
  font-size: 26px;
  font-weight: 900;
  color: #e05a5a;
  line-height: 1.1;
}
.bug-kpi-label {
  font-size: 12px;
  color: #9f927d;
  margin-top: 4px;
  font-weight: 600;
}

.view-tabs {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  width: 100%;
}
.view-tabs :deep(.el-tabs) {
  display: flex;
  flex-direction: column;
  overflow: visible;
}
.view-tabs :deep(.el-tabs__list) {
  flex-shrink: 0;
}
.view-tabs :deep(.el-tabs__content) {
  overflow: visible;
  display: block;
  padding-top: 12px;
}
.view-tabs :deep(.el-tabs__inner) {
  min-height: min-content;
  overflow: visible;
}

.bug-list, .case-list { display: flex; flex-direction: column; gap: 12px; }
.bug-case-group :deep(.el-card__body),
.case-group :deep(.el-card__body) { padding: 0; }

.issue-list {
  border-top: 1px solid rgba(139, 115, 85, 0.1);
  padding: 10px 18px 14px 36px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  background: rgba(139, 115, 85, 0.02);
}
.issue-row {
  background: rgba(255, 255, 255, 0.55);
  border: 1px solid rgba(224, 90, 90, 0.18);
  border-radius: 12px;
  padding: 12px 14px;
}
.issue-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}
.issue-count-badge {
  font-size: 13px;
  font-weight: 900;
  color: #fff;
  background: #e05a5a;
  border-radius: 8px;
  padding: 2px 8px;
  min-width: 36px;
  text-align: center;
}
.issue-type {
  font-size: 12px;
  font-weight: 700;
  color: #794f27;
}
.issue-body { display: flex; flex-direction: column; gap: 6px; }
.task-id-inline {
  display: inline-block;
  margin: 2px 4px 0 0;
  font-family: 'SF Mono', 'Fira Code', Consolas, monospace;
  font-size: 11px;
  color: #8a7b66;
  background: rgba(139, 115, 85, 0.08);
  padding: 1px 6px;
  border-radius: 4px;
}

.loading-state, .empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 48px 24px;
  color: #9f927d;
  text-align: center;
}
.empty-state span { font-size: 36px; }
.empty-state p { margin: 0; font-size: 15px; }

.case-header, .task-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 18px;
  cursor: pointer;
}
.case-header:hover, .task-header--clickable:hover { background: rgba(25, 200, 185, 0.05); }

.expand-icon {
  font-size: 10px;
  color: #9f927d;
  transition: transform 0.2s ease;
  flex-shrink: 0;
}
.expand-icon.open { transform: rotate(90deg); }
.expand-icon--sm { font-size: 9px; }

.case-title-wrap { flex: 1; min-width: 0; }
.case-title { font-size: 15px; color: #4a3a28; display: block; }
.case-id, .task-id {
  font-family: 'SF Mono', 'Fira Code', Consolas, monospace;
  font-size: 12px;
  color: #8a7b66;
}
.case-meta, .task-meta {
  font-size: 12px;
  color: #9f927d;
  font-weight: 600;
  white-space: nowrap;
}

.task-list {
  border-top: 1px solid rgba(139, 115, 85, 0.1);
  background: rgba(139, 115, 85, 0.02);
}
.task-block + .task-block { border-top: 1px solid rgba(139, 115, 85, 0.08); }
.task-header { padding-left: 36px; cursor: default; }
.task-header--clickable { cursor: pointer; }
.task-info { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.task-name { font-size: 13px; color: #6b5b48; }

.step-list {
  padding: 0 18px 14px 52px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.step-row {
  background: rgba(255, 255, 255, 0.5);
  border: 1px solid rgba(224, 90, 90, 0.15);
  border-radius: 12px;
  padding: 12px 14px;
}
.step-head { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.step-meta { font-size: 12px; font-weight: 700; color: #794f27; }
.badge {
  display: inline-flex;
  align-items: center;
  padding: 3px 8px;
  border-radius: 50px;
  font-size: 11px;
  font-weight: 700;
}
.badge-fail { background: rgba(224, 90, 90, 0.12); color: #c0392b; }
.step-detail { display: flex; flex-direction: column; gap: 6px; }
.detail-item { display: flex; flex-direction: column; gap: 2px; }
.detail-label { font-size: 11px; color: #9f927d; font-weight: 600; }
.detail-value { font-size: 13px; color: #4a3a28; line-height: 1.45; }
.detail-error { color: #e05a5a; font-family: 'SF Mono', 'Fira Code', Consolas, monospace; word-break: break-all; }
</style>
