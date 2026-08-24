/**
 * useTaskOperations — 任务操作逻辑（创建/启动/停止/删除/重跑/取消排队）
 *
 * 从 index.vue 提取，减少主文件 ~200 行。
 */
import { ElMessage } from 'element-plus'
import { generateTaskId, taskBucket } from './taskUtils'
import { startRun, stopRun, deleteTask, cancelQueue } from '../api'
import { closeTaskWebSocket } from './useTaskWebSocket'

function normalizeCaseIds(ids) {
  return (ids || []).map((id) => String(id))
}

function initTaskProgress(task, cases, availableCases) {
  const idSet = new Set(normalizeCaseIds(task.caseIds))
  const sourceCases = (task.taskType === 'api_testing' || task.taskType === 'web_automation')
    ? availableCases.value : cases.value
  task.caseItems = sourceCases
    .filter((c) => idSet.has(String(c.id)))
    .map((c, i) => {
      let rawSteps = c.steps_data || []
      if (!rawSteps.length && c.steps_json) {
        try { rawSteps = JSON.parse(c.steps_json) } catch (e) { console.error(e) }
      }
      const steps = rawSteps.map((s) => ({
        type: s.type || '', xpath: s.xpath || '',
        description: s.description || s.xpath || s.expected_text || '',
      }))
      return { id: c.id, title: c.title, index: i + 1, status: 'pending', pass: 0, fail: 0, total: task.loopCount, rate: 0, steps }
    })
  task.overallPass = 0
  task.overallFail = 0
  task.stepStates = []
}

