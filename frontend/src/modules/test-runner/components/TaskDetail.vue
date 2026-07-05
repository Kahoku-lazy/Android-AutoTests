<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import client from '@/shared/api-client.js'
import { wsUrl } from '@/shared/ws-url.js'
import { Button as AnimalButton } from 'animal-island-vue'
import PageHeader from '@/shared/components/PageHeader.vue'

const route = useRoute()
const router = useRouter()
const taskId = computed(() => String(route.params.taskId))

const STORAGE_KEY = '_runner_tasks'
const WS_KEY = '_task_ws_map'
const task = ref(null)

function loadTask() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) { console.warn('[TaskDetail] localStorage empty'); return }
    const tasks = JSON.parse(raw)
    if (!Array.isArray(tasks)) { console.warn('[TaskDetail] tasks not array'); return }
    const tid = taskId.value
    task.value = tasks.find(t => String(t.id) === String(tid)) || null
    if (!task.value) {
      console.warn(`[TaskDetail] task not found: id="${tid}", available=[${tasks.map(t => t.id).join(', ')}]`)
    }
  } catch (e) {
    console.error('[TaskDetail] loadTask error:', e)
  }
}

function saveTask() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return
    const tasks = JSON.parse(raw)
    if (!Array.isArray(tasks)) return
    const idx = tasks.findIndex(t => String(t.id) === String(taskId.value))
    if (idx >= 0 && task.value) {
      tasks[idx] = JSON.parse(JSON.stringify(task.value))
      localStorage.setItem(STORAGE_KEY, JSON.stringify(tasks))
    }
  } catch (e) {
    console.error('[TaskDetail] saveTask error:', e)
  }
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
  const ci = task.value?.caseItems; if (!ci?.length) return 0
  const total = ci.reduce((s, c) => s + c.total, 0)
  const done = ci.reduce((s, c) => s + c.pass + c.fail, 0)
  return total ? Math.round(done / total * 100) : 0
}
function taskCompleted() {
  const ci = task.value?.caseItems; if (!ci?.length) return 0
  return ci.reduce((s, c) => s + c.pass + c.fail, 0)
}
function taskTotal() {
  const ci = task.value?.caseItems; if (!ci?.length) return 0
  return ci.reduce((s, c) => s + c.total, 0)
}
function taskStatusInfo() {
  const t = task.value; if (!t) return { label: '', color: '#888' }
  if (t.running) return { label: '执行中', color: '#889df0', icon: '⚡' }
  if (!t.caseItems?.length) return { label: '未执行', color: '#8b7355', icon: '📝' }
  if (t.caseItems[0]?.status === 'pending') return { label: '等待中', color: '#f7cd67', icon: '⏳' }
  return { label: '已完成', color: '#6fba2c', icon: '✅' }
}
function formatTime(isoStr) {
  if (!isoStr) return '—'
  try {
    const d = new Date(isoStr)
    const pad = n => String(n).padStart(2, '0')
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
  } catch (_) { return isoStr }
}

// ── Report helpers ──
const isTaskDone = computed(() => {
  const t = task.value; if (!t) return false
  return !t.running && t.caseItems?.length && t.caseItems[0]?.status !== 'pending'
})

const expandedFailures = ref(new Set())

function toggleFailureCase(title) {
  const s = new Set(expandedFailures.value)
  if (s.has(title)) s.delete(title)
  else s.add(title)
  expandedFailures.value = s
}

function failedStepsByCase() {
  if (!task.value?.failedSteps?.length) return []
  const map = {}
  for (const f of task.value.failedSteps) {
    const key = f.caseTitle || '未知用例'
    if (!map[key]) map[key] = []
    map[key].push(f)
  }
  return Object.entries(map).map(([title, steps]) => {
    // Collect unique failed iterations
    const iters = [...new Set(steps.map(s => s.iteration))].sort((a, b) => a - b)
    return { title, steps, iters }
  })
}

