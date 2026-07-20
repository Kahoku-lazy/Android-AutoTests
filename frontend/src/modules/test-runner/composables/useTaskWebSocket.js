/**
 * WebSocket 连接 + 消息分发（handler 注册表模式，解决列表页→详情页跨页闭包陈旧问题）
 */
import { wsUrl } from "@/shared/ws-url.js";
import { getToken } from "@/shared/api-client.js";

const WS_MAP_KEY = "_task_ws_map";
const HANDLER_KEY = "_task_ws_handlers";

export function getWsMap() {
  return window[WS_MAP_KEY] || {};
}

export function setWsMap(map) {
  window[WS_MAP_KEY] = map;
}

function registerHandler(taskId, handler) {
  if (!window[HANDLER_KEY]) window[HANDLER_KEY] = {};
  window[HANDLER_KEY][taskId] = handler;
}

export function unregisterHandler(taskId) {
  if (window[HANDLER_KEY]) delete window[HANDLER_KEY][taskId];
}

/**
 * 应用 WS 消息到 task 对象
 * @param {object} task - 当前任务（可变引用）
 * @param {object} msg - WS 消息
 * @param {object} hooks - { addLog, save, onPollQueue, onCaseStarted, onRunFinished, onDeviceError }
 */
export function applyWsMessage(task, msg, hooks = {}) {
  if (!task) return;
  const ci = task.caseItems?.find(
    (c) => String(c.id) === String(msg.case_id),
  );
  const {
    addLog = () => {},
    save = () => {},
    onPollQueue = () => {},
    onCaseStarted = () => {},
    onRunFinished = () => {},
    onDeviceError = () => {},
  } = hooks;

  switch (msg.type) {
    case "log":
      addLog(msg.message);
      break;
    case "heartbeat":
      // TREP v1.0: 更新心跳时间戳，前端据此检测连接存活
      task._lastHeartbeat = Date.now();
      task._connectionHealthy = true;
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
      onCaseStarted(ci);
      save();
      break;
    case "step_started":
      if (!task.stepStates) task.stepStates = [];
      if (
        msg.step_index === 0 &&
        !task._wsJustReconnected &&
        hooks.reconnectAware
      ) {
        const s0 = task.stepStates.find((s) => s.index === 0);
        if (s0 && s0.result !== "running") task.stepStates = [];
      }
      task.stepStates = [
        ...task.stepStates.filter((s) => s.index !== msg.step_index),
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
      if (!task.stepStates) task.stepStates = [];
      task.stepStates = [
        ...task.stepStates.filter((s) => s.index !== msg.step_index),
        {
          index: msg.step_index,
          total: msg.total_steps,
          type: msg.step_type,
          desc: msg.description,
          result: msg.result,
        },
      ].sort((a, b) => a.index - b.index);
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
      if (
        hooks.reconnectAware &&
        task._wsJustReconnected &&
        ci &&
        !ci.pass &&
        !ci.fail &&
        msg.iteration > 1
      ) {
        const prevTotal = msg.iteration - 1;
        ci.pass = prevTotal;
        task.overallPass = (task.overallPass || 0) + prevTotal;
      }
      if (hooks.reconnectAware) task._wsJustReconnected = false;

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
      task.currentIteration = msg.iteration;
      save();
      break;
    case "case_finished":
      if (ci) {
        ci.status = "done";
        ci.pass = parseInt(msg.pass);
        ci.fail = parseInt(msg.fail);
        ci.rate = 100;
      }
      save();
      break;
    case "run_finished":
      task.running = false;
      task.status = "done";
      if (task.outcome !== "stopped") task.outcome = "completed";
      task.caseItems?.forEach((c) => {
        if (c.status !== "done") c.status = "done";
      });
      task.currentCaseTitle = "";
      task.currentIteration = 0;
      if (!task.conclusion) {
        const pf = task.overallFail || 0;
        task.conclusion =
          pf === 0
            ? "✅ 测试通过：所有用例全部执行成功"
            : `❌ 测试不通过：${pf} 个用例执行失败`;
      }
      addLog(
        `🏁 完成 ✅${task.overallPass || 0} ❌${task.overallFail || 0}`,
        "success",
      );
      onRunFinished(task);
      save();
      onPollQueue();
      break;
    case "device_error":
      task.running = false;
      task.status = "done";
      task.outcome = "error";
      addLog(`💥 ${msg.error}`, "error");
      onDeviceError(task);
      save();
      onPollQueue();
      break;
    default:
      break;
  }
}

/**
 * 连接 WS；若同 runId 已连接则仅更新 handler（详情页进入时重绑）
 */
export function connectTaskWebSocket(taskId, runId, createHandler) {
  registerHandler(taskId, createHandler);

  const wm = getWsMap();
  const existing = wm[taskId];
  if (
    existing &&
    existing.readyState <= WebSocket.OPEN &&
    existing._runId === runId
  ) {
    return existing;
  }

  if (existing) {
    try {
      existing.close();
    } catch (_) {}
  }

  const url = `${wsUrl("/ws/test-run/" + runId)}?token=${encodeURIComponent(getToken())}`;
  const ws = new WebSocket(url);
  ws._runId = runId;

  ws.onmessage = (e) => {
    const handler = window[HANDLER_KEY]?.[taskId];
    if (!handler) return;
    try {
      const msg = JSON.parse(e.data);
      // TREP v1.0: seq gap 检测
      if (msg.seq !== undefined) {
        const prev = ws._lastSeq || 0;
        if (prev > 0 && msg.seq > prev + 1) {
          console.warn(
            `[WS] seq gap: ${prev} → ${msg.seq} (${msg.seq - prev - 1} lost) for ${taskId}`,
          );
          ws._seqGapDetected = true;
        }
        ws._lastSeq = msg.seq;
      }
      handler(msg);
    } catch (_) {}
  };

  wm[taskId] = ws;
  setWsMap(wm);
  return ws;
}

export function closeTaskWebSocket(taskId) {
  const wm = getWsMap();
  if (wm[taskId]) {
    try {
      wm[taskId].close();
    } catch (_) {}
    delete wm[taskId];
    setWsMap(wm);
  }
  unregisterHandler(taskId);
}
