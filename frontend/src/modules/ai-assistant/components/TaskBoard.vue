<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import type { FormInstance, UploadRawFile } from 'element-plus'
import { ElMessage } from 'element-plus'
import EmptyState from '@/shared/components/patterns/EmptyState.vue'
import ErrorState from '@/shared/components/patterns/ErrorState.vue'
import FilterTabs from '@/shared/components/FilterTabs.vue'
import ConfirmButton from '@/shared/components/patterns/ConfirmButton.vue'
import DoodleNote from '@/shared/components/DoodleNote.vue'
import DoodleBtn from '@/shared/components/DoodleBtn.vue'
import {
  TASK_STATUS_LABELS,
  taskDetailRoute,
  taskStatusTone,
  type TaskStatusTone,
} from '../constants'
import { formatTaskCost, formatTaskDuration } from '../helpers/task-detail'
import { useTaskPublish } from '../composables/useTaskPublish'
import { useTaskList } from '../composables/useTaskList'
import type { TaskRecord } from '@/shared/types/ai'

/** 任务态 → sticky 底色：成功 Do / 失败 Dont / 执行中 / 等待 */
function stickyStatus(tone: TaskStatusTone): 'ok' | 'run' | 'fail' | 'wait' {
  if (tone === 'success') return 'ok'
  if (tone === 'failed') return 'fail'
  if (tone === 'running') return 'run'
  return 'wait'
}

function deviceDisplay(t: TaskRecord): string {
  return (t.device_label || t.device_serial || '—').trim() || '—'
}

function statusLabel(status: string): string {
  return TASK_STATUS_LABELS[status] || TASK_STATUS_LABELS[taskStatusTone(status)] || status || '—'
}

const router = useRouter()
const {
  form,
  submitting,
  devices,
  dialogVisible,
  ATTACH_ACCEPT,
  openDialog,
  closeDialog,
  submit,
  canSubmit,
  onAttachChange,
  clearAttach,
} = useTaskPublish()

const taskFormRef = ref<FormInstance>()
const taskRules = {
  title: [{ required: true, message: '请填写任务标题', trigger: 'blur' }],
  goal: [{ required: true, message: '请填写任务目标', trigger: 'blur' }],
}
const {
  tasks, loading, error, load,
  activeFilter, filterTabs, filteredItems, groupedByStatus, expandedGroups, emptyCopy,
  clearAll, rerun, rerunningId,
} = useTaskList()

function openDetail(taskId: number) {
  router.push(taskDetailRoute(taskId))
}

function isFailed(t: TaskRecord): boolean {
  return taskStatusTone(t.status) === 'failed'
}

function beforeAttachUpload(raw: UploadRawFile) {
  const name = raw.name || ''
  const ok = /\.(docx|pdf)$/i.test(name)
  if (!ok) {
    ElMessage.error('仅支持 Word（.docx）与 PDF')
    return false
  }
  if (raw.size > 20 * 1024 * 1024) {
    ElMessage.error('文件过大（上限 20MB）')
    return false
  }
  onAttachChange(raw)
  return false // 阻止 el-upload 自动上传；随表单一起提交
}

function onAttachRemove() {
  clearAttach()
}

function onAttachExceed() {
  ElMessage.warning('每条任务最多一份附件')
}

