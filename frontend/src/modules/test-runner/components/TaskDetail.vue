<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import client from '@/shared/api-client.js'
// Button → el-button (Element Plus auto-import)
import ConfirmButton from '@/shared/components/patterns/ConfirmButton.vue'
import PageHeader from '@/shared/components/PageHeader.vue'
import {
  isTaskQueued,
  taskStatusInfo as getTaskStatusInfo,
  taskProgress as calcTaskProgress,
  taskCompletedCount,
  taskTotalCount,
  buildTaskSavePayload,
  generateTaskId,
} from '../composables/taskUtils.js'
import {
  connectTaskWebSocket,
  closeTaskWebSocket,
  applyWsMessage,
} from '../composables/useTaskWebSocket.js'
import { getActiveRuns, listDefinitions } from '../api.js'
import { listApiDefinitions } from '@/modules/case-manager/api/apiTesting.js'
import { listWebDefinitions } from '@/modules/case-manager/api/webAutomation.js'

const route = useRoute()
const router = useRouter()
const taskId = computed(() => String(route.params.taskId))

const WS_KEY = '_task_ws_map'
const task = ref(null)
const casesDefs = ref([])   // full case definitions (with steps)

// ── Expand / collapse ──
const expandedCases = ref(new Set())
const expandedBugs = ref(new Set())

function toggleCase(id) {
  const s = new Set(expandedCases.value)
  if (s.has(id)) { s.delete(id) } else { s.add(id) }
  expandedCases.value = s
}
function toggleBug(key) {
  const s = new Set(expandedBugs.value)
  if (s.has(key)) { s.delete(key) } else { s.add(key) }
  expandedBugs.value = s
}

async function loadTask() {
  try {
    const { data } = await client.get('/runner/tasks')
    if (data.ok && data.tasks) {
      const tid = String(taskId.value)
      task.value = data.tasks.find(t => String(t.id) === tid) || null
      if (!task.value) {
        console.warn(`[TaskDetail] task not found on server: id="${tid}"`)
      } else {
        // Auto-expand currently running case
        if (task.value.running && task.value.currentCaseTitle) {
          const running = task.value.caseItems?.find(
            c => c.title === task.value.currentCaseTitle
          )
          if (running) expandedCases.value = new Set([running.id])
        }
        // Ensure caseItems have step definitions
        await ensureStepDefs()
      }
    }
  } catch (e) {
    console.error('[TaskDetail] loadTask error:', e)
  }
}

// Fetch case definitions and inject step lists into caseItems if missing.
// Also creates caseItems from scratch when task has caseIds but empty caseItems.
async function ensureStepDefs() {
  const t = task.value; if (!t) return
  const hasCaseIds = (t.caseIds || []).length > 0
  const hasCaseItems = (t.caseItems || []).length > 0
  const missingSteps = hasCaseItems && t.caseItems.some(ci => !ci.steps?.length)
  if (!hasCaseIds) return
  if (hasCaseItems && !missingSteps) return  // already have steps

  // Load case definitions once, using the right API per task type
  const taskType = t.taskType || 'ui_automation'
  if (!casesDefs.value.length) {
    try {
      let data
      if (taskType === 'api_testing') {
        const res = await listApiDefinitions()
        data = res.data
      } else if (taskType === 'web_automation') {
        const res = await listWebDefinitions()
        data = res.data
      } else {
        const res = await listDefinitions()
        data = res.data
      }
      if (data?.ok) casesDefs.value = data.definitions || []
    } catch (_) {}
  }

  const idSet = new Set((t.caseIds || []).map(String))

  // If caseItems is empty, create from scratch
  if (!hasCaseItems) {
    t.caseItems = casesDefs.value
      .filter(c => idSet.has(String(c.id)))
      .map((c, i) => {
        let rawSteps = c.steps_data || []
        if (!rawSteps.length && c.steps_json) {
          try { rawSteps = JSON.parse(c.steps_json) } catch (_) {}
        }
        return {
          id: c.id, title: c.title, index: i + 1, status: 'pending',
          pass: 0, fail: 0, total: t.loopCount, rate: 0,
          steps: rawSteps.map(s => ({
            type: s.type || '', xpath: s.xpath || '',
            description: s.description || s.xpath || s.expected_text || '',
          })),
        }
      })
    return
  }

  // Otherwise inject missing steps into existing caseItems
  for (const ci of t.caseItems) {
    if (ci.steps?.length) continue
    const def = casesDefs.value.find(d => String(d.id) === String(ci.id))
    if (def) {
      let rawSteps = def.steps_data || []
      if (!rawSteps.length && def.steps_json) {
        try { rawSteps = JSON.parse(def.steps_json) } catch (_) {}
      }
      ci.steps = rawSteps.map(s => ({
        type: s.type || '',
        xpath: s.xpath || '',
        description: s.description || s.xpath || s.expected_text || '',
      }))
    } else {
      ci.steps = []
    }
  }
}

function saveTask() {
  if (!task.value) return
  client.post('/runner/tasks/save', buildTaskSavePayload(task.value)).catch((e) => {
    // 高频后台自动保存:失败仅记录到控制台,避免每条日志都弹 toast 打扰用户
    console.error('[saveTask] 保存失败:', e)
  })
}

