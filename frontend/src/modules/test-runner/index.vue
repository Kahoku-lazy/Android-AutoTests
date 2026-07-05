<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import client from '@/shared/api-client.js'
import { wsUrl } from '@/shared/ws-url.js'
import { Button as AnimalButton, Card, Tabs, Modal } from 'animal-island-vue'
import PageHeader from '@/shared/components/PageHeader.vue'

const router = useRouter()

const cases = ref([])
const devices = ref([])
const showNewTask = ref(false)
const activeTab = ref('all')

const STORAGE_KEY = '_runner_tasks'
const WS_MAP_KEY = '_task_ws_map'
const COUNTER_KEY = '_task_id_counter'
const tasks = ref([])

// ── Sequential ID generator: ID-001, ID-002, ... ──
function _readCounter() {
  try { return parseInt(localStorage.getItem(COUNTER_KEY)) || 0 } catch (_) { return 0 }
}
function _writeCounter(n) {
  localStorage.setItem(COUNTER_KEY, String(n))
}
function _nextSeq() {
  const n = _readCounter() + 1
  _writeCounter(n)
  return n
}
function generateTaskId() {
  return `ID-${String(_nextSeq()).padStart(3, '0')}`
}

// ── JWT decode for creator ──
function getCurrentUsername() {
  try {
    const token = localStorage.getItem('access_token')
    if (!token) return '未知'
    const payload = JSON.parse(atob(token.split('.')[1]))
    return payload.username || payload.sub || '未知'
  } catch (_) { return '未知' }
}

// ── Gradient palette for cards ──
const CARD_GRADIENTS = [
  'linear-gradient(135deg, #fef9ef 0%, #fdf0d5 100%)',
  'linear-gradient(135deg, #eef6fb 0%, #dceef7 100%)',
  'linear-gradient(135deg, #f3edf9 0%, #e8dcf5 100%)',
  'linear-gradient(135deg, #edf7ef 0%, #d6eddb 100%)',
  'linear-gradient(135deg, #fef5f0 0%, #fde8d8 100%)',
]
function cardGradient(idx) { return CARD_GRADIENTS[idx % CARD_GRADIENTS.length] }

// ── localStorage ──
function getWsMap() { return window[WS_MAP_KEY] || {} }
function setWsMap(m) { window[WS_MAP_KEY] = m }

function saveTasks() {
  const data = tasks.value.map(t => ({
    id: t.id, name: t.name, mode: t.mode, deviceSerial: t.deviceSerial, caseIds: t.caseIds,
    loopCount: t.loopCount, running: t.running, runId: t.runId,
    caseItems: t.caseItems, stepStates: t.stepStates,
    overallPass: t.overallPass, overallFail: t.overallFail, logs: (t.logs || []).slice(-100),
    createdAt: t.createdAt, creator: t.creator,
    currentCaseTitle: t.currentCaseTitle, currentIteration: t.currentIteration,
    failedSteps: (t.failedSteps || []).slice(-200),
    conclusion: t.conclusion || '', bugTicket: t.bugTicket || '',
  }))
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
}
function restoreTasks() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) {
      tasks.value = JSON.parse(raw).map(d => ({
        ...d,
        createdAt: d.createdAt || '',
        creator: d.creator || '',
        currentCaseTitle: d.currentCaseTitle || '',
        currentIteration: d.currentIteration || 0,
        failedSteps: d.failedSteps || [],
        conclusion: d.conclusion || '', bugTicket: d.bugTicket || '',
      }))
      // Sync counter: find max ID-NNN → ensure counter ≥ that
      let maxSeq = 0
      for (const t of tasks.value) {
        const m = String(t.id).match(/^ID-(\d+)$/)
        if (m) maxSeq = Math.max(maxSeq, parseInt(m[1]))
      }
      if (maxSeq >= _readCounter()) _writeCounter(maxSeq)
    }
  } catch (_) {}
}
watch(tasks, () => saveTasks(), { deep: true })

