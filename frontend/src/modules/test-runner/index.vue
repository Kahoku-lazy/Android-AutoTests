<script setup>
import { ref, computed, watch, onMounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import client from "@/shared/api-client.js";
import { wsUrl } from "@/shared/ws-url.js";
import { Button as AnimalButton, Card, Tabs, Modal } from "animal-island-vue";
import PageHeader from "@/shared/components/PageHeader.vue";

const router = useRouter();

const cases = ref([]);
const devices = ref([]);
const showNewTask = ref(false);
const activeTab = ref("all");

const WS_MAP_KEY = "_task_ws_map";
const COUNTER_KEY = "_task_id_counter";
const tasks = ref([]);

// ── Sequential ID generator: ID-001, ID-002, ... (collision-safe) ──
function _readCounter() {
  try {
    return parseInt(localStorage.getItem(COUNTER_KEY)) || 0;
  } catch (_) {
    return 0;
  }
}
function _writeCounter(n) {
  localStorage.setItem(COUNTER_KEY, String(n));
}
function generateTaskId() {
  const existing = new Set(tasks.value.map((t) => t.id));
  let n = Math.max(_readCounter(), 0);
  let tid;
  do {
    n++;
    tid = `ID-${String(n).padStart(3, "0")}`;
  } while (existing.has(tid));
  _writeCounter(n);
  return tid;
}

// ── JWT decode for creator ──
function getCurrentUsername() {
  try {
    const token = localStorage.getItem("access_token");
    if (!token) return "未知";
    const payload = JSON.parse(atob(token.split(".")[1]));
    return payload.username || payload.sub || "未知";
  } catch (_) {
    return "未知";
  }
}

// ── Card style ──
const CARD_BG = "rgb(247,243,223)";

// ── Server persistence (replaces localStorage) ──
function getWsMap() {
  return window[WS_MAP_KEY] || {};
}
function setWsMap(m) {
  window[WS_MAP_KEY] = m;
}

async function saveTaskToServer(task) {
  try {
    const body = {
      id: task.id,
      name: task.name,
      mode: task.mode,
      deviceSerial: task.deviceSerial,
      caseIds: task.caseIds,
      loopCount: task.loopCount,
      intervalSeconds: task.intervalSeconds,
      running: task.running,
      runId: task.runId || "",
      caseItems: task.caseItems,
      stepStates: task.stepStates,
      overallPass: task.overallPass,
      overallFail: task.overallFail,
      logs: (task.logs || []).slice(-200),
      createdAt: task.createdAt,
      creator: task.creator,
      currentCaseTitle: task.currentCaseTitle,
      currentIteration: task.currentIteration,
      failedSteps: (task.failedSteps || []).slice(-200),
      conclusion: task.conclusion || "",
      bugTicket: task.bugTicket || "",
      outcome: task.outcome || "",
      round: task.round || 0,
      status: task.status || deriveTaskStatus(task),
    };
    await client.post("/runner/tasks/save", body);
  } catch (e) {
    console.error("[saveTaskToServer] failed:", e);
    ElMessage.error("保存任务失败，请检查网络");
  }
}

function deriveTaskStatus(task) {
  if (task.running) return "running";
  if (task.status === "queued") return "queued";
  // Terminal outcomes take priority — a done task should never be re-classified
  if (task.outcome === "completed") return "done";
  if (
    task.outcome &&
    ["stopped", "interrupted", "error"].includes(task.outcome)
  )
    return "done";
  // 后端 status 是排队的唯一真相（第79行已覆盖）；不再用 caseItems 猜测，
  // 否则遗留 pending caseItems 的 idle 任务会被误判为"排队中"（取消排队按钮还会失败）
  return "idle";
}

function isTaskQueued(task) {
  return deriveTaskStatus(task) === "queued";
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
      }));
      // Sync counter
      let maxSeq = 0;
      for (const t of tasks.value) {
        const m = String(t.id).match(/^ID-(\d+)$/);
        if (m) maxSeq = Math.max(maxSeq, parseInt(m[1]));
      }
      if (maxSeq >= _readCounter()) _writeCounter(maxSeq);
    }
  } catch (_) {
    /* 加载失败保持空列表 */
  }
}

// Throttled save: persists the full task list at most once per second.
// Uses non-resetting timer to prevent WebSocket message storms from
// perpetually deferring the save (starvation). Once the timer fires,
// the next call starts a fresh cycle.
let _saveTimer = null;
function scheduleSave() {
  if (_saveTimer) return; // 已有定时器，不重置（防止 WS 消息饿死）
  _saveTimer = setTimeout(() => {
    _saveTimer = null;
    for (const t of tasks.value) saveTaskToServer(t);
  }, 1000);
}

