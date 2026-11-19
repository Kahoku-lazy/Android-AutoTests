<script setup lang="ts">
/**
 * 工作流任务表。
 *
 * 分类按现存工作流，执行状态单独下拉。表格沿用设备管理表纸：实线、无阴影、表头图标。
 */
import { computed, ref } from "vue"
import { ElMessage } from "element-plus"
import AppTable from "@/shared/components/AppTable.vue"
import EmptyState from "@/shared/components/patterns/EmptyState.vue"
import ErrorState from "@/shared/components/patterns/ErrorState.vue"
import ConfirmButton from "@/shared/components/patterns/ConfirmButton.vue"
import DoodleBtn from "@/shared/components/DoodleBtn.vue"
import { usePagination } from "@/shared/composables/usePagination"
import {
  TASK_DEFAULT_PAGE_SIZE,
  TASK_PAGE_SIZE_OPTIONS,
  TASK_STATUS_LABELS,
  canRerunTask,
  orchestrationLabel,
  taskStatusLabel,
  workflowKindLabel,
  taskStatusTone,
} from "../constants"
import { caseHover } from "../helpers/case-identity"
import { formatTaskCost, formatTaskDuration } from "../helpers/task-detail"
import { fetchTaskReport } from "../api/tasks"
import { useTaskList } from "../composables/useTaskList"
import TaskStatsStrip from "./TaskStatsStrip.vue"
import type { TaskRecord } from "@/shared/types/ai"

const STATUS_OPTIONS = ["pending", "running", "success", "failed", "interrupted", "cancelled"]
const COLUMNS = [
  { dataIndex: "id", title: "编号", icon: "#", minWidth: 80, align: "center" },
  { dataIndex: "workflow_name", title: "工作流", icon: "☰", minWidth: 180, align: "left" },
  { dataIndex: "orchestration", title: "编排", icon: "☰", minWidth: 90, align: "center" },
  { dataIndex: "kind", title: "种类", icon: "☰", minWidth: 110, align: "center" },
  { dataIndex: "case_label", title: "用例", icon: "☰", minWidth: 180, align: "left" },
  { dataIndex: "status", title: "执行状态", icon: "●", minWidth: 120, align: "center" },
  { dataIndex: "device", title: "设备", icon: "▣", minWidth: 150, align: "center" },
  { dataIndex: "attachment", title: "附件", icon: "▤", minWidth: 160, align: "left" },
  { dataIndex: "created_at", title: "创建", icon: "◷", minWidth: 160, align: "center" },
  { dataIndex: "duration", title: "耗时", icon: "⏱", minWidth: 100, align: "center" },
  { dataIndex: "cost", title: "平台费用", icon: "¥", minWidth: 100, align: "right" },
  { dataIndex: "actions", title: "操作", icon: "✎", minWidth: 180, align: "center" },
]

const workflowId = ref("all")
const statusFilter = ref("")
const {
  tasks,
  workflows,
  stats,
  loading,
  error,
  load,
  rerunningId,
  cancellingId,
  filteredItems,
  emptyCopy,
  clearAll,
  rerun,
  cancel,
} = useTaskList()

const workflowTabs = computed(() => [
  { key: "all", label: "全部" },
  ...workflows.value.map((workflow) => ({ key: String(workflow.id), label: workflow.name })),
])

const visibleTasks = computed(() =>
  filteredItems.value.filter((task) => {
    const workflowOk =
      workflowId.value === "all" || String(task.workflow_id || "") === workflowId.value
    const statusOk = !statusFilter.value || taskStatusTone(task.status) === statusFilter.value
    return workflowOk && statusOk
  }),
)
// 每页行数由 constants 提供（固定 10，不渲染选择器）
const { currentPage, totalPages, pagedItems, goPage } = usePagination(visibleTasks, {
  pageSize: TASK_DEFAULT_PAGE_SIZE,
  options: TASK_PAGE_SIZE_OPTIONS,
})

function deviceDisplay(task: TaskRecord): string {
  return (task.device_label || task.device_serial || "—").trim() || "—"
}

function canRerun(task: TaskRecord): boolean {
  return canRerunTask(task.status)
}

async function openReport(task: TaskRecord) {
  if (!task.report_run || !task.report_name) return
  try {
    const content = await fetchTaskReport(task.report_run, task.report_name)
    if (!content) {
      ElMessage.error("报告不存在")
      return
    }
    const url = URL.createObjectURL(new Blob([content], { type: "text/html" }))
    window.open(url, "_blank", "noopener")
    window.setTimeout(() => URL.revokeObjectURL(url), 60_000)
  } catch {
    ElMessage.error("报告打开失败")
  }
}
</script>

