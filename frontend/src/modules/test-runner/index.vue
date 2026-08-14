<script setup>
import { ref, computed, watch, onMounted, onUnmounted, onDeactivated, onActivated } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { getActiveUsername } from "@/shared/auth/token-storage";
import ConfirmButton from "@/shared/components/patterns/ConfirmButton.vue";
import EmptyState from "@/shared/components/patterns/EmptyState.vue";
import ErrorState from "@/shared/components/patterns/ErrorState.vue";
import AppTable from "@/shared/components/AppTable.vue";
import WorkbenchHeader from "@/shared/components/WorkbenchHeader.vue";
import FilterTabs from "@/shared/components/FilterTabs.vue";
import KpiCard from "@/shared/components/KpiCard.vue";
import {
  generateTaskId,
  readTaskCounter,
  writeTaskCounter,
  isTaskQueued,
  deriveTaskStatus,
  taskBucket,
  taskCardClass,
  taskStatusInfo,
  taskCompletedCount,
  taskTotalCount,
  taskPassRate,
  taskCardRateBg,
  taskProgress,
  buildTaskSavePayload,
} from "./composables/taskUtils";
import { useDebouncedSave } from "./composables/useDebouncedSave";
import { useQueuePoller } from "./composables/useQueuePoller";
import NewTaskDialog from "./components/NewTaskDialog.vue";
import {
  connectTaskWebSocket,
  closeTaskWebSocket,
  closeAllTaskWebSockets,
  applyWsMessage,
} from "./composables/useTaskWebSocket";
import { startRun, stopRun, getActiveRuns, listDefinitions, listDevices, listTasks, saveTask, deleteTask, cancelQueue, listApiDefinitions, listWebDefinitions } from "./api";

const router = useRouter();

const cases = ref([]);
const devices = ref([]);
const showNewTask = ref(false);
const error = ref("");

const activeTab = ref("running");
const viewMode = ref("table");
const searchQuery = ref("");
const tasks = ref([]);
const kpiStats = computed(() => ({running:tasks.value.filter(t=>deriveTaskStatus(t)==="running").length,waiting:tasks.value.filter(t=>isTaskQueued(t)).length,completed:tasks.value.filter(t=>taskBucket(t)==="completed").length,incomplete:tasks.value.filter(t=>taskBucket(t)==="incomplete"||deriveTaskStatus(t)==="idle").length}));
const groupedTasks = computed(() => ({running:filteredTasks.value.filter(t=>deriveTaskStatus(t)==="running"),waiting:filteredTasks.value.filter(t=>isTaskQueued(t)),completed:filteredTasks.value.filter(t=>taskBucket(t)==="completed"),incomplete:filteredTasks.value.filter(t=>taskBucket(t)==="incomplete"||deriveTaskStatus(t)==="idle")}));
const filteredTasks = computed(()=>{let l=tasks.value;if(activeTab.value!=="all")l=l.filter(t=>{if(activeTab.value==="running")return deriveTaskStatus(t)==="running";if(activeTab.value==="waiting")return isTaskQueued(t);if(activeTab.value==="completed")return taskBucket(t)==="completed";if(activeTab.value==="incomplete")return taskBucket(t)==="incomplete";if(activeTab.value==="idle")return deriveTaskStatus(t)==="idle";return true});const q=searchQuery.value.trim().toLowerCase();if(q)l=l.filter(t=>(t.name||"").toLowerCase().includes(q)||(t.id||"").toLowerCase().includes(q)||(t.deviceSerial||"").toLowerCase().includes(q));return l});
const tableColumns = [{dataIndex:"id",title:"任务ID",minWidth:90},{dataIndex:"name",title:"名称",minWidth:150},{dataIndex:"taskType",title:"类型",minWidth:80,align:"center"},{dataIndex:"deviceSerial",title:"设备",minWidth:120},{dataIndex:"cases",title:"用例",minWidth:60,align:"center"},{dataIndex:"progress",title:"进度",minWidth:140},{dataIndex:"passRate",title:"成功率",minWidth:80,align:"center"},{dataIndex:"status",title:"状态",minWidth:100,align:"center"},{dataIndex:"time",title:"时间",minWidth:100},{dataIndex:"actions",title:"操作",width:200,fixed:"right"}];

// ── Active account username for creator（JWT sub 是 user id，不能当用户名）──
function getCurrentUsername() {
  return getActiveUsername() || "未知";
}


// ── Server persistence ──
async function saveTaskToServer(task) {
  try {
    await saveTask(buildTaskSavePayload(task));
  } catch (e) {
    console.error("[saveTaskToServer] failed:", e);
    ElMessage.error("保存任务失败，请检查网络");
  }
}

const { scheduleSave, flushSave, cleanup: cleanupDebouncedSave } = useDebouncedSave(tasks, saveTaskToServer);

async function loadTasks() {
  try {
    const { data } = await listTasks();
    if (data.status && data.tasks) {
      tasks.value = data.tasks.map((d) => ({
        ...d,
        status: d.status || "idle",
        createdAt: d.createdAt || "",
        creator: d.creator || "",
        currentCaseTitle: d.currentCaseTitle || "",
        currentIteration: d.currentIteration || 0,
        failedSteps: d.failedSteps || [],
        outcome: d.outcome || "",
        intervalSeconds: d.intervalSeconds || 5,
        round: d.round || 0,
        conclusion: d.conclusion || "",
        bugTicket: d.bugTicket || "",
        startAt: d.startAt || "",
        endAt: d.endAt || "",
      }));
      // Sync counter
      let maxSeq = 0;
      for (const t of tasks.value) {
        const m = String(t.id).match(/^ID-(\d+)$/);
        if (m) maxSeq = Math.max(maxSeq, parseInt(m[1]));
      }
      if (maxSeq >= readTaskCounter()) writeTaskCounter(maxSeq);
    }
    error.value = "";
  } catch (e) {
    error.value = "加载任务列表失败，请检查网络连接";
    console.error(e);
  }
}

