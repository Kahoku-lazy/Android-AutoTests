/**
 * useDebouncedSave — 任务变更防抖保存
 * Extracted from test-runner/index.vue
 */
export function useDebouncedSave(tasks, saveTaskToServer) {
  const _dirtyTaskIds = new Set();
  let _saveTimer = null;
  const SAVE_DEBOUNCE_MS = 1000;

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
    }, SAVE_DEBOUNCE_MS);
  }

  function flushSave() {
    if (_saveTimer) {
      clearTimeout(_saveTimer);
      _saveTimer = null;
    }
    for (const id of _dirtyTaskIds) {
      const t = tasks.value.find((x) => x.id === id);
      if (t) saveTaskToServer(t);
    }
    _dirtyTaskIds.clear();
  }

  function cleanup() {
    if (_saveTimer) {
      clearTimeout(_saveTimer);
      _saveTimer = null;
    }
    _dirtyTaskIds.clear();
  }

  return { scheduleSave, flushSave, cleanup };
}
