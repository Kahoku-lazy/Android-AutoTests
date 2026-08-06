<script setup lang="ts">
defineProps<{
  hint?: object | string | null
  importing?: boolean
}>()

const emit = defineEmits<{ 'import-prd': [payload: object] }>()

function taskStatusClass(status: string): string {
  return status?.toLowerCase() || "";
}

function taskStatusLabel(status) {
  const map = {
    PENDING: "待执行",
    RUNNING: "执行中",
    COMPLETED: "已完成",
    FAILED: "失败",
    STOPPED: "已停止",
  };
  return map[status?.toUpperCase()] || status || "";
}

function genericHintText(hint) {
  if (typeof hint === "string") return hint;
  return hint?.hint || hint?.text || JSON.stringify(hint);
}
</script>

<template>
  <template v-if="hint">
    <div v-if="hint.type === 'task_card'" class="task-card">
      <div class="task-card-header">
        <span class="task-status-badge" :class="taskStatusClass(hint.status)">
          {{ taskStatusLabel(hint.status) }}
        </span>
        <span class="task-id">
          #{{ hint.run_id?.replace("ai-task-", "").slice(0, 12) }}
        </span>
      </div>
      <div class="task-title">{{ hint.title || "AI 任务" }}</div>
      <div class="task-meta">
        <span>📱 {{ hint.device || "—" }}</span>
        <span v-if="hint.device_model"> ({{ hint.device_model }})</span>
      </div>
      <div class="task-meta">
        <span>📋 {{ (hint.case_titles || []).length }} 个用例</span>
        <span v-if="hint.loop_count > 1"> · 🔁 {{ hint.loop_count }} 轮</span>
      </div>
    </div>

    <div v-else-if="hint.type === 'sop_card'" class="sop-card">
      <div class="sop-card-header">
        <span class="sop-icon">📋</span>
        <span class="sop-title">SOP 工作流</span>
        <span class="sop-phase-badge" :class="'phase-' + hint.phase">
          阶段 {{ hint.phase }}: {{ hint.phase_label }}
        </span>
      </div>
      <div v-if="hint.requirement" class="sop-requirement">
        <strong>需求:</strong> {{ hint.requirement }}
      </div>
      <div v-if="hint.case_count > 0" class="sop-cases">
        <strong>用例设计 ({{ hint.case_count }} 个):</strong>
        <ol>
          <li v-for="(name, i) in hint.case_names" :key="i">{{ name }}</li>
        </ol>
      </div>
      <div v-if="hint.next_hint" class="sop-hint">
        <span class="arrow">→</span> {{ hint.next_hint }}
      </div>
    </div>

    <div v-else-if="hint.type === 'prd_case_preview'" class="prd-preview-card">
      <div class="prd-preview-header">
        <span class="prd-icon">📄</span>
        <span class="prd-title">PRD 用例设计完成</span>
      </div>
      <div class="prd-preview-body">
        <div class="prd-preview-stat">
          <span class="prd-stat-value">{{ hint.total_cases || 0 }}</span>
          <span class="prd-stat-label">生成用例</span>
        </div>
        <div v-if="hint.p0_count" class="prd-preview-stat">
          <span class="prd-stat-value p0">{{ hint.p0_count }}</span>
          <span class="prd-stat-label">P0 必测</span>
        </div>
        <div v-if="hint.p1_count" class="prd-preview-stat">
          <span class="prd-stat-value p1">{{ hint.p1_count }}</span>
          <span class="prd-stat-label">P1 应测</span>
        </div>
      </div>
      <div class="prd-preview-actions">
        <button
          class="prd-import-btn"
          :disabled="importing"
          @click="
            emit('import-prd', {
              sessionId: hint.session_id,
              cases: hint.cases_preview,
            })
          "
        >
          {{ importing ? "导入中..." : "📥 导入到用例库" }}
        </button>
      </div>
    </div>

    <div v-else class="hint-block">
      <span class="hint-icon">💡</span>
      <span class="hint-text">{{ genericHintText(hint) }}</span>
    </div>
  </template>
</template>