// ── Filter ──
const runningTasks = computed(() => tasks.value.filter(t => t.running))
const waitingTasks = computed(() => tasks.value.filter(t => !t.running && t.caseItems?.length && t.caseItems[0]?.status === 'pending'))
const doneTasks = computed(() => tasks.value.filter(t => !t.running && t.caseItems?.length && t.caseItems[0]?.status !== 'pending'))
const idleTasks = computed(() => tasks.value.filter(t => !t.running && !t.caseItems?.length))

const filterTabs = computed(() => [
  { key: 'all', label: `📋 全部 (${tasks.value.length})` },
  { key: 'running', label: `⚡ 执行中 (${runningTasks.value.length})` },
  { key: 'waiting', label: `⏳ 等待中 (${waitingTasks.value.length})` },
  { key: 'done', label: `✅ 已完成 (${doneTasks.value.length})` },
  { key: 'idle', label: `📝 未执行 (${idleTasks.value.length})` },
])

function tasksForTab(key) {
  if (key === 'all') return tasks.value
  if (key === 'running') return runningTasks.value
  if (key === 'waiting') return waitingTasks.value
  if (key === 'done') return doneTasks.value
  return idleTasks.value
}

function taskBucket(task) {
  if (task.running) return 'running'
  if (!task.caseItems?.length) return 'idle'
  if (task.caseItems[0]?.status === 'pending') return 'waiting'
  return 'done'
}

// ── Helpers ──
function ts() { return new Date().toLocaleTimeString('zh-CN', { hour12: false }) }
function taskAddLog(task, msg, level = 'info') {
  if (!task.logs) task.logs = []
  task.logs.push({ time: ts(), text: msg, level })
  if (task.logs.length > 500) task.logs = task.logs.slice(-300)
}
function deviceLabel(d) { const p = []; if (d.brand) p.push(d.brand); if (d.model) p.push(d.model); p.push(`[${d.serial}]`); return p.join(' ') }
function findDevice(serial) { return devices.value.find(d => d.serial === serial) || { serial, model: serial } }

function taskProgress(task) {
  const ci = task.caseItems; if (!ci?.length) return 0
  const t = ci.reduce((s, c) => s + c.total, 0), d = ci.reduce((s, c) => s + c.pass + c.fail, 0)
  return t ? Math.round(d / t * 100) : 0
}

function taskCompletedCount(task) {
  const ci = task.caseItems; if (!ci?.length) return 0
  return ci.reduce((s, c) => s + c.pass + c.fail, 0)
}

function taskTotalCount(task) {
  const ci = task.caseItems; if (!ci?.length) return 0
  return ci.reduce((s, c) => s + c.total, 0)
}

function taskStatusInfo(task) {
  if (task.running) return { label: '执行中', color: '#889df0', icon: '⚡' }
  if (!task.caseItems?.length) return { label: '未执行', color: '#8b7355', icon: '📝' }
  if (task.caseItems[0]?.status === 'pending') return { label: '等待中', color: '#f7cd67', icon: '⏳' }
  return { label: '已完成', color: '#6fba2c', icon: '✅' }
}

function formatTime(isoStr) {
  if (!isoStr) return ''
  try {
    const d = new Date(isoStr)
    const pad = n => String(n).padStart(2, '0')
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
  } catch (_) { return isoStr }
}

// ── Navigate to detail page ──
function openTaskDetail(task) {
  router.push(`/runner/task/${task.id}`)
}

// ── New task form ──
const newForm = ref({ name: '', deviceSerial: '', caseIds: [], loopCount: 3, mode: 'now', startAt: '', endAt: '' })
function resetNewForm() { newForm.value = { name: '', deviceSerial: devices.value[0]?.serial || '', caseIds: [], loopCount: 3, mode: 'now', startAt: '', endAt: '' } }

async function openNewTask() {
  resetNewForm()
  await Promise.all([loadDevices(), loadCases()])
  if (!devices.value.length) ElMessage.warning('暂无在线设备，请先在设备管理中连接设备')
  if (!cases.value.length) ElMessage.warning('暂无可用用例，请先在测试用例中创建用例')
  showNewTask.value = true
}