function groupFailedByIteration(steps) {
  const map = {}
  for (const s of steps) {
    const key = `第 ${s.iteration} 轮`
    if (!map[key]) map[key] = []
    map[key].push(s)
  }
  return Object.entries(map)
}

function updateConclusion(val) {
  if (task.value) task.value.conclusion = val
  saveTask()
}

function updateBugTicket(val) {
  if (task.value) task.value.bugTicket = val
  saveTask()
}

function stepTypeLabel(type) {
  const map = { click: '点击', long_click: '长按', click_indexed: '点击第N个', swipe: '滑动',
    drag: '拖动', wait: '等待出现', wait_disappear: '等待消失', wait_any: '等待任一',
    wait_toast: '等待Toast', verify_text: '校验文字', poll_text: '等待文字',
    start_app: '启动应用', kill_app: '关闭应用', restart_app: '重启应用',
    retry_click: '点击后等待', sleep: '暂停', log: '记录' }
  return map[type] || type
}

// ── WS ──
function getWsMap() { return window[WS_KEY] || {} }
function setWsMap(m) { window[WS_KEY] = m }

function connectTaskWS(runId) {
  if (!task.value) return
  const wm = getWsMap()
  if (wm[task.value.id]) { try { wm[task.value.id].close() } catch (_) {} }
  const url = `${wsUrl('/ws/test-run/' + runId)}?token=${encodeURIComponent(localStorage.getItem('access_token') || '')}`
  const ws = new WebSocket(url)
  wm[task.value.id] = ws
  setWsMap(wm)

  ws.onopen = () => taskAddLog('🟢 日志已连接', 'success')

  ws.onmessage = (e) => {
    if (!task.value) return
    try {
      const msg = JSON.parse(e.data)
      const ci = task.value.caseItems?.find(c => c.id === msg.case_id)
      switch (msg.type) {
        case 'log': taskAddLog(msg.message); break
        case 'case_started':
          if (ci) { ci.status = 'running'; ci.pass = 0; ci.fail = 0 }
          if (!task.value.stepStates) task.value.stepStates = []
          task.value.stepStates = []
          task.value.currentCaseTitle = ci?.title || msg.case_id || ''
          task.value.currentIteration = 1
          saveTask()
          break
        case 'step_result':
          if (!task.value.stepStates) task.value.stepStates = []
          task.value.stepStates = [...task.value.stepStates.filter(s => s.index !== msg.step_index),
            { index: msg.step_index, total: msg.total_steps, type: msg.step_type, desc: msg.description, result: msg.result }
          ].sort((a, b) => a.index - b.index)
          // Track failed steps for report
          if (msg.result !== 'pass' && msg.result !== 'stopped') {
            if (!task.value.failedSteps) task.value.failedSteps = []
            const dup = task.value.failedSteps.find(
              f => f.caseTitle === ci?.title && f.iteration === (task.value.currentIteration || 1) && f.stepIndex === msg.step_index
            )
            if (!dup) {
              task.value.failedSteps.push({
                caseTitle: ci?.title || msg.case_id || '',
                iteration: task.value.currentIteration || 1,
                stepIndex: msg.step_index,
                stepType: msg.step_type,
                description: msg.description || '',
                result: msg.result,
              })
            }
          }
          break
        case 'iteration_result':
          if (msg.result === 'pass') { if (ci) ci.pass++; task.value.overallPass = (task.value.overallPass || 0) + 1 }
          else { if (ci) ci.fail++; task.value.overallFail = (task.value.overallFail || 0) + 1 }
          if (ci) ci.rate = ci.total ? Math.round((ci.pass + ci.fail) / ci.total * 100) : 0
          task.value.currentIteration = (ci ? ci.pass + ci.fail : task.value.currentIteration || 0) + 1
          saveTask()
          break
        case 'case_finished':
          if (ci) { ci.status = 'done'; ci.pass = parseInt(msg.pass); ci.fail = parseInt(msg.fail); ci.rate = 100 }
          saveTask()
          break
        case 'run_finished':
          task.value.running = false
          delete wm[task.value.id]; setWsMap(wm)
          task.value.caseItems?.forEach(c => { if (c.status !== 'done') c.status = 'done' })
          task.value.currentCaseTitle = ''; task.value.currentIteration = 0
          // Auto-generate conclusion if not manually set
          if (!task.value.conclusion) {
            const pf = task.value.overallFail || 0
            task.value.conclusion = pf === 0 ? '✅ 测试通过：所有用例全部执行成功' : `❌ 测试不通过：${pf} 个用例执行失败`
          }
          taskAddLog(`🏁 完成 ✅${task.value.overallPass || 0} ❌${task.value.overallFail || 0}`, 'success')
          saveTask()
          break
        case 'device_error':
          task.value.running = false
          taskAddLog(`💥 ${msg.error}`, 'error')
          saveTask()
          break
      }
    } catch (_) {}
  }
  ws.onclose = () => { if (task.value?.running) taskAddLog('🔴 日志断开', 'warn') }
}