<template>
  <section class="task-share">
    <TaskStatsStrip :stats="stats" :loading="loading" />
  </section>

  <section class="doc-section task-table-section">
    <div class="task-toolbar">
      <el-select v-model="workflowId" placeholder="工作流" class="task-workflow-filter">
        <el-option v-for="tab in workflowTabs" :key="tab.key" :label="tab.label" :value="tab.key" />
      </el-select>
      <el-select v-model="statusFilter" clearable placeholder="执行状态" class="task-status-filter">
        <el-option
          v-for="key in STATUS_OPTIONS"
          :key="key"
          :label="TASK_STATUS_LABELS[key]"
          :value="key"
        />
      </el-select>
      <ConfirmButton
        type="warning"
        danger
        plain
        message="将删除全部任务记录，且不可恢复。确认清空？"
        title="调试 · 清空任务"
        confirm-text="清空"
        :disabled="!tasks.length"
        @confirm="clearAll"
        >调试 · 清空</ConfirmButton
      >
    </div>

    <ErrorState v-if="error && !loading" :message="error" @retry="load" />

    <div class="table-toolbar">
      <span class="page-info"
        >第 {{ currentPage }} / {{ totalPages }} 页 · 共 {{ visibleTasks.length }} 条</span
      >
      <div class="page-nav">
        <button
          type="button"
          class="page-nav-btn"
          :disabled="currentPage <= 1"
          @click="goPage(currentPage - 1)"
        >
          上一页
        </button>
        <button
          type="button"
          class="page-nav-btn"
          :disabled="currentPage >= totalPages"
          @click="goPage(currentPage + 1)"
        >
          下一页
        </button>
      </div>
    </div>

    <AppTable
      class="task-table"
      :columns="COLUMNS"
      :data-source="pagedItems"
      row-key="id"
      :striped="true"
      :loading="loading"
      table-layout="fixed"
      accent="var(--c-ai)"
      empty-text="暂无数据"
    >
      <template v-for="col in COLUMNS" :key="col.dataIndex" v-slot:[`header-${col.dataIndex}`]>
        <span class="th-ico" aria-hidden="true">{{ col.icon }}</span
        >{{ col.title }}
      </template>
      <template #cell-case_label="{ record }">
        <span class="case-label" :title="caseHover(record.case_rows)">{{
          record.case_label || "—"
        }}</span>
      </template>
      <template #cell-orchestration="{ record }">{{
        orchestrationLabel(record.orchestration || "")
      }}</template>
      <template #cell-kind="{ record }">{{ workflowKindLabel(record.kind || "") }}</template>
      <template #cell-status="{ record }">
        <span class="status-pill" :class="`is-${taskStatusTone(record.status)}`">{{
          taskStatusLabel(record.status)
        }}</span>
      </template>
      <template #cell-device="{ record }">{{ deviceDisplay(record) }}</template>
      <template #cell-attachment="{ record }">{{ record.attachment_filename || "—" }}</template>
      <template #cell-duration="{ record }">{{
        formatTaskDuration(record.started_at, record.finished_at)
      }}</template>
      <template #cell-cost="{ record }">{{ formatTaskCost(record.deepseek_cost) }}</template>
      <template #cell-actions="{ record }">
        <DoodleBtn
          v-if="taskStatusTone(record.status) === 'running'"
          tone="danger"
          :disabled="cancellingId === record.id"
          @click="cancel(record)"
          >关闭</DoodleBtn
        >
        <DoodleBtn
          v-if="canRerun(record)"
          tone="yellow"
          :disabled="rerunningId === record.id"
          @click="rerun(record)"
          >重新执行</DoodleBtn
        >
        <DoodleBtn
          v-if="record.report_run && record.report_name"
          tone="teal"
          @click="openReport(record)"
          >报告</DoodleBtn
        >
      </template>
      <template #empty>
        <EmptyState icon="☰" :text="emptyCopy.text" :hint="emptyCopy.hint" />
      </template>
    </AppTable>
  </section>
</template>

<style scoped>
.case-label {
  display: inline-block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.task-toolbar,
.table-toolbar {
  display: flex;
  align-items: center;
  gap: var(--app-space-sm);
  flex-wrap: wrap;
}
/* 两行工具栏与表格之间都留出明显间距 */
.task-toolbar {
  margin-bottom: var(--app-space-md);
}
.table-toolbar {
  margin-top: var(--app-space-sm);
  margin-bottom: var(--app-space-md);
}
.task-workflow-filter {
  width: 200px;
}
.task-status-filter {
  width: 160px;
}
.page-nav {
  display: flex;
  gap: var(--app-space-sm);
  margin-left: auto;
}
.page-nav-btn {
  min-width: 36px;
  padding: var(--app-space-xs) 10px;
  border: 2px solid var(--ink);
  border-radius: 2px;
  background: var(--c-workflow);
  color: var(--app-text-primary);
  font-weight: var(--app-font-weight-bold);
  box-shadow: 2px 2px 0 0 var(--ink);
}
/* 不可点：灰底灰边 + 撤影，与可点态一眼可分 */
.page-nav-btn:disabled {
  background: var(--app-bg-subtle);
  border-color: var(--app-border-strong);
  color: var(--app-text-secondary);
  box-shadow: none;
  cursor: not-allowed;
}
.page-info {
  color: var(--app-text-secondary);
  font-size: var(--app-size-sm);
}
.th-ico {
  margin-right: 4px;
}
.status-pill {
  /* 每个 tone 只声明 --sp-color，基类统一产出：状态色描边 + 20%→5% 纵向渐变 + 深色文字 */
  --sp-color: var(--app-border-strong);
  display: inline-flex;
  align-items: center;
  padding: 0 10px;
  border: 1.5px solid color-mix(in srgb, var(--sp-color) 75%, transparent);
  border-radius: var(--app-radius-pill);
  background: linear-gradient(
    180deg,
    color-mix(in srgb, var(--sp-color) 20%, var(--app-bg-card)),
    color-mix(in srgb, var(--sp-color) 5%, var(--app-bg-card))
  );
  color: var(--ink);
  font-size: var(--app-size-xs);
  font-weight: var(--app-font-weight-bold);
  white-space: nowrap;
}
/* 七态色相：全部取已登记令牌，不新增颜色原子 */
.status-pill.is-pending {
  --sp-color: var(--c-dashboard);
}
.status-pill.is-running {
  --sp-color: var(--c-workflow);
}
.status-pill.is-paused {
  --sp-color: var(--app-status-purple);
}
.status-pill.is-success {
  --sp-color: var(--app-status-success);
}
.status-pill.is-failed {
  --sp-color: var(--app-status-danger);
}
.status-pill.is-interrupted {
  --sp-color: var(--c-ops);
}
.status-pill.is-cancelled {
  --sp-color: var(--c-report);
}
</style>