function normalizeCaseIds(ids) {
  return (ids || []).map(id => String(id))
}

async function createAndStart() {
  if (!newForm.value.deviceSerial) { ElMessage.warning('请选择执行设备'); return }
  if (!newForm.value.caseIds.length) { ElMessage.warning('请至少选择一个测试用例'); return }
  const tid = generateTaskId()
  const task = {
    id: tid, name: newForm.value.name || `任务${tid}`, mode: newForm.value.mode,
    startAt: newForm.value.startAt, endAt: newForm.value.endAt,
    deviceSerial: newForm.value.deviceSerial, caseIds: normalizeCaseIds(newForm.value.caseIds),
    loopCount: newForm.value.loopCount, running: false, runId: '',
    caseItems: [], stepStates: [], logs: [], overallPass: 0, overallFail: 0,
    createdAt: new Date().toISOString(), creator: getCurrentUsername(),
    currentCaseTitle: '', currentIteration: 0,
  }
  tasks.value.push(task)
  resetNewForm()
  showNewTask.value = false
  activeTab.value = taskBucket(task)
  ElMessage.success(`任务「${task.name}」已创建`)
  await doStartTask(task)
}

function initTaskProgress(task) {
  const idSet = new Set(normalizeCaseIds(task.caseIds))
  task.caseItems = cases.value
    .filter(c => idSet.has(String(c.id)))
    .map((c, i) => ({
      id: c.id, title: c.title, index: i + 1, status: 'pending',
      pass: 0, fail: 0, total: task.loopCount, rate: 0,
    }))
  task.overallPass = 0
  task.overallFail = 0
  task.stepStates = []
}

async function doStartTask(task) {
  if (!cases.value.length) await loadCases()
  initTaskProgress(task)
  if (!task.caseItems.length) {
    taskAddLog(task, '❌ 未匹配到用例，请确认用例列表已加载且用例ID有效', 'error')
    ElMessage.warning('用例数据未加载或ID不匹配，请刷新页面后重试')
    return
  }
  const body = { case_ids: task.caseIds, loop_count: task.loopCount, device_serial: task.deviceSerial, client_task_id: task.id }
  if (task.mode === 'scheduled') { if (task.startAt) body.start_at = new Date(task.startAt).toISOString(); if (task.endAt) body.end_at = new Date(task.endAt).toISOString() }
  try {
    const { data } = await client.post('/runner/run', body)
    if (data.ok && data.runs?.[0]?.run_id) {
      task.running = true
      task.runId = data.runs[0].run_id
      connectTaskWS(task, task.runId)
      taskAddLog(task, '🚀 任务已启动')
    } else if (data.ok && data.queued?.length) {
      // Device busy — task queued
      task.running = false
      taskAddLog(task, `⏳ 设备正忙，任务已加入队列等待执行`)
      ElMessage.info('设备正忙，任务已加入队列，设备空闲后自动执行')
      startQueuePolling()
    } else if (data.ok) {
      task.running = false
      taskAddLog(task, '❌ 设备不可用，任务未启动', 'error')
      ElMessage.warning('设备不可用或未就绪，任务已保存，可在列表中重试')
    } else {
      task.running = false
      taskAddLog(task, `❌ ${data.error}`, 'error')
      ElMessage.error(data.error || '启动失败')
    }
  } catch (e) {
    task.running = false
    taskAddLog(task, `❌ ${e.message}`, 'error')
    ElMessage.error('启动失败，任务已保存到列表')
  }
}

async function stopTask(task) {
  if (!task.runId) {
    // Queued task without a run — just remove it
    try { await ElMessageBox.confirm('确定移除该排队任务？', '移除排队任务', { confirmButtonText: '移除', cancelButtonText: '取消', type: 'warning' }) } catch (_) { return }
    tasks.value = tasks.value.filter(x => x.id !== task.id)
    ElMessage.success('已移除排队任务')
    return
  }
  try { await ElMessageBox.confirm('确定停止该任务？', '停止任务', { confirmButtonText: '停止', cancelButtonText: '取消', type: 'warning' }) } catch (_) { return }
  try { await client.post(`/runner/run/${task.runId}/stop`) } catch (_) {}
  task.running = false; task.currentCaseTitle = ''; task.currentIteration = 0
  const wm = getWsMap(); if (wm[task.id]) { try { wm[task.id].close() } catch (_) {}; delete wm[task.id]; setWsMap(wm) }
}