async function onSubmit() {
  try {
    await taskFormRef.value?.validate()
  } catch {
    return
  }
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
    <el-dialog v-model="dialogVisible" title="新建任务" width="640px" :close-on-click-modal="false">
      <el-form ref="taskFormRef" :model="form" :rules="taskRules" label-width="120px" @submit.prevent>
        <el-form-item label="任务标题" prop="title">
          <el-input v-model="form.title" placeholder="例如：校准 H705F 色温" maxlength="200" show-word-limit />
        </el-form-item>
        <el-form-item label="任务目标" prop="goal">
          <el-input v-model="form.goal" type="textarea" :rows="2" placeholder="例如：拖动 H705F 的色温滑块到最左端" />
        </el-form-item>
        <el-form-item label="任务附件">
          <el-upload
            :accept="ATTACH_ACCEPT"
            :limit="1"
            :auto-upload="false"
            :show-file-list="true"
            :before-upload="beforeAttachUpload"
            :on-remove="onAttachRemove"
            :on-exceed="onAttachExceed"
          >
            <el-button size="small">选择 Word / PDF</el-button>
            <template #tip>
              <div class="el-upload__tip">可选；仅 .docx / .pdf，上传后解析为 Markdown 供规划模型使用</div>
            </template>
          </el-upload>
          <p v-if="form.attachmentFile" class="task-attach-name">已选：{{ form.attachmentFile.name }}</p>
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
        <el-button type="primary" :loading="submitting" :disabled="!canSubmit()" @click="onSubmit">提交</el-button>
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
            <DoodleNote
              v-for="t in group.items"
              :key="t.id"
              class="task-card"
              variant="sticky"
              :status="stickyStatus(taskStatusTone(t.status))"
              :tilt="taskStatusTone(t.status) === 'failed' ? 1.2 : -1.1"
            >
              <template #header>
                <h4 class="task-card__title">{{ t.title || '未命名任务' }}</h4>
              </template>
              <ul class="task-card__meta">
                <li><span class="task-card__meta-k">状态</span>{{ statusLabel(t.status) }}</li>
                <li><span class="task-card__meta-k">创建</span>{{ t.created_at || '—' }}</li>
                <li><span class="task-card__meta-k">设备</span>{{ deviceDisplay(t) }}</li>
                <li><span class="task-card__meta-k">助手</span>{{ t.assistant_name || '—' }}</li>
                <li><span class="task-card__meta-k">费用</span>{{ formatTaskCost(t.deepseek_cost) }}</li>
                <li><span class="task-card__meta-k">耗时</span>{{ formatTaskDuration(t.started_at, t.finished_at) }}</li>
                <li class="task-card__meta-row">
                  <span class="task-card__meta-k">附件</span>
                  <span class="task-card__meta-v">{{ t.attachment_filename || '—' }}</span>
                </li>
              </ul>
              <template #actions>
                <DoodleBtn
                  v-if="isFailed(t)"
                  tone="yellow"
                  :disabled="rerunningId === t.id"
                  @click="rerun(t)"
                >
                  {{ rerunningId === t.id ? '重新执行中…' : '重新执行' }}
                </DoodleBtn>
                <DoodleBtn tone="teal" @click="openDetail(t.id)">详情</DoodleBtn>
              </template>
            </DoodleNote>
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
.task-attach-name {
  margin: var(--app-space-xs) 0 0;
  font-size: var(--app-size-xs);
  color: var(--ai-ink-muted);
}
.task-card__meta {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: var(--app-size-sm);
  color: var(--ai-ink-soft);
}
.task-card__meta-k {
  display: inline-block;
  min-width: 2.5em;
  margin-right: var(--app-space-xs);
  font-weight: 700;
  color: var(--ai-ink-muted);
}
/* 附件行：文件名过长时单行省略，不撑高便签卡片 */
.task-card__meta-row {
  display: flex;
  align-items: baseline;
  min-width: 0;
}
.task-card__meta-v {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.task-status-collapse { --el-collapse-border-color: transparent; --el-collapse-header-height: 36px; }
.task-status-collapse :deep(.el-collapse-item) {
  background: var(--app-bg-card);
  border: 2px solid var(--ai-warm-border);
  border-radius: var(--app-radius-lg);
  margin-bottom: var(--app-space-sm);
  overflow: visible;
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
  padding-top: var(--app-space-sm);
}
.task-card__title {
  margin: 0; font-size: var(--app-size-md); font-weight: 800; color: var(--ai-ink-soft);
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.task-status-head__label {
  flex-shrink: 0;
  font-size: var(--app-size-xs); font-weight: 700; padding: 2px 7px;
  border-radius: var(--el-border-radius-small); border: 1.5px solid var(--ink); white-space: nowrap;
  line-height: 1.2;
}
.task-status-head__label.is-pending {
  background: var(--ai-bg-neutral); color: var(--app-timeline-dot); border-color: var(--app-offline);
}
.task-status-head__label.is-running {
  background: var(--ai-status-blue-bg); color: var(--ai-status-blue-text); border-color: var(--ai-status-blue-border);
}
.task-status-head__label.is-success {
  background: var(--app-status-success-bg); color: var(--app-status-success-text); border-color: var(--app-status-success);
}
.task-status-head__label.is-failed {
  background: var(--app-status-danger-bg); color: var(--app-status-danger-text); border-color: var(--app-status-danger);
}
.task-status-head__label.is-cancelled {
  background: var(--ai-bg-neutral); color: var(--ai-ink-muted); border-color: var(--app-offline);
}
.task-status-head__label.is-paused {
  background: var(--app-status-warning-bg); color: var(--ai-hint-orange); border-color: var(--app-highlight);
}
</style>