// Throttled save — 见上方 scheduleSave

// ── Filter ──
const runningTasks = computed(() => tasks.value.filter((t) => t.running));
const waitingTasks = computed(() => tasks.value.filter((t) => isTaskQueued(t)));
const completedTasks = computed(() =>
  tasks.value.filter((t) => taskBucket(t) === "completed"),
);
const incompleteTasks = computed(() =>
  tasks.value.filter((t) => taskBucket(t) === "incomplete"),
);
const idleTasks = computed(() =>
  tasks.value.filter((t) => deriveTaskStatus(t) === "idle"),
);
const filterAppTabs = computed(() => [
  { key: "all", label: `📋 全部 (${tasks.value.length})` },
  { key: "running", label: `⚡ 执行中 (${runningTasks.value.length})` },
  { key: "waiting", label: `⏳ 等待中 (${waitingTasks.value.length})` },
  { key: "completed", label: `✅ 已完成 (${completedTasks.value.length})` },
  { key: "incomplete", label: `⏹ 未完成 (${incompleteTasks.value.length})` },
  { key: "idle", label: `📝 未执行 (${idleTasks.value.length})` },
]);

function tasksForTab(key) {
  if (key === "all") return tasks.value;
  if (key === "running") return runningTasks.value;
  if (key === "waiting") return waitingTasks.value;
  if (key === "completed") return completedTasks.value;
  if (key === "idle") return idleTasks.value;
  return incompleteTasks.value;
}

// ── Helpers ──
function ts() {
  return new Date().toLocaleTimeString("zh-CN", { hour12: false });
}
function taskAddLog(task, msg, level = "info") {
  if (!task.logs) task.logs = [];
  task.logs.push({ time: ts(), text: msg, level });
  if (task.logs.length > 500) task.logs = task.logs.slice(-300);
}
function deviceLabel(d) {
  const p = [];
  if (d.brand) p.push(d.brand);
  if (d.model) p.push(d.model);
  p.push(`[${d.serial}]`);
  return p.join(" ");
}
function findDevice(serial) {
  return (
    devices.value.find((d) => d.serial === serial) || { serial, model: serial }
  );
}

function formatTime(isoStr) {
  if (!isoStr) return "";
  try {
    const d = new Date(isoStr);
    const pad = (n) => String(n).padStart(2, "0");
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
  } catch (e) {
    console.error(e);
    return isoStr;
  }
}

// ── Navigate ──
function openTaskDetail(task) { router.push(`/runner/task/${task.id}`) }
function openReport(task) { router.push(`/reports/task/${encodeURIComponent(task.id)}`) }

// ── New task form ──
const newForm = ref({
  name: "",
  taskType: "ui_automation",
  deviceSerial: "",
  caseIds: [],
  loopCount: 3,
  intervalSeconds: 5,
  mode: "now",
  startAt: "",
  endAt: "",
});
function resetNewForm() {
  newForm.value = {
    name: "",
    taskType: "ui_automation",
    deviceSerial: devices.value[0]?.serial || "",
    caseIds: [],
    loopCount: 3,
    intervalSeconds: 5,
    mode: "now",
    startAt: "",
    endAt: "",
  };
}

const availableCases = ref([]);

// Watch task type to reload appropriate cases
watch(() => newForm.value.taskType, async (newType) => {
  if (newType === "api_testing") {
    await loadApiCases();
  } else if (newType === "web_automation") {
    await loadWebCases();
  } else {
    availableCases.value = cases.value.filter(c => c.case_type === "ui_automation" || !c.case_type);
  }
});

async function openNewTask() {
  resetNewForm();
  if (newForm.value.taskType === "api_testing") {
    await loadApiCases();
  } else if (newForm.value.taskType === "web_automation") {
    await loadWebCases();
  } else {
    await Promise.all([loadDevices(), loadCases()]);
  }
  if (newForm.value.taskType !== "api_testing" && !devices.value.length)
    ElMessage.warning("暂无在线设备，请先在设备管理中连接设备");
  if (!availableCases.value.length)
    ElMessage.warning("暂无可选用例，请先在用例管理中创建用例");
  showNewTask.value = true;
}

function normalizeCaseIds(ids) {
  return (ids || []).map((id) => String(id));
}

async function createAndStart() {
  if (!newForm.value.name.trim()) {
    ElMessage.warning("请输入任务名称");
    return;
  }
  if (newForm.value.taskType === "ui_automation" && !newForm.value.deviceSerial) {
    ElMessage.warning("Android UI 自动化任务需要选择执行设备");
    return;
  }
  if (!newForm.value.caseIds.length) {
    ElMessage.warning("请至少选择一个测试用例");
    return;
  }
  if (newForm.value.intervalSeconds < 5) {
    ElMessage.warning("轮间间隔最小为 5 秒，请重新设置");
    return;
  }
  const tid = generateTaskId(new Set(tasks.value.map((t) => t.id)));
  const task = {
    id: tid,
    name: newForm.value.name.trim(),
    taskType: newForm.value.taskType,
    mode: newForm.value.mode,
    startAt: newForm.value.startAt,
    endAt: newForm.value.endAt,
    deviceSerial: newForm.value.deviceSerial,
    caseIds: normalizeCaseIds(newForm.value.caseIds),
    loopCount: newForm.value.loopCount,
    intervalSeconds: newForm.value.intervalSeconds,
    running: false,
    runId: "",
    status: "idle",
    caseItems: [],
    stepStates: [],
    logs: [],
    overallPass: 0,
    overallFail: 0,
    createdAt: new Date().toISOString(),
    creator: getCurrentUsername(),
    currentCaseTitle: "",
    currentIteration: 0,
    outcome: "",
    round: 0,
  };
  tasks.value.push(task);
  await saveTaskToServer(task); // ① 初始保存（创建 TaskCard）
  resetNewForm();
  showNewTask.value = false;
  ElMessage.success(`任务「${task.name}」已创建`);
  await doStartTask(task);
  // doStartTask 替换了 tasks 中的对象，重新获取最新引用
  const updated = tasks.value.find((t) => t.id === task.id) || task;
  await saveTaskToServer(updated); // ② 再次保存（含步骤定义的 caseItems + 最新状态）
  activeTab.value = taskBucket(updated);
}

