<script setup lang="ts">
/** BUG 单详情抽屉 — 只渲染详情与状态操作，数据加载由列表页负责。 */
import SkeletonCard from "@/shared/components/patterns/SkeletonCard.vue"
import EmptyState from "@/shared/components/patterns/EmptyState.vue"
import DoodleBtn from "@/shared/components/DoodleBtn.vue"
import {
  bugCategoryClass,
  bugStatusClass,
  bugTaskRoute,
  bugTaskStatusLabel,
  formatBugTime,
} from "../constants"
import type { BugStatus, BugTicket } from "../types"

defineProps<{
  modelValue: boolean
  bug: BugTicket | null
  loading: boolean
  updating: boolean
}>()

const emit = defineEmits<{
  "update:modelValue": [value: boolean]
  "status-change": [status: BugStatus]
}>()
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
        <dd>
          <router-link :to="bugTaskRoute(bug.task_id)" class="bug-task-link">
            #{{ bug.task_id }} {{ bug.task_title || "任务已删除" }}
          </router-link>
        </dd>
        <dt>任务状态</dt>
        <dd>{{ bugTaskStatusLabel(bug.task_status) }}</dd>
        <dt>创建时间</dt>
        <dd>{{ formatBugTime(bug.created_at) }}</dd>
        <dt>解决时间</dt>
        <dd>{{ formatBugTime(bug.resolved_at) }}</dd>
      </dl>

      <div class="bug-detail__actions">
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

      <section class="bug-detail__section">
        <h3 class="bug-detail__subtitle">错误内容</h3>
        <pre class="bug-detail__body">{{ bug.detail || bug.detail_preview || "—" }}</pre>
      </section>
    </div>
  </el-drawer>
</template>

<style src="./BugDetailDrawer.style.css" scoped></style>