async function removeTask(task) {
  try { await ElMessageBox.confirm(`删除任务「${task.name || task.id}」？`, '确认删除', { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }) } catch (_) { return }
  if (task.running) {
    if (task.runId) { try { await client.post(`/runner/run/${task.runId}/stop`) } catch (_) {} }
    const wm = getWsMap(); if (wm[task.id]) { try { wm[task.id].close() } catch (_) {}; delete wm[task.id]; setWsMap(wm) }
  }
  tasks.value = tasks.value.filter(x => x.id !== task.id)
  ElMessage.success('已删除')
}

function restartTask(task) {
  task.caseItems = []; task.stepStates = []; task.overallPass = 0; task.overallFail = 0
  task.logs = []; task.currentCaseTitle = ''; task.currentIteration = 0
  doStartTask(task)
}

// ── WebSocket ──
function connectTaskWS(task, runId) {
  const wm = getWsMap(); if (wm[task.id]) { try { wm[task.id].close() } catch (_) {} }
  const url = `${wsUrl('/ws/test-run/' + runId)}?token=${encodeURIComponent(localStorage.getItem('access_token') || '')}`
  const ws = new WebSocket(url); wm[task.id] = ws; setWsMap(wm)
  ws.onmessage = (e) => {
    try {
      const msg = JSON.parse(e.data)
      const ci = task.caseItems?.find(c => c.id === msg.case_id)
      switch (msg.type) {
        case 'log': taskAddLog(task, msg.message); break
        case 'case_started':
          if (ci) { ci.status = 'running'; ci.pass = 0; ci.fail = 0 }
          task.stepStates = []
          task.currentCaseTitle = ci?.title || msg.case_id || ''
          task.currentIteration = 1
          break
        case 'step_result':
          task.stepStates = [...(task.stepStates || []).filter(s => s.index !== msg.step_index), { index: msg.step_index, total: msg.total_steps, type: msg.step_type, desc: msg.description, result: msg.result }].sort((a, b) => a.index - b.index)
          // Track failed steps for report
          if (msg.result !== 'pass' && msg.result !== 'stopped') {
            if (!task.failedSteps) task.failedSteps = []
            const dup = task.failedSteps.find(
              f => f.caseTitle === ci?.title && f.iteration === (task.currentIteration || 1) && f.stepIndex === msg.step_index
            )
            if (!dup) {
              task.failedSteps.push({
                caseTitle: ci?.title || msg.case_id || '',
                iteration: task.currentIteration || 1,
                stepIndex: msg.step_index,
                stepType: msg.step_type,
                description: msg.description || '',
                result: msg.result,
              })
            }
          }
          break
        case 'iteration_result':
          if (msg.result === 'pass') { if (ci) ci.pass++; task.overallPass = (task.overallPass || 0) + 1 }
          else { if (ci) ci.fail++; task.overallFail = (task.overallFail || 0) + 1 }
          if (ci) ci.rate = ci.total ? Math.round((ci.pass + ci.fail) / ci.total * 100) : 0
          task.currentIteration = (ci ? ci.pass + ci.fail : task.currentIteration || 0) + 1
          break
        case 'case_finished':
          if (ci) { ci.status = 'done'; ci.pass = parseInt(msg.pass); ci.fail = parseInt(msg.fail); ci.rate = 100 }
          break
        case 'run_finished':
          task.running = false; delete wm[task.id]; setWsMap(wm)
          task.caseItems?.forEach(c => { if (c.status !== 'done') c.status = 'done' })
          task.currentCaseTitle = ''; task.currentIteration = 0
          // Auto-generate conclusion if not manually set
          if (!task.conclusion) {
            const pf = task.overallFail || 0
            task.conclusion = pf === 0 ? '✅ 测试通过：所有用例全部执行成功' : `❌ 测试不通过：${pf} 个用例执行失败`
          }
          taskAddLog(task, `🏁 完成 ✅${task.overallPass || 0} ❌${task.overallFail || 0}`, 'success')
          // Immediately check if any queued tasks have been picked up by the backend
          pollQueuedTasks()
          break
        case 'device_error':
          task.running = false; taskAddLog(task, `💥 ${msg.error}`, 'error')
          // Device error frees up the device, check queue
          pollQueuedTasks()
          break
      }
    } catch (_) {}
  }
}