function initTaskProgress(task) {
  const idSet = new Set(normalizeCaseIds(task.caseIds));
  const sourceCases = (task.taskType === "api_testing" || task.taskType === "web_automation")
    ? availableCases.value : cases.value;
  task.caseItems = sourceCases
    .filter((c) => idSet.has(String(c.id)))
    .map((c, i) => {
      // 解析步骤定义（steps_data 为 API 已解析的数组，优先使用）
      let rawSteps = c.steps_data || [];
      if (!rawSteps.length && c.steps_json) {
        try {
          rawSteps = JSON.parse(c.steps_json);
        } catch (e) { console.error(e); }
      }
      const steps = rawSteps.map((s) => ({
        type: s.type || "",
        xpath: s.xpath || "",
        description: s.description || s.xpath || s.expected_text || "",
      }));
      return {
        id: c.id,
        title: c.title,
        index: i + 1,
        status: "pending",
        pass: 0,
        fail: 0,
        total: task.loopCount,
        rate: 0,
        steps,
      };
    });
  task.overallPass = 0;
  task.overallFail = 0;
  task.stepStates = [];
}

async function doStartTask(task) {
  const isApi = task.taskType === "api_testing";
  const isWeb = task.taskType === "web_automation";
  // 始终按任务类型重新加载用例列表，避免 availableCases 被 loadCases() 或
  // createAndStart() 中 resetNewForm() 触发的 watch 覆写成错误的用例类型
  if (isApi) {
    await loadApiCases();
  } else if (isWeb) {
    await loadWebCases();
  } else if (!cases.value.length) {
    await loadCases();
  }
  initTaskProgress(task);
  if (!task.caseItems.length) {
    taskAddLog(task, "❌ 未匹配到用例，请确认用例列表已加载且用例ID有效", "error");
    ElMessage.warning("用例数据未加载或ID不匹配，请刷新页面后重试");
    return;
  }
  const body = {
    case_ids: task.caseIds,
    loop_count: task.loopCount,
    interval_seconds: task.intervalSeconds,
    device_serial: task.deviceSerial,
    client_task_id: task.id,
    task_type: task.taskType || "ui_automation",
  };
  if (task.mode === "scheduled") {
    if (task.startAt) body.start_at = new Date(task.startAt).toISOString();
    if (task.endAt) body.end_at = new Date(task.endAt).toISOString();
  }
  try {
    const { data } = await startRun(body);
    if (data.status && data.runs?.[0]?.run_id) {
      const idx = tasks.value.findIndex((t) => t.id === task.id);
      if (idx !== -1) {
        const runId = data.runs[0].run_id;
        tasks.value[idx] = {
          ...tasks.value[idx],
          running: true,
          runId,
          status: "running",
        };
        // 先绑 WS 再写前台日志，确保能收到后台「设备 ID / 开始执行测试」推送
        bindListTaskWS(tasks.value[idx], runId);
        taskAddLog(tasks.value[idx], "🚀 任务已启动");
      }
    } else if (data.status && data.queued?.length) {
      // Device busy — task queued
      task.running = false;
      task.status = "queued";
      task.outcome = "";
      task.conclusion = "";
      taskAddLog(task, `⏳ 设备正忙，任务已加入队列等待执行`);
      ElMessage.info("设备正忙，任务已加入队列，设备空闲后自动执行");
      startQueuePolling();
    } else if (data.status) {
      task.running = false;
      taskAddLog(task, "❌ 设备不可用，任务未启动", "error");
      ElMessage.warning("设备不可用或未就绪，任务已保存，可在列表中重试");
    } else {
      task.running = false;
      taskAddLog(task, `❌ ${data.message}`, "error");
      ElMessage.error(data.message || "启动失败");
    }
  } catch (e) {
    task.running = false;
    const errMsg = e?.response?.data?.message || e.message || "未知错误";
    taskAddLog(task, `❌ ${errMsg}`, "error");
    ElMessage.error(`启动失败：${errMsg}`);
  }
  scheduleSave(task.id);
}

async function doCancelQueue(task) {
  try {
    await cancelQueue(task.id, task.deviceSerial);
  } catch (e) {
    if (e?.response?.status !== 404) {
      ElMessage.error("取消排队失败，请检查网络后重试"); return;
    }
  }
  task.running = false; task.runId = ""; task.status = "idle";
  task.caseItems = []; task.stepStates = []; task.overallPass = 0;
  task.overallFail = 0; task.failedSteps = []; task.logs = [];
  saveTaskToServer(task);
}

async function doStopTask(task) {
  try {
    await stopRun(task.runId);
    ElMessage.success("停止请求已发送");
  } catch (e) {
    ElMessage.error("停止请求失败，请检查网络连接");
  }
  task.running = false;
  task.status = "done";
  task.currentCaseTitle = "";
  task.currentIteration = 0;
  task.outcome = "stopped";
  closeTaskWebSocket(task.id);
  saveTaskToServer(task);
}

