<script setup lang="ts">
import EmptyState from '@/shared/components/patterns/EmptyState.vue'
import ErrorState from '@/shared/components/patterns/ErrorState.vue'
import FilterTabs from '@/shared/components/FilterTabs.vue'
import {
  AGENT_ROUTES, ROUTE_ICONS, ROUTE_LABELS, taskStatusLabel, taskStatusTone,
} from '../constants'
import { useTaskPublish } from '../composables/useTaskPublish'
import { useTaskList } from '../composables/useTaskList'

const { form, submitting, devices, dialogVisible, openDialog, closeDialog, submit } = useTaskPublish()
const {
  loading, error, load,
  activeFilter, filterTabs, filteredItems, emptyCopy,
} = useTaskList()

function formatTime(raw?: string): string {
  if (!raw) return ''
  return raw.replace('T', ' ').slice(0, 16)
}

function resultSummary(raw?: string): string {
  if (!raw) return ''
  const text = raw.trim()
  const clamp = (s: string) => {
    const t = s.replace(/\s+/g, ' ').trim()
    return t.length > 120 ? `${t.slice(0, 120)}…` : t
  }
  try {
    const obj = JSON.parse(text)
    if (typeof obj === 'string') return clamp(obj)
    if (obj && typeof obj === 'object') {
      const summary = obj.summary || obj.message || obj.reason
      if (typeof summary === 'string' && summary) return clamp(summary)
      if (Array.isArray(obj.completed) && obj.completed.length) {
        return clamp(`已完成 ${obj.completed.length} 项`)
      }
      if (obj.status) return clamp(String(obj.status))
    }
  } catch { /* 非 JSON，走原文截断 */ }
  return clamp(text)
}

async function onSubmit() {
  await submit(() => {
    closeDialog()
    load()
  })
}
</script>

<template>
  <section class="doc-section step-panel">
    <div class="doc-section__header">
      <h3 class="doc-section__title">任务卡片<span class="doc-tag">Task</span></h3>
      <div class="task-board__actions">
        <FilterTabs :tabs="filterTabs" v-model="activeFilter" />
        <el-button type="primary" @click="openDialog">新建任务</el-button>
      </div>
    </div>

    <!-- 新建任务弹窗 -->
    <el-dialog v-model="dialogVisible" title="新建任务" width="640px">
      <el-form label-width="120px" @submit.prevent>
        <el-form-item label="任务目标" required>
          <el-input v-model="form.goal" type="textarea" :rows="2" placeholder="例如：拖动 H705F 的色温滑块到最左端" />
        </el-form-item>
        <el-form-item label="任务要求">
          <el-input v-model="form.requirements" type="textarea" :rows="2" placeholder="补充说明（可选）" />
        </el-form-item>
        <el-form-item label="任务附件文件">
          <el-input v-model="form.attachment" placeholder="附件路径 / URL（可选）" />
        </el-form-item>
        <el-form-item label="智能体" required>
          <el-select v-model="form.route" style="width:100%">
            <el-option v-for="r in AGENT_ROUTES" :key="r.value" :label="r.label" :value="r.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="设备">
          <el-select v-model="form.device_serial" style="width:100%" clearable filterable placeholder="留空则第一台在线设备">
            <el-option
              v-for="d in devices"
              :key="d.serial"
              :label="`${d.serial}${d.model ? ' · ' + d.model : ''} (${d.status})`"
              :value="d.serial"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="报告文件名">
          <el-input v-model="form.report_name" placeholder="报告文件名（可选）" />
        </el-form-item>
        <el-form-item label="任务校验清单">
          <el-input v-model="form.checklist" type="textarea" :rows="2" placeholder="验收标准（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="closeDialog">取消</el-button>
        <el-button type="primary" :loading="submitting" :disabled="!form.goal.trim()" @click="onSubmit">提交</el-button>
      </template>
    </el-dialog>

    <!-- 任务卡片列表 -->
    <ErrorState v-if="error" :message="error" @retry="load" />
    <template v-else>
      <div v-loading="loading" class="task-card-grid">
        <article v-for="t in filteredItems" :key="t.id" class="task-card">
          <div class="task-card__head">
            <h4 class="task-card__title">{{ t.title || t.goal }}</h4>
            <div class="task-card__badges">
              <span class="task-card__kind" :class="`is-${t.route}`">
                {{ ROUTE_ICONS[t.route] || '' }} {{ ROUTE_LABELS[t.route] || t.route }}
              </span>
              <span class="task-card__status" :class="`is-${taskStatusTone(t.status)}`">
                {{ taskStatusLabel(t.status) }}
              </span>
            </div>
          </div>
          <p class="task-card__goal">{{ t.goal }}</p>
          <div class="task-card__meta">
            <span v-if="t.device_serial" class="task-card__tag">{{ t.device_serial }}</span>
            <span class="task-card__time">{{ formatTime(t.created_at) }}</span>
          </div>
          <p v-if="t.result" class="task-card__result">{{ resultSummary(t.result) }}</p>
        </article>
      </div>
      <EmptyState
        v-if="!filteredItems.length && !loading"
        icon="📋"
        :text="emptyCopy.text"
        :hint="emptyCopy.hint"
      />
    </template>
  </section>
