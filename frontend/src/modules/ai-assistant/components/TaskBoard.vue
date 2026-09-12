<script setup lang="ts">
import { useRouter } from 'vue-router'
import EmptyState from '@/shared/components/patterns/EmptyState.vue'
import ErrorState from '@/shared/components/patterns/ErrorState.vue'
import FilterTabs from '@/shared/components/FilterTabs.vue'
import ConfirmButton from '@/shared/components/patterns/ConfirmButton.vue'
import { taskDetailRoute, taskStatusLabel, taskStatusTone } from '../constants'
import { useTaskPublish } from '../composables/useTaskPublish'
import { useTaskList } from '../composables/useTaskList'

const router = useRouter()
const { form, submitting, devices, dialogVisible, openDialog, closeDialog, submit } = useTaskPublish()
const {
  tasks, loading, error, load,
  activeFilter, filterTabs, filteredItems, groupedByStatus, expandedGroups, emptyCopy,
  remove, clearAll,
} = useTaskList()

function openDetail(taskId: number) {
  router.push(taskDetailRoute(taskId))
}

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
        <ConfirmButton
          type="warning"
          danger
          plain
          message="将删除全部任务卡片，且不可恢复。确认清空？"
          title="调试 · 清空任务"
          confirm-text="清空"
          :disabled="!tasks.length"
          @confirm="clearAll"
        >调试 · 清空</ConfirmButton>
        <el-button type="primary" @click="openDialog">新建任务</el-button>
      </div>
    </div>

    <!-- 新建任务弹窗 -->
    <el-dialog v-model="dialogVisible" title="新建任务" width="640px">
      <el-form label-width="120px" @submit.prevent>
        <el-form-item label="任务目标" required>
          <el-input v-model="form.goal" type="textarea" :rows="2" placeholder="例如：拖动 H705F 的色温滑块到最左端" />
        </el-form-item>
        <el-form-item label="任务附件文件">
          <el-input v-model="form.attachment" placeholder="附件路径 / URL（可选）" />
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
      </el-form>
      <template #footer>
        <el-button @click="closeDialog">取消</el-button>
        <el-button type="primary" :loading="submitting" :disabled="!form.goal.trim()" @click="onSubmit">提交</el-button>
      </template>
    </el-dialog>

    <!-- 任务卡片列表 -->
    <ErrorState v-if="error" :message="error" @retry="load" />
    <template v-else>
      <div v-loading="loading" class="task-board__body">
      <el-collapse
        v-if="groupedByStatus.length"
        v-model="expandedGroups"
        class="task-status-collapse"
      >
        <el-collapse-item
          v-for="group in groupedByStatus"
          :key="group.key"
          :name="group.key"
          :class="`is-${group.key}`"
        >
          <template #title>
            <div class="task-status-head">
              <span class="task-status-head__label" :class="`is-${group.key}`">{{ group.label }}</span>
              <span class="task-status-head__count">{{ group.items.length }}</span>
            </div>
          </template>
          <div class="task-card-grid">
            <article v-for="t in group.items" :key="t.id" class="task-card">
              <div class="task-card__head">
                <h4 class="task-card__title">{{ t.title || t.goal }}</h4>
                <div class="task-card__badges">
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
              <div class="task-card__actions">
                <el-button size="small" @click="openDetail(t.id)">详情</el-button>
                <ConfirmButton
                  size="small"
                  type="warning"
                  danger
                  plain
                  :message="`删除任务「${t.title || t.goal}」？`"
                  title="确认删除"
                  confirm-text="删除"
                  @confirm="remove(t)"
                >删除</ConfirmButton>
              </div>
            </article>
          </div>
        </el-collapse-item>
      </el-collapse>
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
.task-board__body { min-height: var(--app-space-2xl); }
.task-status-collapse { --el-collapse-border-color: transparent; --el-collapse-header-height: 36px; }
.task-status-collapse :deep(.el-collapse-item) {
  background: var(--app-bg-card);
  border: 2px solid var(--ai-warm-border);
  border-radius: var(--app-radius-lg);
  margin-bottom: var(--app-space-sm);
  overflow: hidden;
}
.task-status-collapse :deep(.el-collapse-item__header) {
  height: var(--el-collapse-header-height);
  line-height: var(--el-collapse-header-height);
  padding: 0 var(--app-space-md);
  font-size: var(--app-size-sm);
  font-weight: 700;
  color: var(--ink);
  border-bottom: 1px solid var(--ai-bg-subtle);
}
.task-status-collapse :deep(.el-collapse-item.is-pending .el-collapse-item__header) {
  background: var(--ai-bg-neutral); color: var(--app-timeline-dot);
}
.task-status-collapse :deep(.el-collapse-item.is-running .el-collapse-item__header) {
  background: var(--ai-status-blue-bg); color: var(--ai-status-blue-text);
}
.task-status-collapse :deep(.el-collapse-item.is-success .el-collapse-item__header) {
  background: var(--app-status-success-bg); color: var(--app-status-success-text);
}
.task-status-collapse :deep(.el-collapse-item.is-failed .el-collapse-item__header) {
  background: var(--app-status-danger-bg); color: var(--app-status-danger-text);
}
.task-status-collapse :deep(.el-collapse-item.is-cancelled .el-collapse-item__header) {
  background: var(--ai-bg-neutral); color: var(--ai-ink-muted);
}
.task-status-collapse :deep(.el-collapse-item.is-paused .el-collapse-item__header) {
  background: var(--app-status-warning-bg); color: var(--ai-hint-orange);
}
.task-status-collapse :deep(.el-collapse-item__title) {
  display: flex;
  align-items: center;
  height: 100%;
  line-height: 1;
}
.task-status-collapse :deep(.el-collapse-item__content) { padding: var(--app-space-md); }
.task-status-head {
  display: flex;
  align-items: center;
  gap: var(--app-space-sm);
  width: 100%;
  line-height: 1.2;
}
.task-status-head__count {
  flex-shrink: 0;
  font-size: var(--app-size-xs);
  font-weight: 600;
  line-height: 1.2;
  color: inherit;
  border: 1px solid currentColor;
  padding: 0 var(--app-space-xs);
  border-radius: var(--app-radius-sm);
}
.task-card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--app-space-md);
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
.task-status-head__label,
.task-card__status {
  flex-shrink: 0;
  font-size: var(--app-size-xs); font-weight: 700; padding: 2px 7px;
  border-radius: 3px 6px 3px 6px; border: 1.5px solid var(--ink); white-space: nowrap;
  line-height: 1.2;
}
.task-status-head__label.is-pending,
.task-card__status.is-pending {
  background: var(--ai-bg-neutral); color: var(--app-timeline-dot); border-color: var(--app-offline);
}
.task-status-head__label.is-running,
.task-card__status.is-running {
  background: var(--ai-status-blue-bg); color: var(--ai-status-blue-text); border-color: var(--ai-status-blue-border);
}
.task-status-head__label.is-success,
.task-card__status.is-success {
  background: var(--app-status-success-bg); color: var(--app-status-success-text); border-color: var(--app-status-success);
}
.task-status-head__label.is-failed,
.task-card__status.is-failed {
  background: var(--app-status-danger-bg); color: var(--app-status-danger-text); border-color: var(--app-status-danger);
}
.task-status-head__label.is-cancelled,
.task-card__status.is-cancelled {
  background: var(--ai-bg-neutral); color: var(--ai-ink-muted); border-color: var(--app-offline);
}
.task-status-head__label.is-paused,
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
.task-card__actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--app-space-sm);
  margin-top: auto;
  padding-top: var(--app-space-sm);
  border-top: 1.5px dashed var(--ai-warm-border);
}
</style>