<style scoped>
.hint-block {
  margin: 4px 0;
  padding: 8px 12px;
  border-radius: 10px;
  background: rgba(230, 249, 246, 0.3);
  border: 1px solid rgba(25, 200, 185, 0.2);
  font-size: var(--app-size-sm);
  color: var(--doodle-ink, #2d2d2d);
}
.hint-icon {
  margin-right: 6px;
}
.hint-text {
  white-space: pre-wrap;
}
.sop-card {
  margin: 8px 0;
  padding: 14px 16px;
  border-radius: 12px;
  background: linear-gradient(135deg, #eeedfe 0%, #e1f5ee 100%);
  border: 1.5px solid #afa9ec;
  box-shadow: 0 2px 8px rgba(83, 74, 183, 0.08);
}
.sop-card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}
.sop-icon {
  font-size: var(--app-size-lg);
}
.sop-title {
  font-weight: 600;
  font-size: var(--app-size-sm);
  color: #3c3489;
}
.sop-phase-badge {
  margin-left: auto;
  padding: 3px 10px;
  border-radius: 10px;
  font-size: var(--app-size-sm);
  font-weight: 500;
  background: var(--ai-hint-purple);
  color: white;
}
.sop-phase-badge.phase-1 {
  background: var(--ai-hint-blue);
}
.sop-phase-badge.phase-2 {
  background: var(--ai-hint-green);
}
.sop-phase-badge.phase-3 {
  background: var(--ai-hint-orange);
}
.sop-phase-badge.phase-4 {
  background: var(--ai-hint-red);
}
.sop-requirement {
  font-size: var(--app-size-sm);
  color: #2c2c2a;
  margin: 6px 0;
  line-height: 1.5;
}
.sop-cases {
  font-size: var(--app-size-sm);
  color: #2c2c2a;
  margin: 6px 0;
}
.sop-cases ol {
  margin: 4px 0 0 20px;
  padding: 0;
}
.sop-cases li {
  margin: 3px 0;
}
.sop-hint {
  margin-top: 10px;
  padding: 8px 12px;
  border-radius: 8px;
  background: #fff;
  font-size: var(--app-size-sm);
  color: #3c3489;
  font-weight: 500;
}
.sop-hint .arrow {
  color: var(--ai-hint-green);
  font-weight: 600;
  margin-right: 4px;
}
.prd-preview-card {
  margin: 8px 0;
  padding: 14px 16px;
  border-radius: 12px;
  background: linear-gradient(135deg, var(--ai-hint-yellow-bg) 0%, #fff0e0 100%);
  border: 1.5px solid var(--ai-hint-yellow-border);
  box-shadow: 0 2px 8px rgba(247, 205, 103, 0.12);
  animation: card-appear 0.25s ease;
}
@keyframes card-appear {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
.prd-preview-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}
.prd-icon {
  font-size: var(--app-size-lg);
}
.prd-title {
  font-weight: 600;
  font-size: var(--app-size-sm);
  color: #8b6914;
}
.prd-preview-body {
  display: flex;
  gap: 16px;
  margin: 10px 0;
}
.prd-preview-stat {
  text-align: center;
}
.prd-stat-value {
  font-size: var(--app-size-xl);
  font-weight: 700;
  color: #f7a826;
}
.prd-stat-value.p0 {
  color: var(--app-error);
}
.prd-stat-value.p1 {
  color: #f7a826;
}
.prd-stat-label {
  font-size: var(--app-size-sm);
  color: #9f927d;
  margin-top: 2px;
}
.prd-preview-actions {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid rgba(247, 205, 103, 0.3);
}
.prd-import-btn {
  width: 100%;
  padding: 10px 16px;
  border-radius: 10px;
  border: 1.5px solid #f7a826;
  background: var(--ai-hint-yellow-bg);
  color: #8b6914;
  font-size: var(--app-size-sm);
  font-weight: 700;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.15s;
}
.prd-import-btn:hover:not(:disabled) {
  background: var(--ai-hint-yellow-border);
  color: #fff;
}
.prd-import-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.task-card {
  margin: 8px 0;
  padding: 14px 16px;
  border-radius: 12px;
  background: linear-gradient(135deg, var(--ai-teal-bg) 0%, #f0faf8 100%);
  border: 1.5px solid var(--app-accent-purple, #b39ef3);
  box-shadow: 0 2px 8px rgba(25, 200, 185, 0.1);
}
.task-card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.task-status-badge {
  font-size: var(--app-size-xs);
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 8px;
  text-transform: uppercase;
}
.task-status-badge.pending {
  background: var(--ai-hint-orange-bg);
  color: #e65100;
}
.task-status-badge.running {
  background: #e3f2fd;
  color: #1565c0;
}
.task-status-badge.completed {
  background: #e8f5e9;
  color: var(--app-status-success-text);
}
.task-status-badge.failed {
  background: #ffebee;
  color: var(--app-status-danger-text);
}
.task-status-badge.stopped {
  background: #f5f5f5;
  color: var(--app-text-secondary);
}
.task-id {
  font-size: var(--app-size-xs);
  color: #8a7b66;
  font-family: var(--app-font-mono);
}
.task-title {
  font-size: var(--app-size-md);
  font-weight: 700;
  color: var(--doodle-ink, #2d2d2d);
  margin-bottom: 6px;
}
.task-meta {
  font-size: var(--app-size-sm);
  color: #6d5f4b;
  margin: 2px 0;
}
</style>