async function doRemoveTask(task) {
  if (task.running) {
    if (task.runId) {
      try {
        await stopRun(task.runId);
      } catch (e) {
        console.error("[removeTask] stop failed:", e);
      }
    }
    closeTaskWebSocket(task.id);
  }
  try {
    await deleteTask(task.id);
  } catch (e) {
    console.error("[removeTask] delete failed:", e);
    ElMessage.error("删除失败，请检查网络后重试");
    return;
  }
  tasks.value = tasks.value.filter((x) => x.id !== task.id);
  ElMessage.success("已删除");
}

function restartTask(task) {
  // Create a brand-new task card with new ID, copying config from original
  const round = (task.round || 0) + 1;
  const tid = generateTaskId(new Set(tasks.value.map((t) => t.id)));
  const newTask = {
    id: tid,
    name: task.name, // keep original name, not appended
    round, // round badge: 第2轮, 第3轮, ...
    mode: task.mode,
    deviceSerial: task.deviceSerial,
    caseIds: [...task.caseIds],
    loopCount: task.loopCount,
    intervalSeconds: task.intervalSeconds || 5,
    running: false,
    runId: "",
    caseItems: [],
    stepStates: [],
    logs: [],
    overallPass: 0,
    overallFail: 0,
    createdAt: new Date().toISOString(),
    creator: getCurrentUsername(),
    currentCaseTitle: "",
    currentIteration: 0,
    outcome: "",
  };
  tasks.value.push(newTask);
  saveTaskToServer(newTask);
  activeTab.value = taskBucket(newTask);
  ElMessage.success(`已创建新任务「${newTask.name}」第${round}轮`);
  doStartTask(newTask);
}

// ── WebSocket（handler 注册表：详情页进入时重绑，避免闭包陈旧） ──
function bindListTaskWS(task, runId) {
  connectTaskWebSocket(task.id, runId, (msg) => {
    const t = tasks.value.find((x) => x.id === task.id);
    if (!t) return;
    if (msg.type === "log") {
      taskAddLog(t, msg.message);
      scheduleSave(t.id);
      return;
    }
    applyWsMessage(t, msg, {
      addLog: (text, level) => taskAddLog(t, text, level),
      save: () => scheduleSave(t.id),
      onPollQueue: pollQueuedTasks,
      onRunFinished: () => closeTaskWebSocket(t.id),
    });
  });
}

// ── Queue polling: detect when a queued task gets picked up by the backend ──
const queuePollTimer = ref(null);
const POLL_INTERVAL = 1500; // 1.5 seconds, reduced from 3s for faster queue→running detection

function hasQueuedTasks() {
  return tasks.value.some((t) => isTaskQueued(t));
}

async function pollQueuedTasks() {
  if (!hasQueuedTasks()) {
    stopQueuePolling();
    return;
  }
  try {
    const { data } = await getActiveRuns();
    if (!data.status || !data.active?.length) return;
    for (const active of data.active) {
      if (!active.client_task_id) continue;
      const task = tasks.value.find((t) => t.id === active.client_task_id);
      if (task && !task.running) {
        // Our queued task is now running! Replace in array to force Vue reactivity
        const idx = tasks.value.findIndex(
          (t) => t.id === active.client_task_id,
        );
        if (idx !== -1) {
          const updated = {
            ...tasks.value[idx],
            running: true,
            runId: active.run_id,
            status: "running",
          };
          tasks.value.splice(idx, 1, updated);
          bindListTaskWS(updated, active.run_id);
          taskAddLog(updated, "🚀 排队任务已被后台调度，开始执行");
          scheduleSave(updated.id);
        }
      }
    }
  } catch (e) {
    /* polling is best-effort */
    console.error(e);
  }
}

function startQueuePolling() {
  if (queuePollTimer.value) return;
  pollQueuedTasks(); // 立即检查一次，不等间隔
  queuePollTimer.value = setInterval(pollQueuedTasks, POLL_INTERVAL);
}

function stopQueuePolling() {
  if (queuePollTimer.value) {
    clearInterval(queuePollTimer.value);
    queuePollTimer.value = null;
  }
}

// Also update the run_finished WS handler to re-check polling after a run ends
// (in case the finished run was on a device that had queued tasks)

onMounted(async () => {
  await Promise.all([loadTasks(), loadDevices(), loadCases()]);
  tasks.value.forEach((t) => {
    if (t.running && t.runId) bindListTaskWS(t, t.runId);
  });
  if (hasQueuedTasks()) startQueuePolling();
});

// keep-alive: pause timers when leaving page
onDeactivated(() => {
  stopQueuePolling();
  cleanupDebouncedSave();
});

// keep-alive: resume on return (WS stays connected, messages accumulate)
onActivated(() => {
  if (hasQueuedTasks()) startQueuePolling();
});

// Final cleanup when evicted from cache
onUnmounted(() => {
  stopQueuePolling();
  cleanupDebouncedSave();
  closeAllTaskWebSockets();
});

