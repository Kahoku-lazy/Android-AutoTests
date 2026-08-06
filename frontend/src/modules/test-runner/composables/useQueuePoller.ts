/**
 * useQueuePoller — 轮询检测排队任务是否被后端调度
 * Extracted from test-runner/index.vue
 *
 * getActiveRuns — api.js 函数，通过依赖注入传入，避免 composable 直接 import client
 */
import { ref } from "vue";

export function useQueuePoller(tasks, isTaskQueued, onTaskActivated, taskAddLog, scheduleSave, getActiveRuns) {
  const POLL_INTERVAL = 1500;
  const queuePollTimer = ref(null);

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
          const idx = tasks.value.findIndex((t) => t.id === active.client_task_id);
          if (idx !== -1) {
            const updated = {
              ...tasks.value[idx],
              running: true,
              runId: active.run_id,
              status: "running",
            };
            tasks.value.splice(idx, 1, updated);
            onTaskActivated(updated, active.run_id);
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
    pollQueuedTasks();
    queuePollTimer.value = setInterval(pollQueuedTasks, POLL_INTERVAL);
  }

  function stopQueuePolling() {
    if (queuePollTimer.value) {
      clearInterval(queuePollTimer.value);
      queuePollTimer.value = null;
    }
  }

  return { queuePollTimer, pollQueuedTasks, startQueuePolling, stopQueuePolling };
}