export function useTaskOperations({
  tasks, cases, devices, availableCases,
  saveTaskToServer, scheduleSave, taskAddLog, getCurrentUsername,
  bindListTaskWS, loadCases, loadApiCases, loadWebCases,
  loadDevices, startQueuePolling, activeTab,
}) {
  async function doStartTask(task) {
    const isApi = task.taskType === 'api_testing'
    const isWeb = task.taskType === 'web_automation'
    if (isApi) {
      await loadApiCases()
    } else if (isWeb) {
      if (loadWebCases) await loadWebCases()
    } else if (!cases.value.length) {
      await loadCases()
    }
    initTaskProgress(task, cases, availableCases)
    if (!task.caseItems.length) {
      taskAddLog(task, '❌ 未匹配到用例，请确认用例列表已加载且用例ID有效', 'error')
      ElMessage.warning('用例数据未加载或ID不匹配，请刷新页面后重试')
      return
    }
    const body: Record<string, any> = {
      case_ids: task.caseIds,
      loop_count: task.loopCount,
      interval_seconds: task.intervalSeconds,
      device_serial: task.deviceSerial,
      client_task_id: task.id,
      task_type: task.taskType || 'ui_automation',
    }
    if (task.mode === 'scheduled') {
      if (task.startAt) body.start_at = new Date(task.startAt).toISOString()
      if (task.endAt) body.end_at = new Date(task.endAt).toISOString()
    }
    try {
      const { data } = await startRun(body)
      if (data.status && data.runs?.[0]?.run_id) {
        const idx = tasks.value.findIndex((t) => t.id === task.id)
        if (idx !== -1) {
          const runId = data.runs[0].run_id
          tasks.value[idx] = {
            ...tasks.value[idx],
            running: true,
            runId,
            status: 'running',
            state: 'running',  // Step 6 镜像同步
          }
          bindListTaskWS(tasks.value[idx], runId)
          taskAddLog(tasks.value[idx], '🚀 任务已启动')
        }
      } else if (data.status && data.queued?.length) {
        task.running = false
        task.status = 'queued'
        task.state = 'queued'  // Step 6 镜像同步
        task.outcome = ''
        task.conclusion = ''
        taskAddLog(task, '⏳ 设备正忙，任务已加入队列等待执行')
        ElMessage.info('设备正忙，任务已加入队列，设备空闲后自动执行')
        startQueuePolling()
      } else if (data.status) {
        task.running = false
        task.state = 'idle'  // Step 6 镜像同步
        taskAddLog(task, '❌ 设备不可用，任务未启动', 'error')
        ElMessage.warning('设备不可用或未就绪，任务已保存，可在列表中重试')
      } else {
        task.running = false
        task.state = 'idle'  // Step 6 镜像同步
        taskAddLog(task, `❌ ${data.message}`, 'error')
        ElMessage.error(data.message || '启动失败')
      }
    } catch (e) {
      task.running = false
      task.state = 'idle'  // Step 6 镜像同步
      const errMsg = e?.response?.data?.message || e.message || '未知错误'
      taskAddLog(task, `❌ ${errMsg}`, 'error')
      ElMessage.error(`启动失败：${errMsg}`)
    }
    scheduleSave(task.id)
  }

  async function doCancelQueue(task) {
    try {
      await cancelQueue(task.id, task.deviceSerial)
    } catch (e) {
      if (e?.response?.status !== 404) {
        ElMessage.error('取消排队失败，请检查网络后重试')
        return
      }
    }
    task.running = false
    task.runId = ''
    task.status = 'idle'
    task.state = 'idle'  // Step 6 镜像同步
    task.caseItems = []
    task.stepStates = []
    task.overallPass = 0
    task.overallFail = 0
    task.failedSteps = []
    task.logs = []
    saveTaskToServer(task)
  }

  async function doStopTask(task) {
    try {
      await stopRun(task.runId)
      ElMessage.success('停止请求已发送')
    } catch (e) {
      ElMessage.error('停止请求失败，请检查网络连接')
    }
    task.running = false
    task.status = 'done'
    task.state = 'done'  // Step 6 镜像同步
    task.currentCaseTitle = ''
    task.currentIteration = 0
    task.outcome = 'stopped'
    closeTaskWebSocket(task.id)
    saveTaskToServer(task)
  }

  async function doRemoveTask(task) {
    if (task.running) {
      if (task.runId) {
        try { await stopRun(task.runId) } catch (e) { console.error('[removeTask] stop failed:', e) }
      }
      closeTaskWebSocket(task.id)
    }
    try {
      await deleteTask(task.id)
    } catch (e) {
      console.error('[removeTask] delete failed:', e)
      ElMessage.error('删除失败，请检查网络后重试')
      return
    }
    tasks.value = tasks.value.filter((x) => x.id !== task.id)
    ElMessage.success('已删除')
  }

  function restartTask(task) {
    const round = (task.round || 0) + 1
    const tid = generateTaskId(new Set(tasks.value.map((t) => t.id)))
    const newTask = {
      id: tid, name: task.name, round,
      mode: task.mode, deviceSerial: task.deviceSerial,
      caseIds: [...task.caseIds], loopCount: task.loopCount,
      intervalSeconds: task.intervalSeconds || 5,
      running: false, runId: '', state: 'idle', caseItems: [], stepStates: [], logs: [],
      overallPass: 0, overallFail: 0,
      createdAt: new Date().toISOString(), creator: getCurrentUsername(),
      currentCaseTitle: '', currentIteration: 0, outcome: '',
    }
    tasks.value.push(newTask)
    saveTaskToServer(newTask)
    if (activeTab?.value) activeTab.value = taskBucket(newTask)
    ElMessage.success(`已创建新任务「${newTask.name}」第${round}轮`)
    doStartTask(newTask)
  }

  async function createAndStart(newForm, showNewTask, resetNewForm) {
    if (!newForm.value.name.trim()) {
      ElMessage.warning('请输入任务名称')
      return
    }
    if (newForm.value.taskType === 'ui_automation' && !newForm.value.deviceSerial) {
      ElMessage.warning('Android UI 自动化任务需要选择执行设备')
      return
    }
    if (!newForm.value.caseIds.length) {
      ElMessage.warning('请至少选择一个测试用例')
      return
    }
    if (newForm.value.intervalSeconds < 5) {
      ElMessage.warning('轮间间隔最小为 5 秒，请重新设置')
      return
    }
    const tid = generateTaskId(new Set(tasks.value.map((t) => t.id)))
    const task = {
      id: tid, name: newForm.value.name.trim(),
      taskType: newForm.value.taskType, mode: newForm.value.mode,
      startAt: newForm.value.startAt, endAt: newForm.value.endAt,
      deviceSerial: newForm.value.deviceSerial,
      caseIds: normalizeCaseIds(newForm.value.caseIds),
      loopCount: newForm.value.loopCount,
      intervalSeconds: newForm.value.intervalSeconds,
      running: false, runId: '', status: 'idle', state: 'idle',
      caseItems: [], stepStates: [], logs: [],
      overallPass: 0, overallFail: 0,
      createdAt: new Date().toISOString(), creator: getCurrentUsername(),
      currentCaseTitle: '', currentIteration: 0, outcome: '', round: 0,
    }
    tasks.value.push(task)
    await saveTaskToServer(task)
    resetNewForm()
    showNewTask.value = false
    ElMessage.success(`任务「${task.name}」已创建`)
    await doStartTask(task)
    const updated = tasks.value.find((t) => t.id === task.id) || task
    await saveTaskToServer(updated)
    if (activeTab?.value) activeTab.value = taskBucket(updated)
  }

  return {
    doStartTask, doCancelQueue, doStopTask, doRemoveTask,
    restartTask, createAndStart,
  }
}