watch(
  tasks,
  () => {
    if (hasQueuedTasks()) startQueuePolling();
  },
  { deep: true },
);
async function loadCases() {
  try {
    const { data } = await listDefinitions();
    if (data.status) cases.value = data.definitions;
    availableCases.value = (data.definitions || []).filter(
      c => c.case_type === "ui_automation" || !c.case_type
    );
  } catch (e) { console.error(e); }
}
async function loadApiCases() {
  try {
    const { data } = await listApiDefinitions();
    if (data.status) {
      availableCases.value = (data.definitions || []).filter(
        c => c.case_type === "api_testing"
      );
      if (!availableCases.value.length) ElMessage.info('暂无 API 用例，请先在用例管理中创建');
    } else {
      ElMessage.error(data.message || '加载 API 用例失败');
    }
  } catch (e) {
    ElMessage.error('加载 API 用例失败，请检查网络连接');
    console.error(e);
  }
}
async function loadWebCases() {
  try {
    const { data } = await listWebDefinitions();
    if (data.status) {
      availableCases.value = (data.definitions || []).filter(
        c => c.case_type === "web_automation"
      );
      if (!availableCases.value.length) ElMessage.info('暂无 Web 用例，请先在用例管理中创建');
    } else {
      ElMessage.error(data.message || '加载 Web 用例失败');
    }
  } catch (e) {
    ElMessage.error('加载 Web 用例失败，请检查网络连接');
    console.error(e);
  }
}
async function loadDevices() {
  try {
    const { data } = await listDevices();
    if (data.status)
      devices.value = (data.devices || []).filter(
        (d) => d.status === "ONLINE" || d.status === "BUSY",
      );
  } catch (e) { console.error(e); }
}
</script>

<template>
  <div class="doc-page wb-shell runner-page">
    <WorkbenchHeader
      title="执行引擎"
      subtitle="创建并监控测试任务，查看实时执行进度与历史结果"
      icon="play-circle"
      icon-gradient="linear-gradient(135deg,#FFB5A7,#f87171)"
    />
    <div class="doc-body">
      <ErrorState v-if="error" :message="error" @retry="loadTasks" />
      <template v-else>
      <!-- 统计概览 -->
      <section class="doc-section runner-stats">
        <div class="doc-section__header">
          <h3 class="doc-section__title">统计概览 <span class="doc-tag">Overview</span></h3>
          <span class="doc-section__label">任务执行状态与进度总览</span>
        </div>
        <div class="kpi-row">
          <KpiCard :value="kpiStats.running" label="执行中" color="var(--c-ai)" shape="diamond" />
          <KpiCard :value="kpiStats.waiting" label="等待中" color="var(--c-dashboard)" shape="triangle" />
          <KpiCard :value="kpiStats.completed" label="已完成" color="var(--c-device)" shape="square" />
          <KpiCard :value="kpiStats.incomplete" label="失败/未完成" color="var(--c-runner)" shape="circle" />
        </div>
      </section>

      <!-- 任务列表 -->
      <section class="doc-section runner-tasks">
        <div class="runner-toolbar">
          <el-input class="search-input" v-model="searchQuery" placeholder="搜索任务名称 / ID / 设备..." clearable />
          <div class="runner-toolbar__right">
            <FilterTabs :tabs="filterAppTabs" v-model="activeTab" />
            <div class="view-toggle"><button class="view-btn" :class="{active:viewMode==='table'}" @click="viewMode='table'">📋 表格</button><button class="view-btn" :class="{active:viewMode==='cards'}" @click="viewMode='cards'">📷 卡片</button></div>
            <span class="filter-count">{{ filteredTasks.length }} 任务</span>
          </div>
          <el-button class="action-btn" type="primary" @click="openNewTask">＋ 新建任务</el-button>
        </div>
        <el-card v-if="viewMode==='table'" class="table-card" shadow="never"><div class="device-table-wrapper"><AppTable :columns="tableColumns" :data-source="filteredTasks" row-key="id" empty-text="暂无任务" @row-click="openTaskDetail">
          <template #cell-id="{record}"><span class="mono-text">{{ record.id }}</span></template>
          <template #cell-name="{record}"><span style="font-weight:700">{{ record.name||record.id }}</span></template>
          <template #cell-taskType="{record}"><span class="task-type-tag" :class="'task-type--' + (record.taskType||'ui_automation')">{{ {api_testing:'API',web_automation:'Web',ui_automation:'UI'}[record.taskType||'ui_automation']||'UI' }}</span></template>
          <template #cell-deviceSerial="{record}"><template v-if="record.taskType==='api_testing'||record.taskType==='web_automation'">无需设备</template><template v-else>📱 {{ record.deviceSerial||'—' }}</template></template>
          <template #cell-cases="{record}">{{ record.caseIds?.length||0 }}</template>
          <template #cell-progress="{record}"><div v-if="!isTaskQueued(record)" class="mini-progress"><div class="mini-progress-fill" :style="{width:taskProgress(record)+'%',background:taskStatusInfo(record).color}"></div></div><span style="font-size:var(--app-size-xs);margin-left:4px">{{ isTaskQueued(record)?'排队':taskProgress(record)+'%' }}</span></template>
          <template #cell-passRate="{record}">{{ isTaskQueued(record) || !taskCompletedCount(record) ? '—' : taskPassRate(record) + '%' }}</template>
          <template #cell-status="{record}"><span class="status-badge" :style="{background:taskStatusInfo(record).color}">{{ taskStatusInfo(record).icon }} {{ taskStatusInfo(record).label }}</span></template>
          <template #cell-time="{record}">{{ formatTime(record.createdAt) }}</template>
          <template #cell-actions="{record}"><div class="table-actions">
            <template v-if="deriveTaskStatus(record)==='running'"><ConfirmButton size="small" type="danger" plain message="停止后任务将中断" @confirm="doStopTask(record)">⏹ 停止</ConfirmButton></template>
            <template v-else-if="isTaskQueued(record)"><ConfirmButton size="small" type="warning" plain message="确认取消排队？" @confirm="doCancelQueue(record)">取消排队</ConfirmButton></template>
            <template v-else><el-button size="small" v-if="record.caseIds?.length" @click.stop="doStartTask(record)">▶ 执行</el-button><el-button size="small" v-if="record.outcome" @click.stop="restartTask(record)">↻ 重跑</el-button><el-button size="small" v-if="record.outcome" @click.stop="openReport(record)">📊 报告</el-button><ConfirmButton size="small" type="danger" plain message="确认删除该任务？" @confirm="doRemoveTask(record)">🗑 删除</ConfirmButton></template>
          </div></template>
          <template #empty><EmptyState icon="▶️" text="暂无任务" hint="点击「新建任务」创建第一个测试任务" /></template>
        </AppTable></div></el-card>
        <div v-if="viewMode==='cards'" class="card-grid-grouped">
          <div v-for="g in [{k:'running',l:'🟣 执行中'},{k:'waiting',l:'🟡 等待中'},{k:'completed',l:'🟢 已完成'},{k:'incomplete',l:'🔴 失败/未完成'}]" :key="g.k">
            <template v-if="groupedTasks[g.k].length">
              <div class="card-group-title">{{ g.l }} <span class="card-group-count">{{ groupedTasks[g.k].length }}</span></div>
              <div class="card-grid"><div v-for="task in groupedTasks[g.k]" :key="task.id" class="task-card" role="button" tabindex="0" @click="openTaskDetail(task)" @keydown.enter.prevent="openTaskDetail(task)" @keydown.space.prevent="openTaskDetail(task)" :style="{'--card-accent': taskStatusInfo(task).color}">
                <div class="task-card-header">
                  <span class="task-card-id">{{ task.id }}</span>
                  <span class="task-type-tag" :class="'task-type--' + (task.taskType||'ui_automation')">{{ {api_testing:'API 测试',web_automation:'Web 自动化',ui_automation:'UI 自动化'}[task.taskType||'ui_automation']||'UI 自动化' }}</span>
                </div>
                <div class="task-card-name">{{ task.name||task.id }}</div>
                <div class="task-card-meta">
                  <span class="meta-item" v-if="task.taskType==='api_testing'||task.taskType==='web_automation'">🌐 无需设备</span>
                  <span class="meta-item" v-else>📱 {{ task.deviceSerial||'—' }}</span>
                  <span class="meta-item">📋 {{ task.caseIds?.length||0 }} 用例</span>
                  <span class="meta-item">🔁 {{ task.loopCount||1 }} 轮</span>
                </div>
                <div v-if="!isTaskQueued(task)" class="task-card-progress">
                  <div class="mini-progress"><div class="mini-progress-fill" :style="{width:taskProgress(task)+'%',background:taskStatusInfo(task).color}"></div></div>
                </div>
                <div class="task-card-stats">
                  <span class="task-card-status" :style="{color:taskStatusInfo(task).color}">{{ taskStatusInfo(task).icon }} {{ taskStatusInfo(task).label }}</span>
                  <span v-if="isTaskQueued(task)">排队等待</span>
                  <span v-else class="task-card-count">{{ taskCompletedCount(task) }}/{{ taskTotalCount(task) }} · {{ taskProgress(task) }}%</span>
                  <span class="task-card-time">{{ formatTime(task.createdAt) }}</span>
                </div>
                <div class="task-card-actions" @click.stop>
                  <template v-if="deriveTaskStatus(task)==='running'">
                    <ConfirmButton size="small" type="danger" plain message="停止后任务将中断" @confirm="doStopTask(task)">⏹ 停止</ConfirmButton>
                  </template>
                  <template v-else-if="isTaskQueued(task)">
                    <ConfirmButton size="small" type="warning" plain message="确认取消排队？" @confirm="doCancelQueue(task)">🚫 取消排队</ConfirmButton>
                  </template>
                  <template v-else>
                    <el-button size="small" v-if="task.caseIds?.length" type="primary" @click.stop="doStartTask(task)">▶ 执行</el-button>
                    <el-button size="small" v-if="task.outcome" @click.stop="restartTask(task)">↻ 重跑</el-button>
                    <el-button size="small" v-if="task.outcome" @click.stop="openReport(task)">📊 报告</el-button>
                    <ConfirmButton size="small" type="danger" plain message="确认删除该任务？" @confirm="doRemoveTask(task)">🗑 删除</ConfirmButton>
                  </template>
                </div>
              </div></div>
            </template>
          </div>
        </div>
      </section>
    </template>
    </div>

    <NewTaskDialog
      v-model="showNewTask"
      :new-form="newForm"
      :devices="devices"
      :available-cases="availableCases"
      :device-label="deviceLabel"
      @create="createAndStart"
    />
  </div>
