<script setup lang="ts">
import { computed } from "vue"
import { ElMessage } from "element-plus"
import SkeletonCard from "@/shared/components/patterns/SkeletonCard.vue"
import EmptyState from "@/shared/components/patterns/EmptyState.vue"
import DoodleBtn from "@/shared/components/DoodleBtn.vue"
import { fetchTaskReport } from "@/modules/task-list/api/tasks"
import {
  bugCategoryClass,
  bugKindLabel,
  bugStatusClass,
  bugTaskStatusLabel,
  formatBugTime,
} from "../constants"
import type { BugFailureStep, BugStatus, BugTicket } from "../types"

const props = defineProps<{
  modelValue: boolean
  bug: BugTicket | null
  loading: boolean
  updating: boolean
}>()

const emit = defineEmits<{
  "update:modelValue": [value: boolean]
  "status-change": [status: BugStatus]
}>()

const steps = computed(() => props.bug?.failure_steps ?? [])
const hasReport = computed(() => Boolean(props.bug?.report_run && props.bug?.report_name))

function attemptText(step: BugFailureStep): string {
  if (!step.attempts) return ""
  return `第 ${step.attempts} 次尝试仍未通过`
}

async function openReport() {
  const bug = props.bug
  if (!bug?.report_run || !bug.report_name) return
  try {
    const content = await fetchTaskReport(bug.report_run, bug.report_name)
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
  <el-drawer
    :model-value="modelValue"
    title="BUG 单详情"
    size="min(520px, 92vw)"
    class="bug-drawer"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <SkeletonCard v-if="loading" variant="list" :lines="6" />

    <EmptyState v-else-if="!bug" icon="🐞" text="没有这张 BUG 单" hint="请关闭后刷新列表" />

    <div v-else class="bug-detail">
      <div class="bug-detail__head">
        <code class="bug-detail__no">{{ bug.bug_no }}</code>
        <span class="bug-badge" :class="bugCategoryClass(bug.category)">
          {{ bug.category_label }}
        </span>
        <span class="bug-status" :class="bugStatusClass(bug.status)">
          {{ bug.status_label }}
        </span>
      </div>

      <h2 class="bug-detail__title">{{ bug.title }}</h2>

      <dl class="bug-meta">
        <dt>关联任务</dt>
        <dd>#{{ bug.task_id }} {{ bug.task_title || "任务已删除" }}</dd>
        <dt>任务状态</dt>
        <dd>{{ bugTaskStatusLabel(bug.task_status) }}</dd>
        <template v-if="bug.case_label">
          <dt>用例</dt>
          <dd>
            {{ bug.case_label }}
            <ul v-if="(bug.case_rows || []).length > 1" class="bug-cases">
              <li v-for="row in bug.case_rows" :key="row.id">
                {{ row.project || "未命名项目" }} / {{ row.title }}
              </li>
            </ul>
          </dd>
        </template>
        <dt>创建时间</dt>
        <dd>{{ formatBugTime(bug.created_at) }}</dd>
        <dt>解决时间</dt>
        <dd>{{ formatBugTime(bug.resolved_at) }}</dd>
      </dl>

      <div class="bug-detail__actions">
        <DoodleBtn v-if="hasReport" tone="teal" @click="openReport">查看报告</DoodleBtn>
        <DoodleBtn
          v-if="bug.status !== 'resolved'"
          tone="teal"
          :disabled="updating"
          @click="emit('status-change', 'resolved')"
        >
          标记已解决
        </DoodleBtn>
        <DoodleBtn
          v-if="bug.status !== 'ignored'"
          tone="yellow"
          :disabled="updating"
          @click="emit('status-change', 'ignored')"
        >
          忽略
        </DoodleBtn>
        <DoodleBtn
          v-if="bug.status !== 'open'"
          tone="paper"
          :disabled="updating"
          @click="emit('status-change', 'open')"
        >
          重新打开
        </DoodleBtn>
      </div>

      <section v-if="steps.length" class="bug-detail__section">
        <h3 class="bug-detail__subtitle">失败步骤</h3>
        <article v-for="(step, index) in steps" :key="step.seq" class="bug-step">
          <details :open="index === 0">
            <summary class="bug-step__summary">第 {{ step.seq }} 步 · {{ step.name }}</summary>
            <dl class="bug-step__facts">
              <dt>出错步骤</dt>
              <dd>第 {{ step.seq }} 步 · {{ step.name }}</dd>
              <dt>原因类别</dt>
              <dd>{{ bugKindLabel(step.kind) }}</dd>
              <dt>期望结果</dt>
              <dd>{{ step.expected || "未记录" }}</dd>
              <dt>实际结果</dt>
              <dd>{{ step.actual || "未记录" }}</dd>
            </dl>
            <p v-if="attemptText(step)" class="bug-step__attempt">{{ attemptText(step) }}</p>
          </details>
        </article>
      </section>

      <section v-else class="bug-detail__section">
        <h3 class="bug-detail__subtitle">错误内容</h3>
        <pre class="bug-detail__body">{{ bug.detail || bug.detail_preview || "—" }}</pre>
      </section>
    </div>
  </el-drawer>
</template>

<style src="./BugDetailDrawer.style.css" scoped></style>
