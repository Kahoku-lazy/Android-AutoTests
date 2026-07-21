<script setup>
import { ref, computed, watch, onMounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import client, { getToken } from "@/shared/api-client.js";
import ConfirmButton from "@/shared/components/patterns/ConfirmButton.vue";
// Card/AppTabs → AppCard/AppTabs
import AppCard from "@/shared/components/AppCard.vue";
import AppTabs from "@/shared/components/AppTabs.vue";
import WorkbenchHeader from "@/shared/components/WorkbenchHeader.vue";
import {
  generateTaskId,
  readTaskCounter,
  writeTaskCounter,
  isTaskQueued,
  taskBucket,
  taskCardClass,
  taskStatusInfo,
  taskCompletedCount,
  taskTotalCount,
  taskPassRate,
  taskCardRateBg,
  taskProgress,
  buildTaskSavePayload,
} from "./composables/taskUtils.js";
import {
  connectTaskWebSocket,
  closeTaskWebSocket,
  applyWsMessage,
} from "./composables/useTaskWebSocket.js";
import { startRun, listDefinitions, listDevices } from "./api.js";
import { listApiDefinitions } from "@/modules/case-manager/api/apiTesting.js";
import { listWebDefinitions } from "@/modules/case-manager/api/webAutomation.js";

const router = useRouter();

const cases = ref([]);
const devices = ref([]);
const showNewTask = ref(false);

const activeTab = ref("running");
const tasks = ref([]);

// ── JWT decode for creator ──
function getCurrentUsername() {
  try {
    const token = getToken();
    if (!token) return "未知";
    const payload = JSON.parse(atob(token.split(".")[1]));
    return payload.username || payload.sub || "未知";
  } catch (_) {
    return "未知";
  }
}


// ── Server persistence ──
async function saveTaskToServer(task) {
  try {
    await client.post("/runner/tasks/save", buildTaskSavePayload(task));
  } catch (e) {
    console.error("[saveTaskToServer] failed:", e);
    ElMessage.error("保存任务失败，请检查网络");
  }
}

// 脏任务 ID 集合 — 仅保存有变更的任务，避免 WS 风暴时全表写入
const _dirtyTaskIds = new Set();
let _saveTimer = null;
function scheduleSave(taskId) {
  if (taskId) _dirtyTaskIds.add(taskId);
  if (_saveTimer) return;
  _saveTimer = setTimeout(() => {
    _saveTimer = null;
    for (const id of _dirtyTaskIds) {
      const t = tasks.value.find((x) => x.id === id);
      if (t) saveTaskToServer(t);
    }
    _dirtyTaskIds.clear();
  }, 1000);
}

async function loadTasks() {
  try {
    const { data } = await client.get("/runner/tasks");
    if (data.ok && data.tasks) {
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
  } catch (_) {
    /* 加载失败保持空列表 */
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
const filterAppTabs = computed(() => [
  { key: "all", label: `📋 全部 (${tasks.value.length})` },
  { key: "running", label: `⚡ 执行中 (${runningTasks.value.length})` },
  { key: "waiting", label: `⏳ 等待中 (${waitingTasks.value.length})` },
  { key: "completed", label: `✅ 已完成 (${completedTasks.value.length})` },
  { key: "incomplete", label: `⏹ 未完成 (${incompleteTasks.value.length})` },
]);

function tasksForTab(key) {
  if (key === "all") return tasks.value;
  if (key === "running") return runningTasks.value;
  if (key === "waiting") return waitingTasks.value;
  if (key === "completed") return completedTasks.value;
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
  } catch (_) {
    return isoStr;
  }
}

// ── Navigate to detail page ──
function openTaskDetail(task) {
  router.push(`/runner/task/${task.id}`);
}

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
  const sourceCases = task.taskType === "api_testing" ? availableCases.value : cases.value;
  task.caseItems = sourceCases
    .filter((c) => idSet.has(String(c.id)))
    .map((c, i) => {
      // 解析步骤定义（steps_data 为 API 已解析的数组，优先使用）
      let rawSteps = c.steps_data || [];
      if (!rawSteps.length && c.steps_json) {
        try {
          rawSteps = JSON.parse(c.steps_json);
        } catch (_) {}
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
  if (!isApi && !cases.value.length) await loadCases();
  if (isApi && !availableCases.value.length) await loadApiCases();
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
    if (data.ok && data.runs?.[0]?.run_id) {
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
    } else if (data.ok && data.queued?.length) {
      // Device busy — task queued
      task.running = false;
      task.status = "queued";
      task.outcome = "";
      task.conclusion = "";
      taskAddLog(task, `⏳ 设备正忙，任务已加入队列等待执行`);
      ElMessage.info("设备正忙，任务已加入队列，设备空闲后自动执行");
      startQueuePolling();
    } else if (data.ok) {
      task.running = false;
      taskAddLog(task, "❌ 设备不可用，任务未启动", "error");
      ElMessage.warning("设备不可用或未就绪，任务已保存，可在列表中重试");
    } else {
      task.running = false;
      taskAddLog(task, `❌ ${data.error}`, "error");
      ElMessage.error(data.error || "启动失败");
    }
  } catch (e) {
    task.running = false;
    const errMsg = e?.response?.data?.error || e.message || "未知错误";
    taskAddLog(task, `❌ ${errMsg}`, "error");
    ElMessage.error(`启动失败：${errMsg}`);
  }
  scheduleSave(task.id);
}

async function doCancelQueue(task) {
  try {
    await client.post("/runner/queue/cancel", {
      client_task_id: task.id, device_serial: task.deviceSerial,
    });
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
    await client.post(`/runner/run/${task.runId}/stop`);
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
        await client.post(`/runner/run/${task.runId}/stop`);
      } catch (e) {
        console.error("[removeTask] stop failed:", e);
      }
    }
    closeTaskWebSocket(task.id);
  }
  try {
    await client.delete(`/runner/tasks/${task.id}`);
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
    const { data } = await client.get("/runner/active");
    if (!data.ok || !data.active?.length) return;
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
  } catch (_) {
    /* polling is best-effort */
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
    if (data.ok) cases.value = data.definitions;
    availableCases.value = (data.definitions || []).filter(
      c => c.case_type === "ui_automation" || !c.case_type
    );
  } catch (_) {}
}
async function loadApiCases() {
  try {
    const { data } = await listApiDefinitions();
    if (data.ok) {
      availableCases.value = (data.definitions || []).filter(
        c => c.case_type === "api_testing"
      );
    }
  } catch (_) {}
}
async function loadWebCases() {
  try {
    const { data } = await listWebDefinitions();
    if (data.ok) {
      availableCases.value = (data.definitions || []).filter(
        c => c.case_type === "web_automation"
      );
    }
  } catch (_) {}
}
async function loadDevices() {
  try {
    const { data } = await listDevices();
    if (data.ok)
      devices.value = (data.devices || []).filter(
        (d) => d.status === "ONLINE" || d.status === "BUSY",
      );
  } catch (_) {}
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
      <section class="doc-section runner-section">
        <div class="doc-section__header">
          <h3 class="doc-section__title">
            任务列表<span class="doc-tag">Tasks</span>
          </h3>
          <el-button class="wb-btn" type="primary" @click="openNewTask">+ 新建任务</el-button>
        </div>

        <!-- AppTabs panel: cards render inside animal-tabs content slots -->
        <div class="tabs-panel">
          <AppTabs
            class="runner-tabs"
            :items="filterAppTabs"
            v-model="activeTab"
            :leaf-animation="true"
            :shadow="true"
          >
            <template v-for="tab in filterAppTabs" #[tab.key] :key="tab.key">
              <div v-if="tasksForTab(tab.key).length" class="card-grid">
                <div
                  v-for="(task, idx) in tasksForTab(tab.key)"
                  :key="task.id"
                  class="task-card"
                  :class="taskCardClass(task)"
                  :style="taskCardRateBg(task)"
                  @click="openTaskDetail(task)"
                >
                  <!-- Row 1: task name + round badge + status badge -->
                  <div class="tc-row1">
                    <span class="tc-name">
                      {{ task.name || task.id }}
                      <span v-if="task.round" class="tc-round-badge"
                        >第{{ task.round }}轮</span
                      >
                    </span>
                    <span
                      class="tc-status-badge"
                      :style="{ background: taskStatusInfo(task).color }"
                    >
                      {{ taskStatusInfo(task).icon }}
                      {{ taskStatusInfo(task).label }}
                      <span
                        v-if="taskStatusInfo(task).rateTag"
                        class="tc-rate-tag"
                        :style="{ background: taskStatusInfo(task).rateColor }"
                      >{{ taskStatusInfo(task).rateTag }}</span>
                    </span>
                  </div>
                  <!-- Row 1b: device + task ID -->
                  <div class="tc-row1b">
                    <span class="tc-device">📱 {{ task.deviceSerial }}</span>
                    <span class="tc-id-badge">{{ task.id }}</span>
                  </div>

                  <!-- Row 2: meta -->
                  <div class="tc-row2">
                    <span>📋 {{ task.caseIds?.length || 0 }} 用例</span>
                    <span v-if="task.loopCount"
                      >🔁 {{ task.loopCount }} 轮</span
                    >
                    <span class="tc-creator-tag"
                      >👤 {{ task.creator || "未知" }}</span
                    >
                    <span class="tc-time"
                      >🕐 {{ formatTime(task.createdAt) }}</span
                    >
                  </div>

                  <!-- Row 3: current case + progress -->
                  <div
                    v-if="task.running && task.currentCaseTitle"
                    class="tc-row3"
                  >
                    <span class="tc-current-label">▶ 正在执行：</span>
                    <span class="tc-current-name">{{
                      task.currentCaseTitle
                    }}</span>
                  </div>
                  <div class="tc-row3">
                    <span class="tc-progress-text">
                      <template v-if="isTaskQueued(task)">
                        排队等待执行（{{ task.caseIds?.length || 0 }} 用例 ·
                        {{ task.loopCount || 1 }} 轮）
                      </template>
                      <template v-else>
                        已执行 {{ taskCompletedCount(task) }}/{{
                          taskTotalCount(task)
                        }}
                        次
                        <template v-if="task.running && task.currentIteration"
                          >（第 {{ task.currentIteration }} 轮循环）</template
                        >
                        <template v-if="task.outcome">
                          · ✅ {{ task.overallPass || 0 }} ❌ {{ task.overallFail || 0 }}
                          <span v-if="taskPassRate(task) < 90" class="tc-rate-warn">
                            ({{ taskPassRate(task) }}%)
                          </span>
                        </template>
                      </template>
                    </span>
                  </div>

                  <!-- Progress bar: hide for pure waiting state -->
                  <el-progress
                    v-if="!isTaskQueued(task)"
                    :percentage="taskProgress(task)"
                    :stroke-width="6"
                    :show-text="taskProgress(task) > 0"
                    :color="taskStatusInfo(task).color"
                  />

                  <!-- Row 4: actions -->
                  <div class="tc-actions" @click.stop>
                    <template v-if="task.running">
                      <ConfirmButton size="small" type="primary" danger
                        message="确定停止该任务？" title="停止任务" confirm-text="停止"
                        @confirm="doStopTask(task)">⏹ 停止</ConfirmButton>
                    </template>
                    <template v-else-if="isTaskQueued(task)">
                      <ConfirmButton size="small" type="primary"
                        message="确定取消该排队任务？任务将回到未执行列表" title="取消排队" confirm-text="取消排队"
                        @confirm="doCancelQueue(task)">⏸ 取消排队</ConfirmButton>
                    </template>
                    <template
                      v-else-if="
                        task.outcome &&
                        [
                          'completed',
                          'stopped',
                          'interrupted',
                          'error',
                        ].includes(task.outcome)
                      "
                    >
                      <el-button
                        size="small"
                        type="primary"
                        @click="restartTask(task)"
                        >↻ 重新执行</el-button>
                      <el-button
                        size="small"
                        type="info"
                        @click="router.push(`/reports/task/${encodeURIComponent(task.id)}`)"
                        >📊 查看报告</el-button>
                    </template>
                    <template v-else-if="!task.caseIds?.length">
                      <el-button size="small" disabled>⚠ 无用例</el-button>
                    </template>
                    <template v-else>
                      <el-button
                        size="small"
                        type="primary"
                        @click="doStartTask(task)"
                        >▶ 执行</el-button>
                    </template>
                    <ConfirmButton size="small" type="primary" danger plain
                      :message="`删除任务「${task.name || task.id}」？`" title="确认删除" confirm-text="删除"
                      @confirm="doRemoveTask(task)">🗑 删除</ConfirmButton>
                  </div>
                </div>
              </div>

              <div v-else class="empty-hint">
                当前分类暂无任务{{
                  tab.key !== "all" ? "，可切换到「全部」查看" : ""
                }}
              </div>
            </template>
          </AppTabs>
        </div>
      </section>
    </div>

    <!-- New task dialog (Element Plus) -->
    <el-dialog
      v-model="showNewTask"
      title="新建测试任务"
      width="520px"
      :close-on-click-modal="false"
      @close="showNewTask = false"
    >
      <div class="new-task-form">
        <el-form label-width="88px" label-position="right">
          <el-form-item label="任务名称" required>
            <el-input
              v-model="newForm.name"
              placeholder="如：稳定性测试"
              maxlength="30"
              clearable
            />
          </el-form-item>
          <el-form-item label="任务类型" required>
            <el-select v-model="newForm.taskType" style="width: 100%">
              <el-option label="📱 Android UI 自动化测试" value="ui_automation" />
              <el-option label="🌍 Web 自动化测试" value="web_automation" />
              <el-option label="🌐 API 测试" value="api_testing" />
            </el-select>
          </el-form-item>
          <el-form-item v-if="newForm.taskType === 'ui_automation'" label="设备" required>
            <el-select
              v-model="newForm.deviceSerial"
              placeholder="选择在线设备"
              style="width: 100%"
              :disabled="!devices.length"
            >
              <el-option
                v-for="d in devices"
                :key="d.serial"
                :label="deviceLabel(d)"
                :value="d.serial"
              />
            </el-select>
            <p v-if="!devices.length" class="field-hint">
              暂无在线设备，请先在「设备管理」中连接
            </p>
          </el-form-item>
          <el-form-item label="用例" required>
            <el-select
              v-model="newForm.caseIds"
              multiple
              collapse-tags
              collapse-tags-tooltip
              :placeholder="newForm.taskType === 'api_testing' ? '选择 API 用例（可多选）' : '选择 UI 用例（可多选）'"
              style="width: 100%"
              :disabled="!availableCases.length"
            >
              <el-option
                v-for="c in availableCases"
                :key="c.id"
                :label="c.title"
                :value="c.id"
              />
            </el-select>
            <p v-if="!availableCases.length" class="field-hint">
              {{ newForm.taskType === 'api_testing' ? '暂无 API 用例，请先在「测试用例 > API 接口用例」中创建' : '暂无 UI 用例，请先在「测试用例 > UI 自动化用例」中创建' }}
            </p>
          </el-form-item>
          <el-form-item label="循环次数">
            <el-input-number
              v-model="newForm.loopCount"
              :min="1"
              :max="10000"
              style="width: 160px"
            />
          </el-form-item>
          <el-form-item label="轮间间隔">
            <el-input-number
              v-model="newForm.intervalSeconds"
              :min="5"
              :max="300"
              style="width: 160px"
            />
            <span style="margin-left: 8px; font-size: 12px; color: var(--app-text-secondary)"
              >秒（最小 5s）</span
            >
          </el-form-item>
          <el-form-item label="执行方式">
            <el-radio-group v-model="newForm.mode">
              <el-radio value="now">立即执行</el-radio>
              <el-radio value="scheduled">定时执行</el-radio>
            </el-radio-group>
          </el-form-item>
          <template v-if="newForm.mode === 'scheduled'">
            <el-form-item label="开始时间">
              <el-date-picker
                v-model="newForm.startAt"
                type="datetime"
                placeholder="开始时间"
                style="width: 100%"
              />
            </el-form-item>
            <el-form-item label="结束时间">
              <el-date-picker
                v-model="newForm.endAt"
                type="datetime"
                placeholder="结束时间（可选）"
                style="width: 100%"
              />
            </el-form-item>
          </template>
        </el-form>
      </div>
      <template #footer>
        <el-button class="wb-btn" @click="showNewTask = false">取消</el-button>
        <el-button
          class="wb-btn"
          type="primary"
          :disabled="!newForm.caseIds.length || !newForm.deviceSerial"
          @click="createAndStart"
        >创建并执行</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.runner-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.runner-page :deep(.doc-body) {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}
.runner-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding: 20px 24px 24px;
}
.runner-section .doc-section__header {
  flex-shrink: 0;
}

/* AppTabs panel — unified container for tabs + content */
.tabs-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  margin-top: 12px;
  border: 1px solid var(--app-glass-border);
  border-radius: var(--ac-radius, 16px);
  background: var(--app-glass-card);
  overflow: hidden;
  box-shadow: var(--app-shadow-sm);
  backdrop-filter: blur(var(--app-glass-blur));
  -webkit-backdrop-filter: blur(var(--app-glass-blur));
}
.tabs-panel :deep(.el-tabs) {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding: 8px 16px 0;
}
.runner-tabs :deep(.el-tabs__content) {
  flex: 1;
  min-height: 0;
  overflow-x: hidden;
  overflow-y: auto;
  display: block;
  padding-top: 12px;
}
.runner-tabs :deep(.el-tabs__inner) {
  min-height: min-content;
}

/* AppCard grid */
.card-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
  padding: 12px 16px 16px;
  align-content: start;
}