const logPanel = ref(null)

function ts() { return new Date().toLocaleTimeString('zh-CN', { hour12: false }) }
function taskAddLog(msg, level = 'info') {
  if (!task.value) return
  if (!task.value.logs) task.value.logs = []
  task.value.logs.push({ time: ts(), text: msg, level })
  if (task.value.logs.length > 1000) task.value.logs = task.value.logs.slice(-500)
  nextTick(() => { if (logPanel.value) logPanel.value.scrollTop = logPanel.value.scrollHeight })
}

// ── Helpers ──
function taskProgress() {
  return calcTaskProgress(task.value || {})
}
function taskCompleted() {
  return taskCompletedCount(task.value || {})
}
function taskTotal() {
  return taskTotalCount(task.value || {})
}
function taskStatusInfo() {
  return getTaskStatusInfo(task.value || {})
}
function formatTime(isoStr) {
  if (!isoStr) return '—'
  try {
    const d = new Date(isoStr)
    const pad = n => String(n).padStart(2, '0')
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
  } catch (_) { return isoStr }
}

// ── APP性能统计 ──
const perfStats = computed(() => {
  return task.value?.perfStats || null
})

/** 获取某个 case 的性能明细 */
function getCasePerf(caseTitle) {
  if (!perfStats.value?.per_case) return null
  return perfStats.value.per_case.find(
    (c) => c.case_title === caseTitle
  ) || null
}

/** 格式化性能耗时 */
function fmtDuration(d) {
  if (d == null) return '—'
  return (Number(d) * 1000).toFixed(0) + 'ms'
}

// ── Case status helpers ──
function caseStatusLabel(ci) {
  if (!task.value) return { text: '等待中', color: '#f7cd67', bg: 'rgba(247,205,103,0.15)' }
  const isCurrent = task.value.running && (
    task.value.currentCaseTitle === ci.title ||
    (!task.value.currentCaseTitle && (task.value.caseItems || []).length === 1)
  )
  if (isCurrent)
    return { text: '◆ 执行中', color: '#889df0', bg: 'rgba(136,157,240,0.1)' }
  if (ci.status === 'done')
    return { text: '完成', color: '#89CFF0', bg: 'rgba(111,186,44,0.1)' }
  return { text: '等待中', color: '#f7cd67', bg: 'rgba(247,205,103,0.15)' }
}

// ── Step state for current case ──
function getStepState(ci, stepIndex) {
  const t = task.value; if (!t) return 'pending'
  // Running task with step states available → use live data
  if (t.running && (t.stepStates || []).length > 0) {
    const ss = t.stepStates.find(s => s.index === stepIndex)
    return ss?.result || 'pending'
  }
  // Finished case: show all steps as passed
  if (ci.status === 'done') return 'pass'
  return 'pending'
}

function stepStateClass(ci, si) {
  return 'step-' + getStepState(ci, si)
}

function stepStatusLabel(ci, si) {
  const s = getStepState(ci, si)
  if (s === 'running') return '◆ 执行中'
  if (s === 'pass') return '已通过'
  if (s === 'fail') return '失败'
  return '未执行'
}

// ── BUG entries ──
const bugEntries = computed(() => {
  const t = task.value; if (!t?.failedSteps?.length) return []
  const seen = new Set()
  const entries = []
  for (const f of t.failedSteps) {
    const key = `${f.caseTitle}||${f.iteration}||${f.stepIndex}`
    if (seen.has(key)) continue
    seen.add(key)
    // Find the case item to get full step list
    const ci = t.caseItems?.find(c => c.title === f.caseTitle)
    const allSteps = ci?.steps || []
    // Build step list with states: pass before fail step, fail at fail step, pending after
    const stepsWithState = allSteps.map((s, i) => ({
      ...s,
      state: i < f.stepIndex ? 'pass' : i === f.stepIndex ? 'fail' : 'pending',
    }))
    entries.push({
      key,
      caseTitle: f.caseTitle,
      iteration: f.iteration,
      failedStepIndex: f.stepIndex,
      failedStepType: f.stepType,
      failedStepDesc: f.description,
      failedResult: f.result,
      steps: stepsWithState,
      bugNum: entries.length + 1,
    })
  }
  return entries
})

function stepTypeLabel(type) {
  const map = {
    // UI
    click: '点击', long_click: '长按', swipe: '滑动',
    wait: '等待出现', wait_disappear: '等待消失',
    verify_text: '校验文字', poll_text: '轮询文本',
    start_app: '启动应用', kill_app: '关闭应用', sleep: '暂停',
    perf_element_time: '等待元素出现耗时',
    wait_toast: '等待Toast', if_element_appear: '如果出现', if_element_disappear: '如果消失',
    loop_n: '循环N次', loop_elements: '遍历元素',
    // API
    api_request: 'API 请求', api_assert: '断言验证',
    api_sleep: '暂停', api_log: '日志',
    // Web
    web_navigate: '页面跳转', web_click: '点击元素', web_fill: '填充输入',
    web_type: '逐字输入', web_wait: '等待', web_assert: '验证文本',
    web_screenshot: '截图', web_step: 'Web 步骤',
  }
  return map[type] || type
}