// ── Filter ──
const runningTasks = computed(() => tasks.value.filter((t) => t.running));
const waitingTasks = computed(() => tasks.value.filter((t) => isTaskQueued(t)));
const completedTasks = computed(() =>
  tasks.value.filter((t) => !t.running && t.outcome === "completed"),
);
const incompleteTasks = computed(() =>
  tasks.value.filter((t) => taskBucket(t) === "incomplete"),
);
const notExecutedTasks = computed(() =>
  tasks.value.filter((t) => taskBucket(t) === "notExecuted"),
);

const filterTabs = computed(() => [
  { key: "all", label: `📋 全部 (${tasks.value.length})` },
  { key: "running", label: `⚡ 执行中 (${runningTasks.value.length})` },
  { key: "waiting", label: `⏳ 等待中 (${waitingTasks.value.length})` },
  { key: "completed", label: `✅ 已完成 (${completedTasks.value.length})` },
  { key: "incomplete", label: `⏹ 未完成 (${incompleteTasks.value.length})` },
  { key: "notExecuted", label: `📝 未执行 (${notExecutedTasks.value.length})` },
]);

function tasksForTab(key) {
  if (key === "all") return tasks.value;
  if (key === "running") return runningTasks.value;
  if (key === "waiting") return waitingTasks.value;
  if (key === "completed") return completedTasks.value;
  if (key === "incomplete") return incompleteTasks.value;
  return notExecutedTasks.value;
}

function taskBucket(task) {
  if (task.running) return "running";
  if (isTaskQueued(task)) return "waiting";
  if (task.outcome === "completed") return "completed";
  // Terminal states (stopped/interrupted/error) → incomplete regardless of caseItems
  if (
    task.outcome &&
    ["stopped", "interrupted", "error"].includes(task.outcome)
  )
    return "incomplete";
  if (task.caseItems?.length) return "incomplete";
  return "notExecuted";
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

function taskCompletedCount(task) {
  const ci = task.caseItems;
  if (!ci?.length) return 0;
  return ci.reduce((s, c) => s + c.pass + c.fail, 0);
}
function taskTotalCount(task) {
  const ci = task.caseItems;
  if (ci?.length) return ci.reduce((s, c) => s + c.total, 0);
  return (task.caseIds?.length || 0) * (task.loopCount || 1);
}
function taskProgress(task) {
  const total = taskTotalCount(task);
  if (!total) return 0;
  return Math.round((taskCompletedCount(task) / total) * 100);
}

function taskStatusInfo(task) {
  if (task.running) return { label: "执行中", color: "#889df0", icon: "⚡" };
  if (isTaskQueued(task))
    return { label: "等待中", color: "#f7cd67", icon: "⏳" };
  if (task.outcome === "stopped")
    return { label: "未完成", color: "#e85f5f", icon: "⏹" };
  if (task.outcome === "interrupted")
    return { label: "运行中断", color: "#f7a8c4", icon: "⚠️" };
  if (task.outcome === "error")
    return { label: "异常终止", color: "#e85f5f", icon: "💥" };
  if (task.outcome === "completed")
    return { label: "已完成", color: "#6fba2c", icon: "✅" };
  return { label: "未执行", color: "#8b7355", icon: "📝" };
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
    deviceSerial: devices.value[0]?.serial || "",
    caseIds: [],
    loopCount: 3,
    intervalSeconds: 5,
    mode: "now",
    startAt: "",
    endAt: "",
  };
}