let saveTimer = null
// Reload when route param changes (e.g. clicking different task cards)
watch(taskId, (newId) => {
  loadTask()
  if (task.value?.running && task.value.runId) {
    const wm = getWsMap()
    if (!wm[task.value.id]) connectTaskWS(task.value.runId)
  }
})

onMounted(() => {
  loadTask()
  if (!task.value) return
  if (task.value.running && task.value.runId) {
    const wm = getWsMap()
    if (!wm[task.value.id]) connectTaskWS(task.value.runId)
  }
  // Periodic save
  saveTimer = setInterval(() => { if (task.value) saveTask() }, 3000)
  // Start queue polling if task is queued
  if (task.value && !task.value.running && task.value.caseItems?.length && task.value.caseItems[0]?.status === 'pending') {
    startDetailQueuePolling()
  }
})

onUnmounted(() => {
  if (saveTimer) clearInterval(saveTimer)
  stopDetailQueuePolling()
})

// ── Actions ──
async function stopTask() {
  if (!task.value) return
  if (!task.value.runId) {
    // Queued task — remove from list
    try { await ElMessageBox.confirm('确定移除该排队任务？', '移除排队任务', { confirmButtonText: '移除', cancelButtonText: '取消', type: 'warning' }) } catch (_) { return }
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      if (raw) {
        const tasks = JSON.parse(raw).filter(t => t.id !== taskId.value)
        localStorage.setItem(STORAGE_KEY, JSON.stringify(tasks))
      }
    } catch (_) {}
    router.push('/runner')
    return
  }
  try { await ElMessageBox.confirm('确定停止该任务？', '停止任务', { confirmButtonText: '停止', cancelButtonText: '取消', type: 'warning' }) } catch (_) { return }
  try { await client.post(`/runner/run/${task.value.runId}/stop`) } catch (_) {}
  task.value.running = false
  task.value.currentCaseTitle = ''
  task.value.currentIteration = 0
  saveTask()
}

async function restartTask() {
  if (!task.value) return
  task.value.caseItems = []; task.value.stepStates = []; task.value.overallPass = 0
  task.value.overallFail = 0; task.value.logs = []
  task.value.currentCaseTitle = ''; task.value.currentIteration = 0
  saveTask()
  // Re-run via parent logic — we need to load cases first
  try { const { data } = await client.get('/cases/definitions'); if (!data.ok) { ElMessage.error('无法加载用例'); return } }
  catch (_) { ElMessage.error('无法加载用例'); return }
  // Trigger start through the runner endpoint
  const body = { case_ids: task.value.caseIds, loop_count: task.value.loopCount, device_serial: task.value.deviceSerial, client_task_id: task.value.id }
  try {
    const { data } = await client.post('/runner/run', body)
    if (data.ok && data.runs?.[0]?.run_id) {
      task.value.running = true
      task.value.runId = data.runs[0].run_id
      task.value.currentCaseTitle = ''
      task.value.currentIteration = 0
      connectTaskWS(task.value.runId)
      taskAddLog('🚀 任务已重新启动')
    } else if (data.ok && data.queued?.length) {
      task.value.running = false
      taskAddLog('⏳ 设备正忙，任务已加入队列等待执行')
      ElMessage.info('设备正忙，任务已加入队列，设备空闲后自动执行')
      startDetailQueuePolling()
    } else {
      taskAddLog('❌ 启动失败', 'error')
      ElMessage.error(data.error || '启动失败')
    }
  } catch (e) {
    taskAddLog(`❌ ${e.message}`, 'error')
    ElMessage.error('启动失败')
  }
}