</template>

<style scoped>
.runner-page { height:100%;display:flex;flex-direction:column;overflow:hidden }
.runner-page :deep(.doc-body) { flex:1;min-height:0;overflow:hidden }
.runner-stats { flex-shrink:0;display:flex;flex-direction:column;gap:14px;padding-top:4px }
.runner-tasks { flex:1;min-height:0;display:flex;flex-direction:column;overflow:hidden;gap:10px }

/* ── Section 标题 ── */
.doc-section__header { flex-shrink:0;margin-bottom:0 }
.doc-section__title {
  font-family:var(--app-font-display);font-size:var(--app-size-lg);font-weight:700;color:var(--ink);
  display:inline-block;position:relative;margin-bottom:4px
}
.doc-section__title::after {
  content:'';position:absolute;bottom:-1px;left:0;right:0;height:3px;
  background:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 80 3'%3E%3Cpath d='M0,1.5 Q20,0 40,2 Q60,3 80,1.5' stroke='%232d2d2d' stroke-width='2' fill='none'/%3E%3C/svg%3E") repeat-x;
  background-size:40px 3px
}
.doc-section__title .doc-tag {
  font-size:var(--app-size-xs);padding:1px 8px;border-radius:4px 8px 4px 8px;
  background:var(--app-bg-card);color:var(--app-ink-muted);border:1.5px solid #e8ecf1;font-weight:700;margin-left:8px
}
.doc-section__label { color:var(--app-ink-muted);font-size:var(--app-size-xs);margin-top:2px }