// ── Queue polling: detect when a queued task gets picked up by the backend ──
const queuePollTimer = ref(null)
const POLL_INTERVAL = 3000  // 3 seconds

function hasQueuedTasks() {
  return tasks.value.some(t => !t.running && t.caseItems?.length && t.caseItems[0]?.status === 'pending')
}

async function pollQueuedTasks() {
  if (!hasQueuedTasks()) { stopQueuePolling(); return }
  try {
    const { data } = await client.get('/runner/active')
    if (!data.ok || !data.active?.length) return
    for (const active of data.active) {
      if (!active.client_task_id) continue
      const task = tasks.value.find(t => t.id === active.client_task_id)
      if (task && !task.running) {
        // Our queued task is now running! Connect WS and update state
        task.running = true
        task.runId = active.run_id
        connectTaskWS(task, active.run_id)
        taskAddLog(task, '🚀 排队任务已被后台调度，开始执行')
      }
    }
  } catch (_) { /* polling is best-effort */ }
}

function startQueuePolling() {
  if (queuePollTimer.value) return
  queuePollTimer.value = setInterval(pollQueuedTasks, POLL_INTERVAL)
}

function stopQueuePolling() {
  if (queuePollTimer.value) { clearInterval(queuePollTimer.value); queuePollTimer.value = null }
}

// Also update the run_finished WS handler to re-check polling after a run ends
// (in case the finished run was on a device that had queued tasks)

onMounted(async () => {
  restoreTasks()
  await Promise.all([loadDevices(), loadCases()])
  tasks.value.forEach(t => { if (t.running && t.runId) connectTaskWS(t, t.runId) })
  if (hasQueuedTasks()) startQueuePolling()
})
async function loadCases() { try { const { data } = await client.get('/cases/definitions'); if (data.ok) cases.value = data.definitions } catch (_) {} }
async function loadDevices() {
  try { const { data } = await client.get('/devices'); if (data.ok) devices.value = (data.devices || []).filter(d => d.status === 'ONLINE' || d.status === 'BUSY') } catch (_) {}
}
</script>