// ── Detail queue polling ──
const detailPollTimer = ref(null)

async function pollDetailQueuedTask() {
  if (!task.value || task.value.running) { stopDetailQueuePolling(); return }
  // Only poll if this task is queued (not running, has caseItems in pending)
  if (!task.value.caseItems?.length || task.value.caseItems[0]?.status !== 'pending') {
    stopDetailQueuePolling(); return
  }
  try {
    const { data } = await client.get('/runner/active')
    if (!data.ok || !data.active?.length) return
    for (const active of data.active) {
      if (active.client_task_id === task.value.id) {
        task.value.running = true
        task.value.runId = active.run_id
        connectTaskWS(active.run_id)
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
    try { await client.post(`/runner/run/${task.value.runId}/stop`) } catch (_) {}
    const wm = getWsMap(); if (wm[task.value.id]) { try { wm[task.value.id].close() } catch (_) {}; delete wm[task.value.id]; setWsMap(wm) }
  }
  // Remove from localStorage
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) {
      const tasks = JSON.parse(raw).filter(t => t.id !== taskId.value)
      localStorage.setItem(STORAGE_KEY, JSON.stringify(tasks))
    }
  } catch (_) {}
  router.push('/runner')
}
</script>

<template>
  <div v-if="task" class="doc-page detail-page">
    <PageHeader
      title="任务详情 Task Detail"
      :subtitle="`设备 ${task.deviceSerial} · ${task.caseIds?.length || 0} 个用例 · ${task.loopCount} 轮`"
      color="app-yellow"
    />

    <div class="doc-body">
      <!-- ── Info card ── -->
      <section class="info-card">
        <div class="info-grid">
          <div class="info-item">
            <span class="info-label">📱 设备</span>
            <span class="info-value">{{ task.deviceSerial }}</span>
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
            <span class="info-label">▶ 当前用例</span>
            <span class="info-value current-case">{{ task.currentCaseTitle }}</span>
          </div>
          <div v-if="task.caseItems?.length" class="info-item">
            <span class="info-label">🔄 进度</span>
            <span class="info-value">{{ taskCompleted() }}/{{ taskTotal() }}
              <template v-if="task.running && task.currentIteration">（第 {{ task.currentIteration }} 次循环）</template>
            </span>
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

        <!-- Actions -->
        <div class="info-actions">
          <AnimalButton @click="router.push('/runner')">← 返回列表</AnimalButton>
          <AnimalButton v-if="task.running" type="danger" @click="stopTask">⏹ 停止</AnimalButton>
          <AnimalButton v-else-if="!task.caseItems?.length" type="primary" @click="restartTask">▶ 执行</AnimalButton>
          <AnimalButton v-else-if="task.caseItems?.[0]?.status === 'pending'" type="warning" @click="stopTask">⏸ 停止执行</AnimalButton>
          <AnimalButton v-else type="primary" @click="restartTask">↻ 重新执行</AnimalButton>
          <AnimalButton type="danger" plain @click="removeTask">🗑 删除</AnimalButton>
        </div>
      </section>

      <!-- ── Case progress ── -->
      <section v-if="task.caseItems?.length" class="doc-section case-section">
        <h3 class="doc-section__title">用例进度 <span class="doc-tag">Progress</span></h3>
        <div class="doc-section__label">各用例执行状态与通过 / 失败统计</div>
        <div v-for="ci in task.caseItems" :key="ci.id" class="case-row">
          <span class="ci-idx">{{ ci.index }}</span>
          <span class="ci-title">{{ ci.title }}</span>
          <span :class="['ci-status', ci.status]">{{ ci.status === 'running' ? '▶ 执行中' : ci.status === 'done' ? '✅ 完成' : '⏸ 等待' }}</span>
          <span class="ci-stats">✅{{ ci.pass }} ❌{{ ci.fail }} {{ ci.pass + ci.fail }}/{{ ci.total }}</span>
          <el-progress :percentage="ci.rate" :stroke-width="4" :show-text="false" style="width:120px" :status="ci.status === 'done' ? 'success' : ''" />
        </div>
      </section>

      <!-- ── Current steps ── -->
      <section v-if="task.stepStates?.length" class="doc-section step-section">
        <h3 class="doc-section__title">当前步骤 <span class="doc-tag">Steps</span></h3>
        <div class="doc-section__label">最近执行的步骤结果</div>
        <div class="step-chips">
          <span v-for="s in task.stepStates" :key="s.index" :class="['step-chip', s.result === 'pass' ? 'ok' : 'fail']">
            {{ s.result === 'pass' ? '✅' : '❌' }}{{ s.desc?.slice(0, 15) || s.type }}
          </span>
        </div>
      </section>

      <!-- ── Test Report (shown when task completed) ── -->
      <section v-if="isTaskDone" class="doc-section report-section">
        <h3 class="doc-section__title">📊 执行报告 <span class="doc-tag">Report</span></h3>
        <div class="doc-section__label">任务执行完毕后的统计与结论</div>

        <!-- Summary stats -->
        <div class="report-stats">
          <div class="rstat pass">
            <span class="rstat-num">{{ task.overallPass || 0 }}</span>
            <span class="rstat-label">✅ 用例成功</span>
          </div>
          <div class="rstat fail">
            <span class="rstat-num">{{ task.overallFail || 0 }}</span>
            <span class="rstat-label">❌ 用例失败</span>
          </div>
          <div class="rstat total">
            <span class="rstat-num">{{ (task.overallPass || 0) + (task.overallFail || 0) }}</span>
            <span class="rstat-label">📋 总执行次数</span>
          </div>
          <div class="rstat rate">
            <span class="rstat-num">{{ taskProgress() }}%</span>
            <span class="rstat-label">📈 通过率</span>
          </div>
        </div>

        <!-- Failed steps: collapsible case list -->
        <div v-if="failedStepsByCase().length" class="report-failures">
          <h4 class="report-subtitle">❌ 失败用例</h4>
          <div
            v-for="fc in failedStepsByCase()"
            :key="fc.title"
            class="failure-case"
            :class="{ expanded: expandedFailures.has(fc.title) }"
          >
            <!-- Summary row: click to expand -->
            <div class="failure-case-header" @click="toggleFailureCase(fc.title)">
              <span class="fcase-expand">{{ expandedFailures.has(fc.title) ? '▼' : '▶' }}</span>
              <span class="fcase-title">📋 {{ fc.title }}</span>
              <span class="fcase-iters">
                <span v-for="it in fc.iters" :key="it" class="fcase-iter-tag">第{{ it }}次</span>
              </span>
              <span class="fcase-count">{{ fc.steps.length }} 处失败</span>
            </div>
            <!-- Expanded detail -->
            <div v-show="expandedFailures.has(fc.title)" class="failure-case-body">
              <div v-for="(iterGroup, iterName) in groupFailedByIteration(fc.steps)" :key="iterName" class="failure-iter">
                <div class="failure-iter-label">{{ iterName }}</div>
                <div v-for="(s, si) in iterGroup" :key="si" class="failure-step">
                  <span class="fstep-idx">步骤 {{ s.stepIndex + 1 }}</span>
                  <span class="fstep-type">{{ stepTypeLabel(s.stepType) }}</span>
                  <span class="fstep-desc">{{ s.description || '(无描述)' }}</span>
                  <span class="fstep-result">{{ s.result }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="report-no-failures">
          🎉 所有步骤均执行成功，无失败记录
        </div>

        <!-- Bug ticket -->
        <div class="report-field">
          <label class="report-label">🐛 BUG 单</label>
          <el-input
            :model-value="task.bugTicket || ''"
            type="textarea"
            :rows="2"
            placeholder="记录关联的 BUG 编号或链接，如：BUG-001, https://jira.xxx.com/browse/XXX-123"
            @input="updateBugTicket"
          />
        </div>
      </section>

      <!-- ── Execution logs ── -->
      <section class="doc-section log-section">
        <div class="doc-section__header">
          <h3 class="doc-section__title">执行日志 <span class="doc-tag">Logs</span></h3>
          <el-button size="small" text @click="task.logs = []">清空</el-button>
        </div>
        <div class="doc-section__label">实时 WebSocket 日志输出 ({{ task.logs?.length || 0 }} 条)</div>
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
    <AnimalButton @click="router.push('/runner')">← 返回任务列表</AnimalButton>
  </div>
</template>

<style scoped>
.detail-page {
  display: flex;
  flex-direction: column;
  min-height: 100%;
  overflow: hidden;
}
.detail-page :deep(.doc-body) {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 18px;
  overflow-y: auto;
  padding-bottom: 40px;
}

/* ── Info card ── */
.info-card {
  background: linear-gradient(135deg, #fef9ef 0%, #fdf0d5 100%);
  border-radius: 14px;
  border: 1px solid rgba(139, 115, 85, 0.1);
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.info-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px 20px;
}
.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}
.info-item.full-width { grid-column: 1 / -1; }
.info-label { color: #9f927d; font-weight: 500; white-space: nowrap; }
.info-value { color: #4A3A28; font-weight: 600; }
.info-value.current-case { color: #409eff; }
.info-tag {
  font-size: 11px;
  font-weight: 700;
  color: #fff;
  padding: 2px 10px;
  border-radius: 12px;
  white-space: nowrap;
}
.info-tag.creator { background: #b39ef3; }
.info-progress { margin-top: 2px; }
.info-actions {
  display: flex;
  gap: 8px;
  padding-top: 4px;
  border-top: 1px solid rgba(139, 115, 85, 0.08);
}

/* ── Sections ── */
.case-section, .step-section { padding: 18px 24px; }
.case-section :deep(.doc-section__title),
.step-section :deep(.doc-section__title) { margin-bottom: 4px; }

.case-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  font-size: 13px;
  border-bottom: 1px solid #f0ebe0;
  background: #faf9f4;
  border-radius: 8px;
  margin-bottom: 6px;
}
.case-row:last-child { border-bottom: none; margin-bottom: 0; }
.ci-idx { color: #19c8b9; font-weight: 700; width: 22px; }
.ci-title { flex: 1; font-weight: 600; color: #4A3A28; }
.ci-status { font-size: 12px; min-width: 60px; }
.ci-status.running { color: #409eff; }
.ci-status.done { color: #67c23a; }
.ci-status.pending { color: #e6a23c; }
.ci-stats { font-family: 'Cascadia Code', monospace; font-size: 12px; color: #8a7b66; min-width: 90px; }

/* Step chips */
.step-chips { display: flex; flex-wrap: wrap; gap: 4px; }
.step-chip { font-size: 11px; padding: 3px 10px; border-radius: 10px; font-weight: 600; }
.step-chip.ok { background: rgba(103, 194, 58, .12); color: #529b2a; }
.step-chip.fail { background: rgba(245, 108, 108, .12); color: #d9534f; }

/* ── Report ── */
.report-section { padding: 18px 24px; }
.report-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin: 14px 0;
}
.rstat {
  text-align: center;
  padding: 14px 8px;
  border-radius: 12px;
  background: #faf9f4;
}
.rstat.pass { border-left: 3px solid #6fba2c; }
.rstat.fail { border-left: 3px solid #e85f5f; }
.rstat.total { border-left: 3px solid #889df0; }
.rstat.rate { border-left: 3px solid #f7cd67; }
.rstat-num { display: block; font-size: 24px; font-weight: 800; color: #4A3A28; }
.rstat-label { display: block; font-size: 12px; color: #9f927d; margin-top: 4px; }

.report-failures { margin-top: 14px; }
.report-subtitle { font-size: 14px; font-weight: 700; color: #e85f5f; margin: 0 0 10px; }
.report-no-failures { text-align: center; color: #6fba2c; padding: 16px; font-size: 14px; font-weight: 600; }

.failure-case {
  background: #faf9f4;
  border-radius: 10px;
  margin-bottom: 8px;
  border: 1px solid #f0ebe0;
  overflow: hidden;
  transition: all 0.2s;
}
.failure-case.expanded { border-color: #e85f5f; }
.failure-case-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  cursor: pointer;
  user-select: none;
  transition: background 0.15s;
}
.failure-case-header:hover { background: rgba(232, 95, 95, 0.04); }
.fcase-expand { font-size: 10px; color: #9f927d; width: 14px; flex-shrink: 0; }
.fcase-title { font-size: 13px; font-weight: 700; color: #4A3A28; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.fcase-iters { display: flex; gap: 4px; flex-shrink: 0; }
.fcase-iter-tag {
  font-size: 10px; font-weight: 700; color: #fff; background: #e85f5f;
  padding: 1px 6px; border-radius: 8px; white-space: nowrap;
}
.fcase-count { font-size: 11px; color: #9f927d; white-space: nowrap; }

.failure-case-body {
  padding: 0 14px 10px;
  margin-left: 22px;
  border-left: 2px solid rgba(232, 95, 95, 0.15);
}
.failure-iter { margin-bottom: 4px; }
.failure-iter-label { font-size: 11px; font-weight: 600; color: #9f927d; padding: 2px 0 4px; }
.failure-step {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  background: #fff5f5;
  border-radius: 6px;
  margin-bottom: 3px;
  font-size: 12px;
}
.fstep-idx { color: #e85f5f; font-weight: 700; white-space: nowrap; }
.fstep-type { color: #8b7355; background: rgba(139,115,85,0.08); padding: 1px 6px; border-radius: 4px; font-size: 11px; }
.fstep-desc { flex: 1; color: #5c4b38; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.fstep-result { color: #d9534f; font-weight: 600; font-family: monospace; font-size: 11px; }

.report-field { margin-top: 14px; }
.report-label { display: block; font-size: 13px; font-weight: 700; color: #6b5b48; margin-bottom: 6px; }

/* ── Logs ── */
.log-section {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  padding: 18px 24px;
  background: #1e1e24;
  border: 1px solid #33333a;
  border-radius: 12px;
  overflow: hidden;
}
.log-section :deep(.doc-section__title) { color: #e8e2d6; }
.log-section :deep(.doc-section__label) { color: #8f8a7d; flex-shrink: 0; }
.log-section :deep(.doc-section__header) { margin-bottom: 0; flex-shrink: 0; }
.log-card-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  margin-top: 10px;
  padding: 12px 16px;
  border-radius: 10px;
  background: #16161c;
  font-family: 'Cascadia Code', Consolas, monospace;
  font-size: 13px;
  line-height: 1.7;
}
.log-line { padding: 2px 4px; border-bottom: 1px solid rgba(255,255,255,.04); white-space: pre-wrap; color: #c5c5c5; }
.log-time { color: #666; margin-right: 8px; font-size: 11px; }
.log-info { color: #bbb; }
.log-success { color: #67c23a; }
.log-error { color: #f56c6c; }
.log-warn { color: #e6a23c; }
.log-empty { text-align: center; color: #666; padding: 40px; font-size: 13px; }

.not-found { text-align: center; color: #9f927d; padding: 80px 0; font-size: 15px; }
.not-found p { margin-bottom: 16px; }
</style>