/* ── 工具栏 ── */
.runner-toolbar { display:flex;align-items:center;gap:10px;flex-wrap:wrap;flex-shrink:0 }
.runner-toolbar__right { display:flex;align-items:center;gap:8px;margin-left:auto;flex-wrap:wrap }
.search-input { width:240px;flex-shrink:0 }
.filter-count { font-size:var(--app-size-xs);color:var(--app-ink-muted);font-weight:600;white-space:nowrap }
.action-btn { flex-shrink:0 }

/* ── 视图切换 — 模块色桃粉 ── */
.view-toggle { display:flex;gap:0;border:2px solid var(--c-runner);border-radius:4px 8px 4px 8px;overflow:hidden }
.view-btn { padding:5px 12px;font-size:var(--app-size-xs);font-weight:700;background:var(--app-bg-card);color:var(--app-ink-muted);border:none;border-right:1.5px solid var(--c-runner);cursor:pointer;font-family:inherit;transition:all 0.12s }
.view-btn:last-child { border-right:none }
.view-btn.active { background:var(--c-runner);color:var(--app-bg-card) }
.view-btn:hover:not(.active) { color:var(--c-runner) }

/* ── KPI 卡片 ── */
.kpi-row { display:grid;grid-template-columns:repeat(4,1fr);gap:18px;flex-shrink:0 }
.kpi-row > :nth-child(1) { transform:rotate(-0.8deg) }
.kpi-row > :nth-child(2) { transform:rotate(0.5deg) }
.kpi-row > :nth-child(3) { transform:rotate(-0.4deg) }
.kpi-row > :nth-child(4) { transform:rotate(0.6deg) }
.kpi-row > :hover { transform:rotate(0deg) scale(1.03)!important;z-index:5 }
@media(max-width:700px){.kpi-row{grid-template-columns:repeat(2,1fr)}}