<template>
  <div class="doc-page runner-page">
    <PageHeader title="执行引擎 Test Runner" subtitle="创建并监控测试任务，查看实时执行进度与历史结果" color="app-yellow" />
    <div class="doc-body">
      <section class="doc-section runner-section">
        <div class="doc-section__header">
          <h3 class="doc-section__title">任务列表<span class="doc-tag">Tasks</span></h3>
          <AnimalButton type="primary" @click="openNewTask">+ 新建任务</AnimalButton>
        </div>

        <!-- Tabs panel: cards render inside animal-tabs content slots -->
        <div class="tabs-panel">
          <Tabs
            class="runner-tabs"
            :items="filterTabs"
            v-model="activeTab"
            :leaf-animation="true"
            :shadow="true"
          >
            <template v-for="tab in filterTabs" #[tab.key] :key="tab.key">
              <div v-if="tasksForTab(tab.key).length" class="card-grid">
                <div
                  v-for="(task, idx) in tasksForTab(tab.key)"
                  :key="task.id"
                  class="task-card"
                  :style="{ background: cardGradient(idx) }"
                  @click="openTaskDetail(task)"
                >
                  <!-- Row 1: device serial + status badge -->
                  <div class="tc-row1">
                    <span class="tc-device">📱 {{ task.deviceSerial }}</span>
                    <span class="tc-status-badge" :style="{ background: taskStatusInfo(task).color }">
                      {{ taskStatusInfo(task).icon }} {{ taskStatusInfo(task).label }}
                    </span>
                  </div>

                  <!-- Row 2: meta -->
                  <div class="tc-row2">
                    <span>📋 {{ task.caseIds?.length || 0 }} 用例</span>
                    <span v-if="task.loopCount">🔁 {{ task.loopCount }} 轮</span>
                    <span class="tc-creator-tag">👤 {{ task.creator || '未知' }}</span>
                    <span class="tc-time">🕐 {{ formatTime(task.createdAt) }}</span>
                  </div>

                  <!-- Row 3: current case + progress -->
                  <div v-if="task.running && task.currentCaseTitle" class="tc-row3">
                    <span class="tc-current-label">▶ 正在执行：</span>
                    <span class="tc-current-name">{{ task.currentCaseTitle }}</span>
                  </div>
                  <div v-if="task.caseItems?.length" class="tc-row3">
                    <span class="tc-progress-text">
                      进度：{{ taskCompletedCount(task) }}/{{ taskTotalCount(task) }}
                      <template v-if="task.running && task.currentIteration">（第 {{ task.currentIteration }} 次循环）</template>
                    </span>
                  </div>

                  <!-- Progress bar -->
                  <el-progress
                    v-if="task.caseItems?.length"
                    :percentage="taskProgress(task)"
                    :stroke-width="6"
                    :show-text="true"
                    :color="taskStatusInfo(task).color"
                  />

                  <!-- Row 4: actions -->
                  <div class="tc-actions" @click.stop>
                    <el-button v-if="task.running" size="small" type="danger" @click="stopTask(task)">⏹ 停止</el-button>
                    <el-button v-else-if="!task.caseItems?.length" size="small" type="primary" @click="doStartTask(task)">▶ 执行</el-button>
                    <el-button v-else-if="task.caseItems?.[0]?.status === 'pending'" size="small" type="warning" @click="stopTask(task)">⏸ 停止执行</el-button>
                    <el-button v-else size="small" type="primary" @click="restartTask(task)">↻ 重新执行</el-button>
                    <el-button size="small" type="danger" plain @click="removeTask(task)">🗑 删除</el-button>
                  </div>
                </div>
              </div>

              <div v-else class="empty-hint">
                当前分类暂无任务{{ tab.key !== 'all' ? '，可切换到「全部」查看' : '' }}
              </div>
            </template>
          </Tabs>
        </div>
      </section>
    </div>

    <!-- New task modal -->
    <Modal
      v-model:open="showNewTask"
      title="新建测试任务"
      width="520px"
      :mask-closable="false"
      :typewriter="false"
      @close="showNewTask = false"
    >
      <div class="new-task-form">
        <el-form label-width="88px" label-position="right">
          <el-form-item label="任务名称">
            <el-input v-model="newForm.name" placeholder="如：稳定性测试" maxlength="30" clearable />
          </el-form-item>
          <el-form-item label="设备" required>
            <el-select v-model="newForm.deviceSerial" placeholder="选择在线设备" style="width:100%" :disabled="!devices.length">
              <el-option v-for="d in devices" :key="d.serial" :label="deviceLabel(d)" :value="d.serial" />
            </el-select>
            <p v-if="!devices.length" class="field-hint">暂无在线设备，请先在「设备管理」中连接</p>
          </el-form-item>
          <el-form-item label="用例" required>
            <el-select v-model="newForm.caseIds" multiple collapse-tags collapse-tags-tooltip placeholder="选择用例（可多选）" style="width:100%" :disabled="!cases.length">
              <el-option v-for="c in cases" :key="c.id" :label="c.title" :value="c.id" />
            </el-select>
            <p v-if="!cases.length" class="field-hint">暂无可用用例，请先在「测试用例」中创建</p>
          </el-form-item>
          <el-form-item label="循环次数">
            <el-input-number v-model="newForm.loopCount" :min="1" :max="10000" style="width:160px" />
          </el-form-item>
          <el-form-item label="执行方式">
            <el-radio-group v-model="newForm.mode">
              <el-radio value="now">立即执行</el-radio>
              <el-radio value="scheduled">定时执行</el-radio>
            </el-radio-group>
          </el-form-item>
          <template v-if="newForm.mode === 'scheduled'">
            <el-form-item label="开始时间">
              <el-date-picker v-model="newForm.startAt" type="datetime" placeholder="开始时间" style="width:100%" />
            </el-form-item>
            <el-form-item label="结束时间">
              <el-date-picker v-model="newForm.endAt" type="datetime" placeholder="结束时间（可选）" style="width:100%" />
            </el-form-item>
          </template>
        </el-form>
      </div>
      <template #footer>
        <AnimalButton @click="showNewTask = false">取消</AnimalButton>
        <AnimalButton type="primary" :disabled="!newForm.caseIds.length || !newForm.deviceSerial" @click="createAndStart">创建并执行</AnimalButton>
      </template>
    </Modal>
  </div>
