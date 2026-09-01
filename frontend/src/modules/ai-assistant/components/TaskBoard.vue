<script setup lang="ts">
import EmptyState from '@/shared/components/patterns/EmptyState.vue'
import ErrorState from '@/shared/components/patterns/ErrorState.vue'
import { AGENT_ROUTES, ROUTE_LABELS } from '../constants'
import { useTaskPublish } from '../composables/useTaskPublish'
import { useTaskList } from '../composables/useTaskList'

const { form, submitting, devices, dialogVisible, openDialog, closeDialog, submit } = useTaskPublish()
const { tasks, loading, error, load } = useTaskList()

const STATUS_LABELS: Record<string, string> = {
  pending: '待执行',
  running: '执行中',
  completed: '成功',
  failed: '失败',
  cancelled: '取消',
  paused: '暂停',
}

function statusLabel(s: string): string {
  return STATUS_LABELS[s] ?? s
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
      <el-button type="primary" @click="openDialog">新建任务</el-button>
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
        <article v-for="t in tasks" :key="t.id" class="task-card">
          <div class="task-card__head">
            <h4 class="task-card__title">{{ t.title }}</h4>
            <span class="task-card__status">{{ statusLabel(t.status) }}</span>
          </div>
          <p class="task-card__goal">{{ t.goal }}</p>
          <div class="task-card__meta">
            <span class="task-card__tag">{{ ROUTE_LABELS[t.route] || t.route }}</span>
            <span v-if="t.device_serial" class="task-card__tag">{{ t.device_serial }}</span>
            <span class="task-card__time">{{ t.created_at }}</span>
          </div>
          <p v-if="t.result" class="task-card__result">{{ t.result }}</p>
        </article>
      </div>
      <EmptyState v-if="!tasks.length && !loading" icon="📋" text="还没有任务" hint="点击「新建任务」创建" />
    </template>
  </section>
</template>

<style scoped>
.task-card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}
.task-card {
  background: var(--ai-sticky-bg, rgb(247, 243, 223));
  border: 1px solid rgba(196, 181, 160, 0.35);
  border-radius: 18px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
.task-card:hover { transform: translateY(-2px); }
.task-card__head { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.task-card__title { margin: 0; font-size: var(--app-size-md); font-weight: 800; color: var(--doodle-ink, #2d2d2d); }
.task-card__status { font-size: var(--app-size-xs); font-weight: 800; padding: 2px 10px; border-radius: 999px; background: rgba(139, 115, 85, 0.1); color: var(--ai-ink-soft); white-space: nowrap; }
.task-card__goal { margin: 0; font-size: var(--app-size-sm); color: var(--ai-ink-soft); line-height: 1.5; }
.task-card__meta { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.task-card__tag { font-size: var(--app-size-xs); font-weight: 700; padding: 1px 8px; border-radius: 999px; background: rgba(139, 115, 85, 0.08); color: var(--ai-ink-muted); }
.task-card__time { font-size: var(--app-size-xs); color: var(--app-ink-muted, #999); margin-left: auto; }
.task-card__result { margin: 0; font-size: var(--app-size-sm); color: var(--ai-ink-muted); line-height: 1.5; }
</style>