/* ── 表格卡片 — 模块色边框 ── */
.table-card { flex:1;min-height:0;display:flex;flex-direction:column;overflow:hidden;border-radius:6px 10px 6px 10px;border:2.5px solid var(--c-runner);box-shadow:2px 3px 0 rgba(255,181,167,0.15);background:var(--app-bg-card) }
.table-card :deep(.el-card__body) { flex:1;min-height:0;display:flex;flex-direction:column;overflow:hidden;padding:0 }
.mono-text { font-family:var(--app-font-mono);font-size:var(--app-size-xs);font-weight:600 }
.status-badge { font-size:var(--app-size-xs);font-weight:700;padding:2px 7px;border-radius:3px 6px 3px 6px;border:1.5px solid var(--ink);color:var(--app-bg-card);display:inline-block }
.mini-progress { height:6px;background:var(--app-border-lighter);border-radius:3px;overflow:hidden;border:1px solid var(--ink);width:80px;display:inline-block;vertical-align:middle }
.mini-progress-fill { height:100%;border-radius:2px;transition:width 0.3s }
.device-table-wrapper { flex:1;min-height:0;overflow-y:auto;overflow-x:auto }
.device-table-wrapper :deep(.el-table th) { background:var(--app-bg-subtle);color:var(--ink);font-weight:700;font-size:var(--app-size-xs);text-transform:uppercase;letter-spacing:0.04em;border-bottom:2.5px solid var(--ink) }
.device-table-wrapper :deep(.el-table td) { border-bottom:1px solid #e8e4d8 }
/* 表格行 hover — 模块色淡底 */
.device-table-wrapper :deep(.el-table tbody tr) { cursor:pointer;transition:background var(--app-duration-fast) var(--app-ease) }
.device-table-wrapper :deep(.el-table tbody tr:hover) { background:rgba(255,181,167,0.08) }

/* 卡片 hover — 上浮 */
.task-card { cursor:pointer;transition:all var(--app-duration) var(--app-ease) }
.task-card:hover { background:rgba(255,181,167,0.06);transform:translateY(-2px);box-shadow:var(--app-shadow-md) }
.table-actions { display:grid;grid-template-columns:1fr 1fr;gap:4px }
.table-actions > :only-child { grid-column:1/-1 }
.table-actions .el-button,.table-actions .wb-btn { width:100%;justify-content:center }
.card-grid-grouped { flex:1;min-height:0;overflow-y:auto;display:flex;flex-direction:column;gap:16px }
.card-group-title { font-family:var(--app-font-display);font-size:var(--app-size-lg);font-weight:700;display:flex;align-items:center;gap:8px;margin-bottom:10px }
.card-group-count { font-family:var(--app-font-mono);font-size:var(--app-size-xs);color:var(--ink);opacity:0.4;background:var(--app-bg-subtle);padding:2px 8px;border-radius:3px 6px 3px 6px;border:1.5px solid #e8e4d8 }
.card-grid { display:grid;grid-template-columns:repeat(3,1fr);gap:14px }
@media(max-width:900px){.card-grid{grid-template-columns:repeat(2,1fr)}}
/* ── Task Card — Doodle Craft Polaroid ── */
.task-card {
  background: radial-gradient(circle, rgba(212,205,192,0.12) 0.8px, transparent 0.8px);
  background-size: 12px 12px;
  background-color: #fffef9;
  border: 2.5px solid var(--ink);
  border-top: 5px solid var(--card-accent, var(--c-dashboard));
  border-radius: 6px 10px 6px 10px;
  padding: 10px 12px 32px 12px;
  box-shadow: 2px 3px 0 rgba(0,0,0,0.06);
  position: relative; cursor: pointer;
  transition: all .2s cubic-bezier(.4,0,.2,1);
}
.task-card::before {
  content: ''; position: absolute; top: 5px; left: 50%; transform: translateX(-50%);
  width: 10px; height: 10px; border-radius: 50%;
  background: radial-gradient(circle, var(--app-pushpin-light) 30%, var(--app-pushpin-dark) 100%);
  box-shadow: 0 1px 1px rgba(0,0,0,.08); z-index: 2;
}
.task-card:nth-child(3n+1){transform:rotate(-0.5deg)}.task-card:nth-child(3n+2){transform:rotate(0.4deg)}.task-card:nth-child(3n+3){transform:rotate(-0.2deg)}
.task-card:hover { transform:rotate(0)scale(1.03)!important;z-index:5;box-shadow:4px 6px 0 rgba(0,0,0,0.1);border-color:var(--c-dashboard) }

.task-card-header { display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;gap:6px }
.task-card-id { font-family:var(--app-font-mono);font-size:var(--app-size-xs);font-weight:700;color:var(--app-ink-muted);background:rgba(0,0,0,0.05);padding:3px 10px;border-radius:5px;letter-spacing:0.02em }
.task-type-tag{display:inline-block;padding:3px 9px;border-radius:5px;font-size:var(--app-size-xs);font-weight:800;color:var(--app-bg-card);letter-spacing:0.03em}
.task-type--api_testing{background:linear-gradient(135deg,#889df0,#6c7ce0)}
.task-type--web_automation{background:linear-gradient(135deg,#6fba2c,#52a01e)}
.task-type--ui_automation{background:linear-gradient(135deg,#f7cd67,#e8b830);color:var(--ink)}

.task-card-name { font-family:var(--app-font-display);font-size:var(--app-size-md);font-weight:800;margin-bottom:8px;color:var(--ink);letter-spacing:-0.01em;line-height:1.3 }

.task-card-meta { display:flex;flex-wrap:wrap;gap:8px;margin-bottom:8px }
.meta-item { font-size:var(--app-size-xs);font-weight:700;color:var(--app-ink-muted);background:rgba(0,0,0,0.03);padding:2px 8px;border-radius:4px }

.task-card-progress { margin-bottom:8px }
.mini-progress { height:6px;background:rgba(0,0,0,0.06);border-radius:4px;overflow:hidden }
.mini-progress-fill { height:100%;border-radius:4px;transition:width .4s cubic-bezier(.4,0,.2,1) }

.task-card-stats { display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;gap:8px }
.task-card-status { font-size:var(--app-size-sm);font-weight:800;flex-shrink:0 }
.task-card-count { font-size:var(--app-size-sm);font-weight:700;color:var(--ink) }
.task-card-time { font-size:var(--app-size-xs);color:var(--app-ink-muted);font-weight:600;opacity:0.5 }

.task-card-actions { display:flex;gap:5px;justify-content:center;flex-wrap:wrap;margin-top:8px;padding-top:8px;border-top:1.5px dashed rgba(0,0,0,0.1) }
.task-card-actions :deep(.el-button) { font-size:var(--app-size-xs);padding:5px 12px;font-weight:700;border-radius:4px 8px 4px 8px;border:2px solid var(--ink);background:var(--app-bg-card);color:var(--ink);transition:all .15s }
.task-card-actions :deep(.el-button:hover) { background:var(--app-highlight);transform:translateY(-1px) }
.task-card-actions :deep(.el-button--primary) { background:var(--c-case);color:var(--app-bg-card);border-color:var(--ink) }
.new-task-form :deep(.el-form-item) { margin-bottom:14px }.new-task-form :deep(.el-form-item__label) { font-size:var(--app-size-xs);font-weight:700;opacity:0.5;text-transform:uppercase }.field-hint{font-size:var(--app-size-xs);color:var(--c-runner);margin-top:4px;font-weight:600}
/* 全覆盖 dialog 内部组件 */
:deep(.el-dialog__header){padding:14px 18px;border-bottom:3px solid var(--ink);background:var(--app-bg-card);border-radius:6px 10px 0 0}:deep(.el-dialog__title){font-family:var(--app-font-display);font-size:var(--app-size-lg);font-weight:700}:deep(.el-dialog__body){padding:18px}:deep(.el-dialog__footer){padding:14px 18px;border-top:2px solid var(--ink);background:var(--app-bg-card)}
:deep(.el-select__wrapper){border-radius:4px 8px 4px 8px!important;border:2px solid var(--ink)!important;box-shadow:none!important}:deep(.el-select__wrapper:hover){border-color:var(--c-dashboard)!important}:deep(.el-select__wrapper.is-disabled){background:var(--app-bg-subtle)!important;opacity:0.5}
:deep(.el-input-number){border-radius:4px 8px 4px 8px;border:2px solid var(--ink)}:deep(.el-input-number .el-input__wrapper){border:none!important;box-shadow:none!important}:deep(.el-input-number__decrease),:deep(.el-input-number__increase){border-color:var(--ink)!important;background:var(--app-bg-card)!important;color:var(--ink)!important}
:deep(.el-radio__label){font-size:var(--app-size-xs);font-weight:700}:deep(.el-radio__inner){border-color:var(--ink)!important}:deep(.el-radio.is-checked .el-radio__inner){background:var(--ink)!important;border-color:var(--ink)!important}
:deep(.el-date-picker__wrapper){border-radius:4px 8px 4px 8px!important;border:2px solid var(--ink)!important}
:deep(.el-dialog__headerbtn){top:16px;right:16px}:deep(.el-dialog__close){color:var(--ink)!important;font-size:var(--app-size-lg)!important}
</style>