</template>

<style scoped>
.runner-page { height: 100%; display: flex; flex-direction: column; overflow: hidden; }
.runner-page :deep(.doc-body) { flex: 1; min-height: 0; overflow: hidden; }
.runner-section { flex: 1; display: flex; flex-direction: column; min-height: 0; padding: 20px 24px 24px; }

/* Tabs panel — unified container for tabs + content */
.tabs-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  margin-top: 12px;
  border: 1px solid #e8e2d6;
  border-radius: 14px;
  background: #fff;
  overflow: hidden;
}
.tabs-panel :deep(.animal-tabs) {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding: 8px 16px 0;
}
.runner-tabs :deep(.animal-tabs__content) {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  padding-top: 12px;
}

/* Card grid */
.card-grid {
  flex: 1;
  overflow-y: auto;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
  padding: 12px 16px 16px;
  align-content: start;
}

/* Task card */
.task-card {
  cursor: pointer;
  border-radius: 14px;
  border: 1px solid rgba(139, 115, 85, 0.12);
  padding: 16px 18px 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  transition: all 0.2s;
  box-shadow: 0 1px 4px rgba(61, 52, 40, 0.04);
}
.task-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 18px rgba(61, 52, 40, 0.1);
}

/* Row 1: device + status */
.tc-row1 {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.tc-device {
  font-size: 14px;
  font-weight: 700;
  color: #4A3A28;
  font-family: 'Cascadia Code', Consolas, monospace;
}
.tc-status-badge {
  font-size: 11px;
  font-weight: 700;
  color: #fff;
  padding: 2px 10px;
  border-radius: 12px;
  white-space: nowrap;
}

/* Row 2: meta */
.tc-row2 {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px 12px;
  font-size: 12px;
  color: #6b5b48;
}
.tc-creator-tag {
  font-size: 11px;
  font-weight: 600;
  color: #fff;
  background: #b39ef3;
  padding: 1px 8px;
  border-radius: 10px;
}
.tc-time {
  font-size: 11px;
  color: #9f927d;
}

/* Row 3: current case + progress */
.tc-row3 {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
}
.tc-current-label {
  color: #409eff;
  font-weight: 600;
}
.tc-current-name {
  color: #4A3A28;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.tc-progress-text {
  color: #6b5b48;
  font-weight: 600;
}

/* Actions */
.tc-actions {
  display: flex;
  gap: 6px;
  padding-top: 2px;
  border-top: 1px solid rgba(139, 115, 85, 0.08);
}

.empty-hint { color: #988B7A; padding: 60px 0; text-align: center; font-size: 15px; flex: 1; display: flex; align-items: center; justify-content: center; }

.new-task-form { padding: 4px 0 8px; }
.new-task-form :deep(.el-form-item) { margin-bottom: 16px; }
.field-hint { margin: 6px 0 0; font-size: 12px; color: #e6a23c; line-height: 1.4; }

/* Responsive: single column on narrow screens */
@media (max-width: 900px) {
  .card-grid { grid-template-columns: 1fr; }
}
</style>