/* Task card */
.task-card {
  cursor: pointer;
  border-radius: var(--ac-radius, 16px);
  border: 1px solid var(--app-glass-border);
  border-left-width: 4px;
  padding: 16px 18px 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  transition: all 0.2s;
  background: rgba(255,255,255,0.48);
  box-shadow: var(--app-shadow-sm);
}
.task-card--running {
  background: linear-gradient(135deg, #e8edff 0%, #f3f6ff 100%);
  border-color: rgba(136, 157, 240, 0.28);
  border-left-color: #889df0;
}
.task-card--waiting {
  background: linear-gradient(135deg, #fff8e0 0%, #fffdf5 100%);
  border-color: rgba(247, 205, 103, 0.35);
  border-left-color: #f7cd67;
}
.task-card--completed {
  background: linear-gradient(135deg, #e8f5e0 0%, #f3faf0 100%);
  border-color: rgba(111, 186, 44, 0.3);
  border-left-color: #89CFF0;
}
.task-card--incomplete {
  background: linear-gradient(135deg, #ffe8ec 0%, #fff5f7 100%);
  border-color: rgba(232, 95, 95, 0.28);
  border-left-color: #e85f5f;
}
.task-card--idle {
  background: rgba(255,255,255,0.48);
  border-color: rgba(162,210,255,0.30);
  border-left-color: var(--app-text-muted);
}
.task-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--app-shadow-md);
}

/* Row 1: device + status */
.tc-row1 {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.tc-row1b {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 2px;
}
.tc-name {
  font-size: 15px;
  font-weight: 700;
  color: var(--app-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 200px;
}
.tc-round-badge {
  display: inline-block;
  font-size: 10px;
  font-weight: 600;
  color: #fff;
  background: #889df0;
  padding: 1px 8px;
  border-radius: 10px;
  margin-left: 6px;
  vertical-align: middle;
}
.tc-id-badge {
  display: inline-block;
  font-size: 10px;
  font-weight: 700;
  color: var(--app-text-secondary);
  background: rgba(162,210,255,0.18);
  padding: 2px 10px;
  border-radius: 10px;
  font-family: "Cascadia Code", Consolas, monospace;
  letter-spacing: 0.3px;
}
.tc-rate-warn {
  font-size: 11px;
  font-weight: 700;
  color: #e85f5f;
}
.tc-device {
  font-size: 12px;
  font-weight: 600;
  color: var(--app-text-secondary);
  font-family: "Cascadia Code", Consolas, monospace;
}
.tc-status-badge {
  font-size: 11px;
  font-weight: 700;
  color: #fff;
  padding: 2px 6px 2px 10px;
  border-radius: 12px;
  white-space: nowrap;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.tc-rate-tag {
  font-size: 9px;
  font-weight: 800;
  color: #fff;
  padding: 1px 7px;
  border-radius: 8px;
  letter-spacing: 0.2px;
}

/* Row 2: meta */
.tc-row2 {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px 12px;
  font-size: 12px;
  color: var(--app-text-secondary);
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
  color: var(--app-text-secondary);
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
  color: var(--app-text);
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.tc-progress-text {
  color: var(--app-text-secondary);
  font-weight: 600;
}

/* Actions */
.tc-actions {
  display: flex;
  gap: 6px;
  padding-top: 2px;
  border-top: 1px solid rgba(162,210,255,0.18);
}

.empty-hint {
  color: var(--app-text-secondary);
  padding: 60px 0;
  text-align: center;
  font-size: 15px;
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.new-task-form {
  padding: 4px 0 8px;
}
.new-task-form :deep(.el-form-item) {
  margin-bottom: 16px;
}
.field-hint {
  margin: 6px 0 0;
  font-size: 12px;
  color: #e6a23c;
  line-height: 1.4;
}

/* Responsive: single column on narrow screens */
@media (max-width: 900px) {
  .card-grid {
    grid-template-columns: 1fr;
  }
}
</style>
