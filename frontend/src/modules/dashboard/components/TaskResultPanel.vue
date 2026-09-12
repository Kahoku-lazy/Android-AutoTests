<script setup lang="ts">
import { useRouter } from 'vue-router'
import type { RecentTask, ExecutionSummary } from '@/shared/types/dashboard'

const router = useRouter()

interface TaskResultPanelProps {
  tasks?: RecentTask[]
  summary?: ExecutionSummary
}

withDefaults(defineProps<TaskResultPanelProps>(), {
  tasks: () => [],
  summary: () => ({ passed: 0, failed: 0 }),
})

interface StatusMetaItem {
  icon: string
  label: string
  cls: string
}

const statusMeta: Record<string, StatusMetaItem> = {
  success: { icon: '✓', label: '全部通过', cls: 'is-success' },
  failed: { icon: '✗', label: '全部失败', cls: 'is-failed' },
  partial: { icon: '△', label: '部分失败', cls: 'is-partial' },
  running: { icon: '▶', label: '执行中', cls: 'is-running' },
  idle: { icon: '○', label: '未执行', cls: 'is-idle' },
}

function meta(status: string): StatusMetaItem {
  return statusMeta[status] || statusMeta['idle']
}

function taskId(task: RecentTask): string | number | null {
  return task.id || task.task_id || task.run_id || null
}

function openTask(task: RecentTask) {
  const id = taskId(task)
  if (!id) return
  router.push('/reports')
}
</script>

<template>
  <div class="task-result-panel">
    <div class="task-result-panel__summary">
      <div class="summary-chip is-success">
        <span class="summary-chip__icon">✓</span>
        <span class="summary-chip__value">{{ summary.passed }}</span>
        <span class="summary-chip__label">成功</span>
      </div>
      <div class="summary-chip is-failed">
        <span class="summary-chip__icon">✗</span>
        <span class="summary-chip__value">{{ summary.failed }}</span>
        <span class="summary-chip__label">失败</span>
      </div>
    </div>

    <div v-if="tasks.length" class="task-result-panel__list">
      <div
        v-for="(task, idx) in tasks"
        :key="String(task.id ?? task.task_id ?? task.run_id ?? `${task.title}-${task.time}-${idx}`)"
        class="task-row"
        :class="{ 'task-row--clickable': taskId(task) }"
        :role="taskId(task) ? 'button' : undefined"
        :tabindex="taskId(task) ? 0 : undefined"
        @click="openTask(task)"
        @keydown.enter.prevent="openTask(task)"
        @keydown.space.prevent="openTask(task)">
        <div class="task-row__status" :class="meta(task.status).cls" :title="meta(task.status).label">
          {{ meta(task.status).icon }}
        </div>
        <div class="task-row__body">
          <div class="task-row__title">{{ task.title }}</div>
          <div class="task-row__cases">
            <span
              v-for="(c, i) in (task.cases || [])"
              :key="i"
              class="case-icon"
              :class="meta(c.status).cls"
              :title="`${c.title} · 成功 ${c.passed} / 失败 ${c.failed}`"
            >{{ meta(c.status).icon }}</span>
          </div>
          <div v-if="task.total" class="task-row__stats">
            成功 {{ task.passed }} · 失败 {{ task.failed }} · 共 {{ task.total }} 次
          </div>
        </div>
        <div class="task-row__time">{{ task.time }}</div>
      </div>
    </div>
    <div v-else class="task-result-panel__empty">暂无执行记录，前往执行引擎启动任务</div>
  </div>
</template>

<style scoped>
/* 任务结果面板 — 纯净卡片风 */
.task-result-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  flex: 1;
  min-height: 0;
}

.task-result-panel__summary {
  display: flex;
  flex-wrap: wrap;
  gap: var(--app-space-sm);
  flex-shrink: 0;
}

.summary-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 999px;
  font-size: var(--app-size-sm);
  font-weight: 700;
  border: 1px solid var(--app-border-light);
  background: var(--app-bg-card);
  color: var(--ink);
}

.summary-chip.is-success {
  border-color: var(--app-status-success-bg);
  background: var(--app-status-success-bg);
  color: var(--app-status-success-text);
}
.summary-chip.is-failed {
  border-color: var(--app-status-danger-bg);
  background: var(--app-status-danger-bg);
  color: var(--app-status-danger-text);
}

.summary-chip__icon {
  width: 16px; height: 16px; border-radius: 50%;
  display: inline-flex; align-items: center; justify-content: center;
  font-size: var(--app-size-xs); font-weight: 800;
  background: var(--app-bg-card);
}
.summary-chip__value { font-size: var(--app-size-md); font-weight: 800; }

.task-result-panel__list {
  display: flex; flex-direction: column; gap: var(--app-space-sm);
  flex: 1; min-height: 0; overflow-y: auto;
  --task-row-height: 68px;
  max-height: calc(var(--task-row-height) * 4 + 8px * 3);
}

.task-row {
  display: flex; align-items: flex-start; gap: 12px;
  padding: 10px 12px; border-radius: var(--app-radius-sm);
  background: var(--app-bg-card); border: 1px solid var(--app-border-light);
  transition: background var(--app-duration-fast) var(--app-ease),
    border-color var(--app-duration-fast) var(--app-ease);
}
.task-row--clickable { cursor: pointer; }
.task-row--clickable:hover {
  background: var(--app-bg-subtle);
  border-color: var(--app-border-lighter);
}
.task-row__status {
  width: 28px; height: 28px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-size: var(--app-size-sm); font-weight: 800; flex-shrink: 0;
}
.task-row__status.is-success { background: var(--app-status-success-bg); color: var(--app-status-success-text); }
.task-row__status.is-failed  { background: var(--app-status-danger-bg); color: var(--app-status-danger-text); }
.task-row__status.is-partial { background: var(--app-status-warning-bg); color: var(--app-warning-text); }
.task-row__status.is-running { background: var(--app-status-purple-bg); color: var(--app-status-purple-text); animation: pulse 1.5s ease-in-out infinite; }
.task-row__status.is-idle    { background: var(--app-bg-subtle); color: var(--app-ink-muted); }

.task-row__body { flex: 1; min-width: 0; }
.task-row__title { font-size: var(--app-size-sm); font-weight: 700; color: var(--ink); margin-bottom: 3px; }

.task-row__cases { display: flex; flex-wrap: wrap; gap: var(--app-space-xs); margin-bottom: 3px; }
.case-icon {
  width: 20px; height: 20px; border-radius: 6px;
  display: inline-flex; align-items: center; justify-content: center;
  font-size: var(--app-size-xs); font-weight: 800;
}
.case-icon.is-success { background: var(--app-status-success-bg); color: var(--app-status-success-text); }
.case-icon.is-failed  { background: var(--app-status-danger-bg); color: var(--app-status-danger-text); }
.case-icon.is-partial { background: var(--app-status-warning-bg); color: var(--app-warning-text); }
.case-icon.is-running { background: var(--app-status-purple-bg); color: var(--app-status-purple-text); }

.task-row__stats { font-size: var(--app-size-xs); color: var(--app-ink-muted); font-weight: 600; }
.task-row__time { font-size: var(--app-size-xs); color: var(--app-ink-muted); white-space: nowrap; flex-shrink: 0; padding-top: 3px; }

.task-result-panel__empty { text-align: center; color: var(--app-ink-muted); font-size: var(--app-size-sm); padding: 20px 0; }

@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.6; } }

@media (prefers-reduced-motion: reduce) {
  .task-row__status.is-running { animation: none; }
}
</style>