const isApiTask = computed(() => task.value?.taskType === 'api_testing')
const isWebTask = computed(() => task.value?.taskType === 'web_automation')

function failReason(failedResult) {
  const reasons = {
    'not found': '元素未找到：XPath 在当前页面匹配 0 个元素，可能页面发生变化或元素尚未加载',
    'timeout': '操作超时：在设定的超时时间内未完成操作',
    'fail': '步骤执行失败：预期条件未满足',
  }
  return reasons[failedResult] || `步骤执行失败：${failedResult}`
}

function getBugMeta(entry) {
  const t = task.value
  // Try to find a matching failedStep with timestamp info (we don't store timestamp in failedSteps yet)
  return {
    bugLabel: `BUG-${String(entry.bugNum).padStart(3, '0')}`,
    caseLabel: entry.caseTitle,
    iterLabel: `第 ${entry.iteration} 轮`,
    stepLabel: `步骤 ${entry.failedStepIndex + 1} · ${entry.failedStepType}`,
  }
}

// ── WS（进入详情页始终重绑 handler，修复列表页→详情页闭包陈旧） ──
function bindDetailTaskWS(runId) {
  if (!task.value) return
  const taskId = task.value.id
  connectTaskWebSocket(taskId, runId, (msg) => {
    if (!task.value) return
    if (msg.type === 'log') {
      taskAddLog(msg.message)
      saveTask()
      return
    }
    applyWsMessage(task.value, msg, {
      reconnectAware: true,
      addLog: (text, level) => taskAddLog(text, level),
      save: saveTask,
      onCaseStarted: (ci) => {
        if (ci) expandedCases.value = new Set([...expandedCases.value, ci.id])
      },
      onRunFinished: () => closeTaskWebSocket(taskId),
    })
  })
  const wm = getWsMap()
  const ws = wm[taskId]
  if (ws) {
    ws.onopen = () => {
      taskAddLog('🟢 日志已连接', 'success')
      if (task.value) task.value._wsJustReconnected = true
    }
    ws.onclose = () => { if (task.value?.running) taskAddLog('🔴 日志断开', 'warn') }
  }
}

function getWsMap() { return window[WS_KEY] || {} }

let saveTimer = null
watch(taskId, () => {
  loadTask().then(() => {
    if (!task.value) return
    const pendingRunId = history.state?.runId
    if (!task.value.runId && pendingRunId) {
      task.value.runId = pendingRunId
    }
    if (task.value?.running && task.value.runId) {
      bindDetailTaskWS(task.value.runId)
    }
  })
})

onMounted(() => {
  loadTask().then(async () => {
    if (!task.value) return
    // 创建任务后跳转详情时，history.state 可能带有 runId（早于 DB 关联）
    const pendingRunId = history.state?.runId
    if (!task.value.runId && pendingRunId) {
      task.value.runId = pendingRunId
    }
    if (task.value.running && task.value.runId) {
      bindDetailTaskWS(task.value.runId)
    } else if (task.value.running && !task.value.runId) {
      try {
        const { data } = await getActiveRuns()
        if (data.ok && data.active?.length) {
          const active = data.active.find(a => a.client_task_id === task.value.id)
          if (active) {
            task.value.runId = active.run_id
            bindDetailTaskWS(active.run_id)
            taskAddLog('🔄 已恢复实时连接')
          }
        }
      } catch (_) {}
    }
    saveTimer = setInterval(() => { if (task.value) saveTask() }, 3000)
    if (task.value && isTaskQueued(task.value)) {
      startDetailQueuePolling()
    }
  })
})

onUnmounted(() => {
  if (saveTimer) clearInterval(saveTimer)
  stopDetailQueuePolling()
  if (task.value?.id) closeTaskWebSocket(task.value.id)
})

// ── Actions ──
async function stopTask() {
  if (!task.value) return
  if (!task.value.runId) {
    try { await ElMessageBox.confirm('确定移除该排队任务？', '移除排队任务', { confirmButtonText: '移除', cancelButtonText: '取消', type: 'warning' }) } catch (_) { return }
    try {
      await client.post('/runner/queue/cancel', { client_task_id: task.value.id, device_serial: task.value.deviceSerial })
    } catch (e) {
      // 404 表示任务已开始执行,属正常;其余为真实失败,报错并留在当前页
      if (e?.response?.status !== 404) {
        ElMessage.error('取消排队失败，请检查网络后重试')
        return
      }
    }
    router.push('/runner')
    return
  }
  try { await ElMessageBox.confirm('确定停止该任务？', '停止任务', { confirmButtonText: '停止', cancelButtonText: '取消', type: 'warning' }) } catch (_) { return }
  try {
    await client.post(`/runner/run/${task.value.runId}/stop`)
    ElMessage.success('停止请求已发送')
  } catch (e) {
    ElMessage.error('停止请求失败，请检查网络连接')
  }
  task.value.running = false
  task.value.status = 'done'
  task.value.currentCaseTitle = ''
  task.value.currentIteration = 0
  task.value.outcome = 'stopped'
  closeTaskWebSocket(task.value.id)
  saveTask()
}

