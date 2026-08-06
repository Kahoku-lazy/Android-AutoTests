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
  summary: () => ({ passed: 0, failed: 0, new_cases_week: 0 }),
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
  // 只有执行中任务有 client_task_id 能定位详情页
  // 已完成任务跳转列表页（后端 ID 与前端 ID 不兼容）
  if (task.status === 'running') {
    router.push(`/runner/task/${id}`)
  } else {
    router.push('/runner')
  }
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
      <div class="summary-chip is-new">
        <span class="summary-chip__icon">+</span>
        <span class="summary-chip__value">{{ summary.new_cases_week }}</span>
        <span class="summary-chip__label">本周新建</span>
      </div>
    </div>

    <div v-if="tasks.length" class="task-result-panel__list">
      <div
        v-for="task in tasks"
        :key="task.id || task.task_id || task.run_id || Math.random()"
        class="task-row"
        :class="{ 'task-row--clickable': taskId(task) }"
        @click="openTask(task)">
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
/* Paper × Polaroid — 任务结果面板 */
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
  gap: 8px;
  flex-shrink: 0;
}

.summary-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 10px;
  border-radius: 4px 8px 4px 8px;
  font-size: var(--app-size-xs);
  font-weight: 700;
  border: 2px solid var(--ink);
  background: #fff;
}

.summary-chip.is-success { border-color: var(--app-status-success); color: var(--app-status-success-text); }
.summary-chip.is-failed  { border-color: var(--app-status-danger); color: var(--app-status-danger-text); }
.summary-chip.is-new     { border-color: var(--app-status-purple); color: #5a3fa0; }

.summary-chip__icon {
  width: 16px; height: 16px; border-radius: 3px;
  display: inline-flex; align-items: center; justify-content: center;
  font-size: var(--app-size-xs); font-weight: 800;
  background: var(--app-bg-subtle);
}
.summary-chip__value { font-size: var(--app-size-md); font-weight: 800; }

.task-result-panel__list {
  display: flex; flex-direction: column; gap: 6px;
  flex: 1; min-height: 0; overflow-y: auto;
  --task-row-height: 68px;
  max-height: calc(var(--task-row-height) * 4 + 6px * 3);
}

.task-row {
  display: flex; align-items: flex-start; gap: 10px;
  padding: 10px 12px; border-radius: 4px 8px 4px 8px;
  background: #fff; border: 1.5px solid var(--app-border-light);
  transition: background var(--app-duration-fast) var(--app-ease);
}
.task-row--clickable { cursor: pointer; }
.task-row--clickable:hover { background: rgba(78, 205, 196, 0.12); }

.task-row__status {
  width: 28px; height: 28px; border-radius: 4px 8px 4px 8px;
  display: flex; align-items: center; justify-content: center;
  font-size: var(--app-size-sm); font-weight: 800; flex-shrink: 0;
  border: 2px solid var(--ink);
}
.task-row__status.is-success { background: #C8F5D0; color: var(--ink); }
.task-row__status.is-failed  { background: #FFE0DB; color: var(--ink); }
.task-row__status.is-partial { background: #FFF9E0; color: var(--ink); }
.task-row__status.is-running { background: #E8DDF8; color: var(--ink); animation: pulse 1.5s ease-in-out infinite; }
.task-row__status.is-idle    { background: #f8f6f2; color: #999; }

.task-row__body { flex: 1; min-width: 0; }
.task-row__title { font-size: var(--app-size-sm); font-weight: 700; color: var(--ink); margin-bottom: 3px; }

.task-row__cases { display: flex; flex-wrap: wrap; gap: 3px; margin-bottom: 3px; }
.case-icon {
  width: 20px; height: 20px; border-radius: 3px 6px 3px 6px;
  display: inline-flex; align-items: center; justify-content: center;
  font-size: var(--app-size-xs); font-weight: 800; border: 1.5px solid var(--ink);
}
.case-icon.is-success { background: #C8F5D0; color: var(--ink); }
.case-icon.is-failed  { background: #FFE0DB; color: var(--ink); }
.case-icon.is-partial { background: #FFF9E0; color: var(--ink); }
.case-icon.is-running { background: #E8DDF8; color: var(--ink); }

.task-row__stats { font-size: var(--app-size-xs); color: var(--app-ink-muted); font-weight: 600; }
.task-row__time { font-size: var(--app-size-xs); color: var(--app-ink-muted); white-space: nowrap; flex-shrink: 0; padding-top: 2px; }

.task-result-panel__empty { text-align: center; color: var(--app-ink-muted); font-size: var(--app-size-sm); padding: 20px 0; }

@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.6; } }
</style>
