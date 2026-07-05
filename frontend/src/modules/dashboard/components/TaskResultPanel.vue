<script setup>
defineProps({
  tasks: { type: Array, default: () => [] },
  summary: {
    type: Object,
    default: () => ({ passed: 0, failed: 0, new_cases_week: 0 }),
  },
})

const statusMeta = {
  success: { icon: '✓', label: '全部通过', cls: 'is-success' },
  failed: { icon: '✗', label: '全部失败', cls: 'is-failed' },
  partial: { icon: '△', label: '部分失败', cls: 'is-partial' },
  running: { icon: '▶', label: '执行中', cls: 'is-running' },
  idle: { icon: '○', label: '未执行', cls: 'is-idle' },
}

function meta(status) {
  return statusMeta[status] || statusMeta.idle
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
      <div v-for="task in tasks" :key="task.id" class="task-row">
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
.task-result-panel {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.task-result-panel__summary {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.summary-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.summary-chip.is-success { background: rgba(111, 186, 44, 0.12); color: #4a7a18; }
.summary-chip.is-failed { background: rgba(224, 90, 90, 0.12); color: #b33a3a; }
.summary-chip.is-new { background: rgba(136, 157, 240, 0.12); color: #4a5fc0; }

.summary-chip__icon {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 800;
  background: rgba(255, 255, 255, 0.7);
}

.summary-chip__value {
  font-size: 16px;
  font-weight: 800;
}

.task-result-panel__list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.task-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(255, 248, 240, 0.75);
  border: 1px solid rgba(139, 115, 85, 0.1);
}

.task-row__status {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 800;
  flex-shrink: 0;
}

.task-row__status.is-success { background: #6fba2c; color: #fff; }
.task-row__status.is-failed { background: #e05a5a; color: #fff; }
.task-row__status.is-partial { background: #f5c31c; color: #5a4a20; }
.task-row__status.is-running { background: #889df0; color: #fff; animation: pulse 1.5s ease-in-out infinite; }
.task-row__status.is-idle { background: rgba(139, 115, 85, 0.12); color: #988B7A; }

.task-row__body {
  flex: 1;
  min-width: 0;
}

.task-row__title {
  font-size: 14px;
  font-weight: 700;
  color: #4A3A28;
  margin-bottom: 4px;
}

.task-row__cases {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 4px;
}

.case-icon {
  width: 22px;
  height: 22px;
  border-radius: 6px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 800;
}

.case-icon.is-success { background: rgba(111, 186, 44, 0.18); color: #4a7a18; }
.case-icon.is-failed { background: rgba(224, 90, 90, 0.18); color: #b33a3a; }
.case-icon.is-partial { background: rgba(245, 195, 28, 0.22); color: #7a6510; }
.case-icon.is-running { background: rgba(136, 157, 240, 0.22); color: #4a5fc0; }

.task-row__stats {
  font-size: 11px;
  color: #988B7A;
}

.task-row__time {
  font-size: 11px;
  color: #9f927d;
  white-space: nowrap;
  flex-shrink: 0;
  padding-top: 2px;
}

.task-result-panel__empty {
  text-align: center;
  color: #988B7A;
  font-size: 13px;
  padding: 24px 0;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.65; }
}
</style>