async function restartTask() {
  if (!task.value) return
  const prev = task.value
  const round = (prev.round || 0) + 1
  const tid = generateTaskId()
  const newTask = {
    id: tid,
    name: prev.name,
    round,
    mode: prev.mode,
    deviceSerial: prev.deviceSerial,
    caseIds: [...prev.caseIds],
    loopCount: prev.loopCount,
    intervalSeconds: prev.intervalSeconds || 5,
    running: false,
    runId: '',
    status: 'idle',
    caseItems: [],
    stepStates: [],
    logs: [],
    overallPass: 0,
    overallFail: 0,
    createdAt: new Date().toISOString(),
    creator: prev.creator || '',
    currentCaseTitle: '',
    currentIteration: 0,
    outcome: '',
  }
  try {
    await client.post('/runner/tasks/save', buildTaskSavePayload(newTask))
  } catch (_) {
    ElMessage.error('创建新任务失败')
    return
  }
  ElMessage.success(`已创建新任务「${newTask.name}」第${round}轮`)
  router.push(`/runner/task/${tid}`)
}

// ── Detail queue polling ──
const detailPollTimer = ref(null)

async function pollDetailQueuedTask() {
  if (!task.value || task.value.running) { stopDetailQueuePolling(); return }
  if (!isTaskQueued(task.value)) { stopDetailQueuePolling(); return }
  try {
    const { data } = await getActiveRuns()
    if (!data.ok || !data.active?.length) return
    for (const active of data.active) {
      if (active.client_task_id === task.value.id) {
        task.value.running = true
        task.value.status = 'running'
        task.value.runId = active.run_id
        bindDetailTaskWS(active.run_id)
        taskAddLog('🚀 排队任务已被后台调度，开始执行')
        stopDetailQueuePolling()
        return
      }
    }
  } catch (_) {}
}

function startDetailQueuePolling() {
  if (detailPollTimer.value) return
  detailPollTimer.value = setInterval(pollDetailQueuedTask, 3000)
}

function stopDetailQueuePolling() {
  if (detailPollTimer.value) { clearInterval(detailPollTimer.value); detailPollTimer.value = null }
}

async function removeTask() {
  if (!task.value) return
  try { await ElMessageBox.confirm(`删除任务「${task.value.name || task.value.id}」？`, '确认删除', { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }) } catch (_) { return }
  if (task.value.running) {
    try { await client.post(`/runner/run/${task.value.runId}/stop`) } catch (e) { console.error('[removeTask] stop failed:', e) }
    const wm = getWsMap(); if (wm[task.value.id]) closeTaskWebSocket(task.value.id)
  }
  try {
    await client.delete(`/runner/tasks/${taskId.value}`)
  } catch (e) {
    console.error('[removeTask] delete failed:', e)
    ElMessage.error('删除失败，请检查网络后重试')
    return
  }
  router.push('/runner')
}
</script>