async function openNewTask() {
  resetNewForm();
  await Promise.all([loadDevices(), loadCases()]);
  if (!devices.value.length)
    ElMessage.warning("暂无在线设备，请先在设备管理中连接设备");
  if (!cases.value.length)
    ElMessage.warning("暂无可用用例，请先在测试用例中创建用例");
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
  if (!newForm.value.deviceSerial) {
    ElMessage.warning("请选择执行设备");
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
  const tid = generateTaskId();
  const task = {
    id: tid,
    name: newForm.value.name.trim(),
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
  router.push(`/runner/task/${task.id}`); // ③ 跳转详情页展示卡片布局
}

function initTaskProgress(task) {
  const idSet = new Set(normalizeCaseIds(task.caseIds));
  task.caseItems = cases.value
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
  if (!cases.value.length) await loadCases();
  initTaskProgress(task);
  if (!task.caseItems.length) {
    taskAddLog(
      task,
      "❌ 未匹配到用例，请确认用例列表已加载且用例ID有效",
      "error",
    );
    ElMessage.warning("用例数据未加载或ID不匹配，请刷新页面后重试");
    return;
  }
  const body = {
    case_ids: task.caseIds,
    loop_count: task.loopCount,
    interval_seconds: task.intervalSeconds,
    device_serial: task.deviceSerial,
    client_task_id: task.id,
  };
  if (task.mode === "scheduled") {
    if (task.startAt) body.start_at = new Date(task.startAt).toISOString();
    if (task.endAt) body.end_at = new Date(task.endAt).toISOString();
  }
  try {
    const { data } = await client.post("/runner/run", body);
    if (data.ok && data.runs?.[0]?.run_id) {
      const idx = tasks.value.findIndex((t) => t.id === task.id);
      if (idx !== -1) {
        tasks.value[idx] = {
          ...tasks.value[idx],
          running: true,
          runId: data.runs[0].run_id,
          status: "running",
        };
        connectTaskWS(tasks.value[idx], data.runs[0].run_id);
        taskAddLog(tasks.value[idx], "🚀 任务已启动");
      }
    } else if (data.ok && data.queued?.length) {
      // Device busy — task queued
      task.running = false;
      task.status = "queued";
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
  scheduleSave();
}

async function stopTask(task) {
  if (!task.runId) {
    // Queued task — cancel queue entry, reset to idle (keep task config)
    try {
      await ElMessageBox.confirm(
        "确定取消该排队任务？任务将回到未执行列表",
        "取消排队",
        {
          confirmButtonText: "取消排队",
          cancelButtonText: "返回",
          type: "warning",
        },
      );
    } catch (_) {
      return;
    }
    try {
      await client.post("/runner/queue/cancel", {
        client_task_id: task.id,
        device_serial: task.deviceSerial,
      });
    } catch (_) {
      /* backend may return 404 if already started */
    }
    // Reset to idle: keep task config, clear execution state
    task.running = false;
    task.runId = "";
    task.status = "idle";
    task.caseItems = [];
    task.stepStates = [];
    task.overallPass = 0;
    task.overallFail = 0;
    task.logs = [];
    task.currentCaseTitle = "";
    task.currentIteration = 0;
    task.failedSteps = [];
    task.outcome = "";
    saveTaskToServer(task);
    ElMessage.success("已取消排队，任务回到未执行列表");
    return;
  }
  try {
    await ElMessageBox.confirm("确定停止该任务？", "停止任务", {
      confirmButtonText: "停止",
      cancelButtonText: "取消",
      type: "warning",
    });
  } catch (_) {
    return;
  }
  try {
    await client.post(`/runner/run/${task.runId}/stop`);
    ElMessage.success("停止请求已发送");
  } catch (e) {
    ElMessage.error("停止请求失败，请检查网络连接");
  }
  task.running = false;
  task.currentCaseTitle = "";
  task.currentIteration = 0;
  task.outcome = "stopped";
  const wm = getWsMap();
  if (wm[task.id]) {
    try {
      wm[task.id].close();
    } catch (_) {}
    delete wm[task.id];
    setWsMap(wm);
  }
  saveTaskToServer(task); // 立即持久化，不依赖防抖
}

async function removeTask(task) {
  try {
    await ElMessageBox.confirm(
      `删除任务「${task.name || task.id}」？`,
      "确认删除",
      { confirmButtonText: "删除", cancelButtonText: "取消", type: "warning" },
    );
  } catch (_) {
    return;
  }
  if (task.running) {
    if (task.runId) {
      try {
        await client.post(`/runner/run/${task.runId}/stop`);
      } catch (_) {}
    }
    const wm = getWsMap();
    if (wm[task.id]) {
      try {
        wm[task.id].close();
      } catch (_) {}
      delete wm[task.id];
      setWsMap(wm);
    }
  }
  try {
    await client.delete(`/runner/tasks/${task.id}`);
  } catch (_) {}
  tasks.value = tasks.value.filter((x) => x.id !== task.id);
  ElMessage.success("已删除");
}

function restartTask(task) {
  // Create a brand-new task card with new ID, copying config from original
  const round = (task.round || 0) + 1;
  const tid = generateTaskId();
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

// ── WebSocket ──
function connectTaskWS(task, runId) {
  const wm = getWsMap();
  if (wm[task.id]) {
    try {
      wm[task.id].close();
    } catch (_) {}
  }
  const url = `${wsUrl("/ws/test-run/" + runId)}?token=${encodeURIComponent(localStorage.getItem("access_token") || "")}`;
  const ws = new WebSocket(url);
  wm[task.id] = ws;
  setWsMap(wm);
  ws.onmessage = (e) => {
    try {
      const msg = JSON.parse(e.data);
      const ci = task.caseItems?.find((c) => c.id === msg.case_id);
      switch (msg.type) {
        case "log":
          taskAddLog(task, msg.message);
          break;
        case "case_started":
          if (ci) {
            ci.status = "running";
            ci.pass = 0;
            ci.fail = 0;
          }
          task.stepStates = [];
          task.currentCaseTitle = ci?.title || msg.case_id || "";
          task.currentIteration = 1;
          break;
        case "step_started":
          // 标记当前步骤为执行中（蓝色脉冲），移除同步骤旧状态
          task.stepStates = [
            ...(task.stepStates || []).filter(
              (s) => s.index !== msg.step_index,
            ),
            {
              index: msg.step_index,
              total: msg.total_steps,
              type: msg.step_type,
              desc: msg.description,
              result: "running",
            },
          ].sort((a, b) => a.index - b.index);
          task.currentIteration = msg.iteration;
          break;
        case "step_result":
          task.stepStates = [
            ...(task.stepStates || []).filter(
              (s) => s.index !== msg.step_index,
            ),
            {
              index: msg.step_index,
              total: msg.total_steps,
              type: msg.step_type,
              desc: msg.description,
              result: msg.result,
            },
          ].sort((a, b) => a.index - b.index);
          // Track failed steps for report
          if (msg.result !== "pass" && msg.result !== "stopped") {
            if (!task.failedSteps) task.failedSteps = [];
            const dup = task.failedSteps.find(
              (f) =>
                f.caseTitle === ci?.title &&
                f.iteration === (task.currentIteration || 1) &&
                f.stepIndex === msg.step_index,
            );
            if (!dup) {
              task.failedSteps.push({
                caseTitle: ci?.title || msg.case_id || "",
                iteration: task.currentIteration || 1,
                stepIndex: msg.step_index,
                stepType: msg.step_type,
                description: msg.description || "",
                result: msg.result,
              });
            }
          }
          break;
        case "iteration_result":
          if (msg.result === "pass") {
            if (ci) ci.pass++;
            task.overallPass = (task.overallPass || 0) + 1;
          } else {
            if (ci) ci.fail++;
            task.overallFail = (task.overallFail || 0) + 1;
          }
          if (ci)
            ci.rate = ci.total
              ? Math.round(((ci.pass + ci.fail) / ci.total) * 100)
              : 0;
          task.currentIteration = msg.iteration; // 使用 WS 消息中的真实轮次
          scheduleSave(); // persist progress on each iteration result
          break;
        case "case_finished":
          if (ci) {
            ci.status = "done";
            ci.pass = parseInt(msg.pass);
            ci.fail = parseInt(msg.fail);
            ci.rate = 100;
          }
          scheduleSave(); // persist on case completion
          break;
        case "run_finished":
          task.running = false;
          task.status = "done";
          // Only set completed if user didn't already stop the task
          if (task.outcome !== "stopped") task.outcome = "completed";
          delete wm[task.id];
          setWsMap(wm);
          task.caseItems?.forEach((c) => {
            if (c.status !== "done") c.status = "done";
          });
          task.currentCaseTitle = "";
          task.currentIteration = 0;
          // Auto-generate conclusion if not manually set
          if (!task.conclusion) {
            const pf = task.overallFail || 0;
            task.conclusion =
              pf === 0
                ? "✅ 测试通过：所有用例全部执行成功"
                : `❌ 测试不通过：${pf} 个用例执行失败`;
          }
          taskAddLog(
            task,
            `🏁 完成 ✅${task.overallPass || 0} ❌${task.overallFail || 0}`,
            "success",
          );
          pollQueuedTasks();
          scheduleSave();
          break;
        case "device_error":
          task.running = false;
          task.status = "done";
          task.outcome = "error";
          taskAddLog(task, `💥 ${msg.error}`, "error");
          pollQueuedTasks();
          break;
      }
    } catch (_) {}
  };
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
          connectTaskWS(updated, active.run_id);
          taskAddLog(updated, "🚀 排队任务已被后台调度，开始执行");
          scheduleSave();
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
    if (t.running && t.runId) connectTaskWS(t, t.runId);
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
    const { data } = await client.get("/cases/definitions");
    if (data.ok) cases.value = data.definitions;
  } catch (_) {}
}
async function loadDevices() {
  try {
    const { data } = await client.get("/devices");
    if (data.ok)
      devices.value = (data.devices || []).filter(
        (d) => d.status === "ONLINE" || d.status === "BUSY",
      );
  } catch (_) {}
}
</script>

<template>
  <div class="doc-page runner-page">
    <PageHeader
      title="执行引擎 Test Runner"
      subtitle="创建并监控测试任务，查看实时执行进度与历史结果"
      color="app-yellow"
    />
    <div class="doc-body">
      <section class="doc-section runner-section">
        <div class="doc-section__header">
          <h3 class="doc-section__title">
            任务列表<span class="doc-tag">Tasks</span>
          </h3>
          <AnimalButton type="primary" @click="openNewTask"
            >+ 新建任务</AnimalButton
          >
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
                  :style="{ background: CARD_BG }"
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
                    </span>
                  </div>
                  <!-- Row 1b: device + task ID -->
                  <div class="tc-row1b">
                    <span class="tc-device">📱 {{ task.deviceSerial }}</span>
                    <span class="tc-id">{{ task.id }}</span>
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
                      已执行 {{ taskCompletedCount(task) }}/{{
                        taskTotalCount(task)
                      }}
                      次
                      <template v-if="task.running && task.currentIteration"
                        >（第 {{ task.currentIteration }} 轮循环）</template
                      >
                      <template v-if="task.outcome === 'completed'">
                        · ✅ 全部通过</template
                      >
                      <template v-if="task.outcome === 'stopped'">
                        · ⏹ 已中止</template
                      >
                    </span>
                  </div>

                  <!-- Progress bar: always show -->
                  <el-progress
                    :percentage="taskProgress(task)"
                    :stroke-width="6"
                    :show-text="taskProgress(task) > 0"
                    :color="taskStatusInfo(task).color"
                  />

                  <!-- Row 4: actions -->
                  <div class="tc-actions" @click.stop>
                    <template v-if="task.running">
                      <el-button
                        size="small"
                        type="danger"
                        @click="stopTask(task)"
                        >⏹ 停止</el-button
                      >
                    </template>
                    <template v-else-if="isTaskQueued(task)">
                      <el-button
                        size="small"
                        type="warning"
                        @click="stopTask(task)"
                        >⏸ 取消排队</el-button
                      >
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
                        >↻ 重新执行</el-button
                      >
                    </template>
                    <template v-else-if="!task.caseIds?.length">
                      <el-button size="small" disabled>⚠ 无用例</el-button>
                    </template>
                    <template v-else>
                      <el-button
                        size="small"
                        type="primary"
                        @click="doStartTask(task)"
                        >▶ 执行</el-button
                      >
                    </template>
                    <el-button
                      size="small"
                      type="danger"
                      plain
                      @click="removeTask(task)"
                      >🗑 删除</el-button
                    >
                  </div>
                </div>
              </div>

              <div v-else class="empty-hint">
                当前分类暂无任务{{
                  tab.key !== "all" ? "，可切换到「全部」查看" : ""
                }}
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
          <el-form-item label="任务名称" required>
            <el-input
              v-model="newForm.name"
              placeholder="如：稳定性测试"
              maxlength="30"
              clearable
            />
          </el-form-item>
          <el-form-item label="设备" required>
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
              placeholder="选择用例（可多选）"
              style="width: 100%"
              :disabled="!cases.length"
            >
              <el-option
                v-for="c in cases"
                :key="c.id"
                :label="c.title"
                :value="c.id"
              />
            </el-select>
            <p v-if="!cases.length" class="field-hint">
              暂无可用用例，请先在「测试用例」中创建
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
            <span style="margin-left: 8px; font-size: 12px; color: #9f927d"
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
        <AnimalButton @click="showNewTask = false">取消</AnimalButton>
        <AnimalButton
          type="primary"
          :disabled="!newForm.caseIds.length || !newForm.deviceSerial"
          @click="createAndStart"
          >创建并执行</AnimalButton
        >
      </template>
    </Modal>
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
  overflow-x: hidden;
  overflow-y: auto;
  display: block;
  padding-top: 12px;
}
.runner-tabs :deep(.animal-tabs__inner) {
  min-height: min-content;
}

/* Card grid */
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
.tc-row1b {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 2px;
}
.tc-name {
  font-size: 15px;
  font-weight: 700;
  color: #4a3a28;
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
.tc-id {
  font-size: 11px;
  color: #988b7a;
  font-family: "Cascadia Code", Consolas, monospace;
  opacity: 0.7;
}
.tc-device {
  font-size: 12px;
  font-weight: 600;
  color: #6b5e4e;
  font-family: "Cascadia Code", Consolas, monospace;
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
  color: #4a3a28;
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

.empty-hint {
  color: #988b7a;
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
