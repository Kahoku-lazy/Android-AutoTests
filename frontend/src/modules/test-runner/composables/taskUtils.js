/** 执行引擎 — 任务状态/进度/持久化共享逻辑（index + TaskDetail 共用） */

const COUNTER_KEY = "_task_id_counter";

export function readTaskCounter() {
  try {
    return parseInt(localStorage.getItem(COUNTER_KEY)) || 0;
  } catch (_) {
    return 0;
  }
}

export function writeTaskCounter(n) {
  localStorage.setItem(COUNTER_KEY, String(n));
}

/** 生成 ID-001 格式任务 ID，existingIds 为已占用 ID 集合 */
export function generateTaskId(existingIds = new Set()) {
  let n = Math.max(readTaskCounter(), 0);
  let tid;
  do {
    n++;
    tid = `ID-${String(n).padStart(3, "0")}`;
  } while (existingIds.has(tid));
  writeTaskCounter(n);
  return tid;
}

export function deriveTaskStatus(task) {
  if (task.running) return "running";
  // 历史数据漂移：DB status=queued 但 outcome 已终态 → 视为已完成
  if (
    task.status === "queued" &&
    task.outcome &&
    ["completed", "stopped", "interrupted", "error"].includes(task.outcome)
  ) {
    return "done";
  }
  if (task.status === "queued") return "queued";
  if (task.outcome === "completed") return "done";
  if (
    task.outcome &&
    ["stopped", "interrupted", "error"].includes(task.outcome)
  )
    return "done";
  return "idle";
}

export function isTaskQueued(task) {
  return deriveTaskStatus(task) === "queued";
}

export function taskBucket(task) {
  if (task.running) return "running";
  if (isTaskQueued(task)) return "waiting";
  // 仅成功跑完全部用例归入「已完成」；停止/中断/异常归入「未完成」
  if (task.outcome === "completed") return "completed";
  return "incomplete";
}

export function taskCardClass(task) {
  const map = {
    running: "task-card--running",
    waiting: "task-card--waiting",
    completed: "task-card--completed",
    incomplete: "task-card--incomplete",
    notExecuted: "task-card--idle",
  };
  return map[taskBucket(task)] || "task-card--idle";
}

export function taskStatusInfo(task) {
  if (task.running) return { label: "执行中", color: "#889df0", icon: "⚡" };
  if (isTaskQueued(task))
    return { label: "等待中", color: "#f7cd67", icon: "⏳" };
  if (task.outcome === "completed")
    return { label: "已完成", color: "#6fba2c", icon: "✅" };
  if (task.outcome === "stopped")
    return { label: "已停止", color: "#f7a8c4", icon: "⏹" };
  if (task.outcome === "interrupted")
    return { label: "运行中断", color: "#f7a8c4", icon: "⚠️" };
  if (task.outcome === "error")
    return { label: "异常终止", color: "#e85f5f", icon: "💥" };
  return { label: "未执行", color: "#8b7355", icon: "📝" };
}

export function taskCompletedCount(task) {
  const ci = task.caseItems;
  if (!ci?.length) return 0;
  return ci.reduce((s, c) => s + c.pass + c.fail, 0);
}

export function taskTotalCount(task) {
  const ci = task.caseItems;
  if (ci?.length) return ci.reduce((s, c) => s + c.total, 0);
  return (task.caseIds?.length || 0) * (task.loopCount || 1);
}

export function taskProgress(task) {
  const total = taskTotalCount(task);
  if (!total) return 0;
  return Math.round((taskCompletedCount(task) / total) * 100);
}

/** 构建 POST /runner/tasks/save 请求体 */
export function buildTaskSavePayload(task) {
  return {
    id: task.id,
    name: task.name,
    mode: task.mode,
    deviceSerial: task.deviceSerial,
    caseIds: task.caseIds,
    loopCount: task.loopCount,
    intervalSeconds: task.intervalSeconds,
    caseItems: task.caseItems,
    stepStates: task.stepStates,
    overallPass: task.overallPass,
    overallFail: task.overallFail,
    logs: (task.logs || []).slice(-200),
    createdAt: task.createdAt,
    creator: task.creator,
    currentCaseTitle: task.currentCaseTitle || "",
    currentIteration: task.currentIteration || 0,
    failedSteps: (task.failedSteps || []).slice(-200),
    conclusion: task.conclusion || "",
    bugTicket: task.bugTicket || "",
    outcome: task.outcome || "",
    round: task.round || 0,
    startAt: task.startAt || "",
    endAt: task.endAt || "",
  };
}