<template>
  <div v-if="task" class="doc-page detail-page">
    <PageHeader
      title="任务详情 Task Detail"
      :subtitle="isApiTask ? `API 测试 · ${task.caseIds?.length || 0} 个用例 · ${task.loopCount} 轮` : isWebTask ? `Web 自动化 · ${task.caseIds?.length || 0} 个用例 · ${task.loopCount} 轮` : `设备 ${task.deviceSerial} · ${task.caseIds?.length || 0} 个用例 · ${task.loopCount} 轮`"
    />

    <div class="doc-body">
      <!-- ① 信息卡片 -->
      <section class="info-card">
        <div class="info-grid">
          <div class="info-item info-item--name full-width">
            <span class="info-label">🏷️ 任务名称</span>
            <span class="info-value task-name">{{ task.name || task.id }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">{{ isApiTask ? '🌐 端点' : isWebTask ? '🌍 目标' : '📱 设备' }}</span>
            <span class="info-value">{{ task.deviceSerial || (isApiTask ? 'API' : isWebTask ? 'Web' : '—') }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">📋 用例数</span>
            <span class="info-value">{{ task.caseIds?.length || 0 }} 个</span>
          </div>
          <div class="info-item">
            <span class="info-label">🔁 循环次数</span>
            <span class="info-value">{{ task.loopCount }} 轮</span>
          </div>
          <div class="info-item">
            <span class="info-label">⏱ 轮间间隔</span>
            <span class="info-value">{{ task.intervalSeconds || 5 }} 秒</span>
          </div>
          <div class="info-item">
            <span class="info-label">🕐 创建时间</span>
            <span class="info-value">{{ formatTime(task.createdAt) }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">👤 创建人</span>
            <span class="info-tag creator">{{ task.creator || '未知' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">📊 状态</span>
            <span class="info-tag status" :style="{ background: taskStatusInfo().color }">
              {{ taskStatusInfo().icon }} {{ taskStatusInfo().label }}
            </span>
          </div>
          <div v-if="task.running && task.currentCaseTitle" class="info-item full-width">
            <span class="info-label">▶ 当前执行</span>
            <span class="info-value current-case">{{ task.currentCaseTitle }} · 第 {{ task.currentIteration || 1 }} 轮</span>
          </div>
          <div v-if="task.caseItems?.length" class="info-item">
            <span class="info-label">🔄 总进度</span>
            <span class="info-value">{{ taskCompleted() }}/{{ taskTotal() }} 次</span>
          </div>
        </div>
        <el-progress
          v-if="task.caseItems?.length"
          :percentage="taskProgress()"
          :stroke-width="10"
          :show-text="true"
          :color="taskStatusInfo().color"
          class="info-progress"
        />
        <div class="info-actions">
          <el-button @click="router.push('/runner')">← 返回列表</el-button>
          <ConfirmButton v-if="task.running" type="primary" danger message="确定停止该任务？" title="停止任务" confirm-text="停止" @confirm="doStopTask">⏹ 停止</ConfirmButton>
          <el-button v-else-if="!task.caseItems?.length" type="primary" @click="restartTask">▶ 执行</el-button>
          <ConfirmButton v-else-if="isTaskQueued(task)" type="primary" message="确定移除该排队任务？" title="移除排队任务" confirm-text="移除" @confirm="doCancelQueue">⏸ 取消排队</ConfirmButton>
          <el-button v-else type="primary" @click="restartTask">↻ 重新执行</el-button>
          <el-button
            v-if="task.outcome && ['completed', 'stopped', 'interrupted', 'error'].includes(task.outcome)"
            @click="router.push(`/reports/task/${encodeURIComponent(task.id)}`)"
          >📊 查看报告</el-button>
          <ConfirmButton type="primary" danger plain :message="`删除任务「${task.name || task.id}」？`" title="确认删除" confirm-text="删除" @confirm="doRemoveTask">🗑 删除</ConfirmButton>
        </div>
      </section>

      <!-- ② 用例执行列表 -->
      <section v-if="task.caseItems?.length" class="section-block">
        <h3 class="sec-title">
          📋 用例执行列表
          <span class="sec-badge sec-badge--cases">{{ task.caseItems.length }}</span>
        </h3>
        <p class="sec-sub">点击用例展开查看步骤实时执行状态。当前执行中的用例自动展开。</p>

        <div v-for="ci in task.caseItems" :key="ci.id" class="case-card" :class="{ expanded: expandedCases.has(ci.id) }">
          <!-- 用例头部 -->
          <div class="case-header" @click="toggleCase(ci.id)">
            <span class="case-expand-icon">▶</span>
            <span class="case-id-badge" :style="{
              background: task.running && task.currentCaseTitle === ci.title ? '#889df0' : 'var(--app-green-deep)'
            }">{{ ci.id }}</span>
            <div class="case-title-area">
              <span class="case-title-text">{{ ci.title }}</span>
            </div>
            <span class="case-status-text" :style="{ color: caseStatusLabel(ci).color, background: caseStatusLabel(ci).bg }">
              {{ caseStatusLabel(ci).text }}
            </span>
            <div class="case-stats">
              <span class="stat-total">🔁 {{ ci.total }}</span>
              <span class="stat-pass">✅ {{ ci.pass }}</span>
              <span class="stat-fail">❌ {{ ci.fail }}</span>
            </div>
          </div>

          <!-- 展开：步骤卡片 -->
          <div v-if="expandedCases.has(ci.id)" class="case-body">
            <!-- 轮次横幅 -->
            <div v-if="task.running && (task.currentCaseTitle === ci.title || (!task.currentCaseTitle && (task.caseItems||[]).length===1))" class="iteration-banner">
              <span class="iter-badge">第 {{ task.currentIteration || 1 }} 轮</span>
              <span>正在执行 — {{ (task.stepStates || []).filter(s => s.result === 'pass').length }}/{{ ci.steps?.length || 0 }} 步完成</span>
            </div>

            <!-- 步骤卡片 -->
            <div class="step-list">
              <div
                v-for="(step, si) in (ci.steps || [])" :key="si"
                class="step-card" :class="stepStateClass(ci, si)"
              >
                <div class="step-strip"></div>
                <div class="step-body">
                  <div class="step-header-row">
                    <span class="step-index">步骤 {{ si + 1 }}</span>
                    <span class="step-type-tag">{{ stepTypeLabel(step.type) || step.type }}</span>
                    <span class="step-status-tag">{{ stepStatusLabel(ci, si) }}</span>
                  </div>
                  <div class="step-desc">{{ step.description }}</div>
                  <div v-if="step.xpath" class="step-xpath">{{ step.xpath }}</div>
                </div>
              </div>
            </div>
            <div v-if="!ci.steps?.length" class="step-empty">暂无可展示的步骤</div>

            <!-- APP性能数据 -->
            <div v-if="getCasePerf(ci.title)" class="perf-case-section">
              <div class="perf-case-title">⏱️ 性能测量 — 等待元素出现耗时</div>
              <div class="perf-case-grid">
                <span class="perf-case-stat"><b>次数</b> {{ getCasePerf(ci.title).count }}</span>
                <span class="perf-case-stat"><b>平均</b> {{ fmtDuration(getCasePerf(ci.title).avg) }}</span>
                <span class="perf-case-stat"><b>最快</b> {{ fmtDuration(getCasePerf(ci.title).min) }}</span>
                <span class="perf-case-stat"><b>最慢</b> {{ fmtDuration(getCasePerf(ci.title).max) }}</span>
                <span class="perf-case-stat"><b>中位</b> {{ fmtDuration(getCasePerf(ci.title).median) }}</span>
              </div>
              <div class="perf-items">
                <div
                  v-for="(pr, pri) in getCasePerf(ci.title).items"
                  :key="pri"
                  class="perf-item"
                >
                  <span class="perf-iter">第{{ pr.iteration }}轮</span>
                  <span class="perf-desc">{{ pr.description }}</span>
                  <span class="perf-dur">{{ fmtDuration(pr.duration) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- ③ BUG 单记录 -->
      <section v-if="bugEntries.length" class="section-block">
        <h3 class="sec-title">
          🐛 执行失败记录（BUG 单）
          <span class="sec-badge" style="background:#e85f5f;">{{ bugEntries.length }}</span>
        </h3>
        <p class="sec-sub">以下用例在循环执行中步骤失败。展开查看完整步骤列表与失败原因。</p>

        <div
          v-for="entry in bugEntries" :key="entry.key"
          class="case-card bug-card" :class="{ expanded: expandedBugs.has(entry.key) }"
        >
          <div class="case-header" @click="toggleBug(entry.key)">
            <span class="case-expand-icon">▶</span>
            <span class="case-id-badge" style="background:#e85f5f;">BUG-{{ String(entry.bugNum).padStart(3, '0') }}</span>
            <div class="case-title-area">
              <span class="case-title-text">{{ entry.caseTitle }}</span>
              <div class="bug-header-sub">第 {{ entry.iteration }} 轮 · 步骤 {{ entry.failedStepIndex + 1 }} 失败</div>
            </div>
            <span class="case-status-text" style="color:#e85f5f;background:rgba(232,95,95,0.12);">🔴 执行失败</span>
          </div>

          <div v-if="expandedBugs.has(entry.key)" class="case-body">
            <!-- BUG 元信息 -->
            <div class="bug-meta">
              <span><span class="bug-meta-label">🐛 BUG 编号</span> <span class="bug-meta-value">{{ getBugMeta(entry).bugLabel }}</span></span>
              <span><span class="bug-meta-label">📋 关联用例</span> <span style="font-weight:700;">{{ entry.caseTitle }}</span></span>
              <span><span class="bug-meta-label">🔁 失败轮次</span> <span class="bug-meta-value">{{ getBugMeta(entry).iterLabel }}</span></span>
              <span><span class="bug-meta-label">❌ 失败步骤</span> <span class="bug-meta-value">{{ getBugMeta(entry).stepLabel }}</span></span>
            </div>

            <!-- 完整步骤列表 -->
            <div class="step-list">
              <div
                v-for="(step, si) in entry.steps" :key="si"
                class="step-card" :class="'step-' + step.state"
              >
                <div class="step-strip"></div>
                <div class="step-body">
                  <div class="step-header-row">
                    <span class="step-index">步骤 {{ si + 1 }}</span>
                    <span class="step-type-tag">{{ stepTypeLabel(step.type) || step.type }}</span>
                    <span class="step-status-tag">
                      {{ step.state === 'pass' ? '✅ 通过' : step.state === 'fail' ? '❌ 失败' : '未执行' }}
                    </span>
                  </div>
                  <div class="step-desc">{{ step.description }}</div>
                  <div v-if="step.xpath" class="step-xpath">{{ step.xpath }}</div>
                  <div v-if="step.state === 'fail'" class="step-fail-reason">
                    <strong>🔍 失败原因：</strong>{{ failReason(entry.failedResult) }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- ④ 执行日志 -->
      <section class="log-section">
        <div class="doc-section__header">
          <h3 class="doc-section__title log-title">执行日志 <span class="doc-tag">Logs</span></h3>
          <el-button size="small" type="text" @click="task.logs = []" style="color:#999;">清空</el-button>
        </div>
        <div class="doc-section__label log-sub">实时 WebSocket 日志输出 ({{ task.logs?.length || 0 }} 条)</div>
        <div ref="logPanel" class="log-card-body">
          <div v-for="(l, i) in (task.logs || [])" :key="i" class="log-line" :class="'log-' + l.level">
            <span class="log-time">{{ l.time }}</span><span>{{ l.text }}</span>
          </div>
          <div v-if="!task.logs?.length" class="log-empty">日志将在此显示</div>
        </div>
      </section>
    </div>
  </div>
  <div v-else class="not-found">
    <p>任务未找到</p>
    <el-button @click="router.push('/runner')">← 返回任务列表</el-button>
  </div>
</template>

<style scoped>
.detail-page {
  display: flex; flex-direction: column; min-height: 100%; overflow: hidden;
}
.detail-page :deep(.doc-body) {
  flex: 1; min-height: 0; display: flex; flex-direction: column; gap: 18px;
  overflow-y: auto; padding-bottom: 40px;
}

/* ── Info card ── */
.info-card {
  background: var(--app-glass-card);
  border-radius: 14px; border: 1px solid var(--app-glass-border);
  padding: 20px 24px; display: flex; flex-direction: column; gap: 14px;
  box-shadow: var(--app-shadow-sm);
  backdrop-filter: blur(var(--app-glass-blur));
  -webkit-backdrop-filter: blur(var(--app-glass-blur));
}
.info-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px 20px; }
.info-item { display: flex; align-items: center; gap: 8px; font-size: 13px; }
.info-item.full-width { grid-column: 1 / -1; }
.info-item--name { padding-bottom: 4px; border-bottom: 1px dashed rgba(162,210,255,0.24); margin-bottom: 2px; }
.info-value.task-name { font-size: 15px; line-height: 1.4; word-break: break-word; }
.info-label { color: var(--app-text-secondary); font-weight: 500; white-space: nowrap; }
.info-value { color: var(--app-text); font-weight: 600; }
.info-value.current-case { color: #409eff; }
.info-tag { font-size: 11px; font-weight: 700; color: #fff; padding: 2px 10px; border-radius: 12px; white-space: nowrap; }
.info-tag.creator { background: #b39ef3; }
.info-progress { margin-top: 2px; }
.info-actions { display: flex; gap: 8px; padding-top: 4px; border-top: 1px solid rgba(162,210,255,0.18); }

/* ── Section titles ── */
.section-block { margin-top: 4px; }
.sec-title {
  font-weight: 800; font-size: 16px; color: var(--app-text);
  display: flex; align-items: center; gap: 8px; margin-bottom: 2px;
}
.sec-badge {
  font-size: 11px; font-weight: 800; color: #fff;
  padding: 2px 10px; border-radius: 50px;
}
.sec-badge--cases { background: var(--app-green-deep); }
.sec-sub { font-size: 12px; color: var(--app-text-secondary); margin-bottom: 14px; }

/* ── Case card ── */
.case-card {
  background: rgba(255,255,255,0.48); border: 1px solid var(--app-glass-border);
  border-radius: 18px; margin-bottom: 14px; overflow: hidden;
  transition: all 0.25s cubic-bezier(0.4,0,0.2,1);
  box-shadow: var(--app-shadow-sm);
}
.case-card:hover { transform: translateY(-1px); box-shadow: var(--app-shadow-md); }
.case-card.expanded { border-color: rgba(162,210,255,0.62); }
.case-card.bug-card { border-left: 4px solid #e85f5f; }

.case-header {
  display: flex; align-items: center; gap: 12px;
  padding: 16px 22px; cursor: pointer; user-select: none;
  transition: background 0.15s;
}
.case-header:hover { background: rgba(162,210,255,0.12); }
.case-expand-icon {
  font-size: 11px; color: var(--app-text-secondary); width: 16px; flex-shrink: 0;
  transition: transform 0.25s cubic-bezier(0.4,0,0.2,1);
}
.case-card.expanded .case-expand-icon { transform: rotate(90deg); }

.case-id-badge {
  font-size: 11px; font-weight: 700; color: #fff;
  padding: 3px 10px; border-radius: 50px; flex-shrink: 0;
}
.case-title-area { flex: 1; min-width: 0; }
.case-title-text {
  font-size: 15px; font-weight: 700; color: var(--app-text);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.bug-header-sub { font-size: 11px; color: var(--app-text-secondary); margin-top: 2px; }
.case-status-text { font-size: 11px; font-weight: 600; padding: 2px 10px; border-radius: 50px; flex-shrink: 0; }
.case-stats { display: flex; gap: 16px; font-size: 12px; font-weight: 600; color: var(--app-text-secondary); flex-shrink: 0; }
.case-stats span { white-space: nowrap; }
.stat-total { color: var(--app-text-secondary); }
.stat-pass { color: #89CFF0; }
.stat-fail { color: #e85f5f; }

/* ── Case body ── */
.case-body { padding-bottom: 2px; }

/* ── Iteration banner ── */
.iteration-banner {
  display: flex; align-items: center; gap: 8px;
  margin: 0 22px 14px 38px;
  padding: 8px 14px;
  background: rgba(136,157,240,0.06); border-radius: 10px;
  border: 1px dashed rgba(136,157,240,0.25);
  font-size: 12px; font-weight: 700; color: #889df0;
}
.iter-badge {
  font-size: 11px; font-weight: 800; color: #fff;
  background: #889df0; padding: 2px 10px; border-radius: 50px;
}

/* ── BUG meta ── */
.bug-meta {
  display: flex; gap: 20px; flex-wrap: wrap;
  margin: 0 22px 12px; padding: 10px 14px;
  background: rgba(232,95,95,0.04); border-radius: 10px;
  border: 1px dashed rgba(232,95,95,0.2);
  font-size: 12px; font-weight: 600; color: var(--app-text-secondary);
}
.bug-meta-label { color: var(--app-text-secondary); }
.bug-meta-value { color: #e85f5f; font-weight: 700; }

/* ── Step list ── */
.step-list { padding: 0 22px 18px 38px; display: flex; flex-direction: column; gap: 8px; }
.step-empty { padding: 24px 22px 18px 38px; color: var(--app-text-secondary); font-size: 13px; text-align: center; }

.step-card {
  display: flex; align-items: stretch; border-radius: 12px;
  overflow: hidden; transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
  box-shadow: var(--app-shadow-sm);
  border: 1px solid var(--app-glass-border);
}
.step-strip { width: 5px; flex-shrink: 0; border-radius: 5px 0 0 5px; }
.step-body { flex: 1; padding: 12px 16px; background: rgba(255,255,255,0.52); display: flex; flex-direction: column; gap: 4px; }
.step-header-row { display: flex; align-items: center; gap: 8px; }
.step-index { font-size: 12px; font-weight: 800; color: var(--app-text-secondary); font-family: 'Cascadia Code', Consolas, monospace; }
.step-type-tag {
  font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 8px;
  background: rgba(162,210,255,0.14); color: var(--app-text-secondary); text-transform: uppercase;
}
.step-status-tag { font-size: 11px; font-weight: 700; padding: 2px 12px; border-radius: 50px; margin-left: auto; }
.step-desc { font-size: 13px; font-weight: 600; color: var(--app-text); line-height: 1.4; }
.step-xpath { font-size: 11px; color: var(--app-text-secondary); font-family: 'Cascadia Code', Consolas, monospace; margin-top: 2px; }
.step-fail-reason {
  font-size: 12px; font-weight: 600; color: #e85f5f;
  background: rgba(232,95,95,0.05); padding: 8px 12px; border-radius: 8px;
  margin-top: 4px; border-left: 3px solid #e85f5f; line-height: 1.5;
}

/* ── Step states ── */
.step-pending .step-strip { background: var(--app-text-muted); }
.step-pending .step-body { background: rgba(255,255,255,0.34); }
.step-pending .step-index, .step-pending .step-desc, .step-pending .step-xpath { color: var(--app-text-muted); }
.step-pending .step-status-tag { background: rgba(162,210,255,0.12); color: var(--app-text-secondary); }
.step-pending .step-type-tag { background: rgba(162,210,255,0.08); color: var(--app-text-muted); }

.step-running { animation: stepPulse 1.8s cubic-bezier(0.4,0,0.2,1) infinite; }
.step-running .step-strip { background: #889df0; }
.step-running .step-body { background: rgba(136,157,240,0.04); }
.step-running .step-status-tag { background: #889df0; color: #fff; }
@keyframes stepPulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(136,157,240,0.25); }
  50% { box-shadow: 0 0 0 6px rgba(136,157,240,0.06); }
}

.step-pass .step-strip { background: #89CFF0; }
.step-pass .step-body { background: rgba(111,186,44,0.03); }
.step-pass .step-status-tag { background: rgba(111,186,44,0.15); color: #529b2a; }

.step-fail .step-strip { background: #e85f5f; }
.step-fail .step-body { background: rgba(232,95,95,0.03); }
.step-fail .step-status-tag { background: rgba(232,95,95,0.15); color: #d9534f; }

/* ── Log section ── */
.log-section {
  display: flex; flex-direction: column; flex-shrink: 0;
  padding: 18px 24px; background: #1e1e24; border: 1px solid #33333a;
  border-radius: 12px; overflow: hidden;
  min-height: 420px;
}
.log-title { color: #e6eef7; }
.log-sub { color: #8f8a7d; flex-shrink: 0; }
.log-card-body {
  flex: 1; min-height: 300px; overflow-y: auto; margin-top: 10px;
  padding: 12px 16px; border-radius: 10px; background: #16161c;
  font-family: 'Cascadia Code', Consolas, monospace;
  font-size: 13px; line-height: 1.7;
}
.log-line { padding: 2px 4px; border-bottom: 1px solid rgba(255,255,255,.04); white-space: pre-wrap; color: #c5c5c5; }
.log-time { color: #666; margin-right: 8px; font-size: 11px; }
.log-info { color: #bbb; }
.log-success { color: #67c23a; }
.log-error { color: #f56c6c; }
.log-warn { color: #e6a23c; }
.log-empty { text-align: center; color: #666; padding: 40px; font-size: 13px; }

.not-found { text-align: center; color: var(--app-text-secondary); padding: 80px 0; font-size: 15px; }
.not-found p { margin-bottom: 16px; }

/* ── 性能测量 ── */
.perf-case-section {
  margin-top: 14px;
  padding: 12px 14px;
  background: rgba(247,205,103,0.08);
  border: 1px solid rgba(247,205,103,0.25);
  border-radius: 12px;
}
.perf-case-title {
  font-size: 13px;
  font-weight: 700;
  color: #b8860b;
  margin-bottom: 10px;
}
.perf-case-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 16px;
  margin-bottom: 10px;
}
.perf-case-stat {
  font-size: 12px;
  color: var(--app-text-secondary);
}
.perf-case-stat b {
  color: var(--app-text);
  font-weight: 600;
}
.perf-items {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.perf-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 5px 10px;
  background: rgba(255,255,255,0.6);
  border-radius: 8px;
  font-size: 12px;
}
.perf-iter {
  font-weight: 600;
  color: var(--app-text-secondary);
  min-width: 40px;
}
.perf-desc {
  flex: 1;
  color: var(--app-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.perf-dur {
  font-weight: 700;
  color: #889df0;
  font-family: "Cascadia Code", Consolas, monospace;
  white-space: nowrap;
}

@media (max-width: 768px) {
  .info-grid { grid-template-columns: 1fr 1fr; }
  .case-header { flex-wrap: wrap; }
  .case-stats { flex-wrap: wrap; gap: 8px; }
  .bug-meta { flex-direction: column; gap: 4px; }
}
</style>