</template>

<style scoped>
.task-board__actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--app-space-sm);
}
.task-card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}
.task-card {
  background: var(--ai-sticky-bg);
  border: 2.5px solid var(--ink);
  border-radius: var(--app-radius-md);
  padding: var(--app-space-md);
  display: flex;
  flex-direction: column;
  gap: var(--app-space-sm);
  box-shadow: var(--app-shadow-sm);
  transition: transform var(--app-duration) var(--app-ease);
}
.task-card:hover { transform: translateY(-2px); }
.task-card__head { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--app-space-sm); }
.task-card__title {
  margin: 0; font-size: var(--app-size-md); font-weight: 800; color: var(--ai-ink-soft);
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.task-card__badges {
  display: flex; flex-shrink: 0; flex-wrap: wrap; gap: 6px; justify-content: flex-end;
}
.task-card__kind {
  font-size: var(--app-size-xs); font-weight: 700; padding: 2px 7px;
  border-radius: 3px 6px 3px 6px; border: 1.5px solid var(--ink); white-space: nowrap;
}
.task-card__kind.is-platform_task {
  background: var(--ai-status-purple-bg); color: var(--ai-status-purple-text);
  border-color: var(--ai-status-purple-border);
}
.task-card__kind.is-device_control {
  background: var(--ai-status-blue-bg); color: var(--ai-status-blue-text);
  border-color: var(--ai-status-blue-border);
}
.task-card__status {
  flex-shrink: 0;
  font-size: var(--app-size-xs); font-weight: 700; padding: 2px 7px;
  border-radius: 3px 6px 3px 6px; border: 1.5px solid var(--ink); white-space: nowrap;
}
.task-card__status.is-pending {
  background: var(--ai-bg-neutral); color: var(--app-timeline-dot); border-color: var(--app-offline);
}
.task-card__status.is-running {
  background: var(--ai-status-blue-bg); color: var(--ai-status-blue-text); border-color: var(--ai-status-blue-border);
}
.task-card__status.is-success {
  background: var(--app-status-success-bg); color: var(--app-status-success-text); border-color: var(--app-status-success);
}
.task-card__status.is-failed {
  background: var(--app-status-danger-bg); color: var(--app-status-danger-text); border-color: var(--app-status-danger);
}
.task-card__status.is-cancelled {
  background: var(--ai-bg-neutral); color: var(--ai-ink-muted); border-color: var(--app-offline);
}
.task-card__status.is-paused {
  background: var(--app-status-warning-bg); color: var(--ai-hint-orange); border-color: var(--app-highlight);
}
.task-card__goal {
  margin: 0; font-size: var(--app-size-sm); color: var(--ai-ink-soft); line-height: 1.5;
  display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;
}
.task-card__meta { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.task-card__tag {
  font-size: var(--app-size-xs); font-weight: 700; padding: 2px 7px;
  border-radius: 3px 6px 3px 6px; border: 1.5px solid var(--ai-warm-border);
  background: var(--ai-warm-bg); color: var(--ai-ink-muted);
}
.task-card__time { font-size: var(--app-size-xs); color: var(--ai-ink-muted); margin-left: auto; }
.task-card__result {
  margin: 0; font-size: var(--app-size-xs); color: var(--ai-ink-muted); line-height: 1.5;
  display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;
}
</style>
