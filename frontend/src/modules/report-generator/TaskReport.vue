<script setup>
import { computed, onMounted, ref, watch } from "vue"
import { useRoute, useRouter } from "vue-router"
import WorkbenchHeader from "@/shared/components/WorkbenchHeader.vue"
import WorkbenchCrumbs from "@/shared/components/WorkbenchCrumbs.vue"
import ErrorState from "@/shared/components/patterns/ErrorState.vue"
import EmptyState from "@/shared/components/patterns/EmptyState.vue"
import { getTaskReport } from "./api"
import { REPORT_HEADER_GRADIENT, REPORT_HEADER_ICON } from "./constants"

const route = useRoute()
const router = useRouter()
const taskId = computed(() => String(route.params.taskId))

const flow = ref(null)
const loading = ref(false)
const error = ref("")

onMounted(() => loadReport())
watch(taskId, () => loadReport())

async function loadReport() {
  loading.value = true
  error.value = ""
  flow.value = null
  try {
    const { data } = await getTaskReport(taskId.value)
    if (data.status) flow.value = data
    else error.value = data.message || "加载报告失败"
  } catch (e) {
    error.value = e?.response?.data?.message || e?.message || "加载报告失败"
  }
  loading.value = false
}

const task = computed(() => flow.value?.task || null)
const conclusion = computed(() => flow.value?.conclusion || null)
const rounds = computed(() => flow.value?.rounds || [])

function formatDateTime(iso) {
  if (!iso) return "—"
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return String(iso)
  const pad = (n) => String(n).padStart(2, "0")
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

function formatElapsed(start, end) {
  if (!start || !end) return ""
  const ms = new Date(end).getTime() - new Date(start).getTime()
  if (Number.isNaN(ms) || ms < 0) return ""
  const total = Math.floor(ms / 1000)
  const hours = Math.floor(total / 3600)
  const minutes = Math.floor((total % 3600) / 60)
  const seconds = total % 60
  if (hours) return `执行 ${hours}小时${minutes}分${seconds}秒`
  if (minutes) return `执行 ${minutes}分${seconds}秒`
  return `执行 ${seconds}秒`
}

const elapsed = computed(() => formatElapsed(task.value?.started_at, task.value?.finished_at))
const openRounds = ref(new Set())

watch(rounds, (list) => {
  openRounds.value = new Set(list.map((_, index) => index))
})

function taskStatusText(status) {
  const key = String(status || "").toLowerCase()
  if (key === "pending" || key === "paused") return "待执行"
  if (key === "running") return "执行中"
  return "已完成"
}

function roundOpen(index) {
  return openRounds.value.has(index)
}

function toggleRound(index) {
  const next = new Set(openRounds.value)
  if (next.has(index)) next.delete(index)
  else next.add(index)
  openRounds.value = next
}

function phaseClass(phase) {
  if (phase === "开始") return "is-start"
  if (phase === "推理") return "is-reason"
  if (phase === "执行") return "is-execute"
  if (phase === "结束") return "is-end"
  return "is-other"
}
</script>

<template>
  <div v-if="error" class="doc-page wb-shell task-flow-page">
    <WorkbenchHeader
      title="任务报告"
      subtitle="按时间查看智能体事件"
      :icon="REPORT_HEADER_ICON"
      :gradient="REPORT_HEADER_GRADIENT"
    />
    <div class="doc-body">
      <WorkbenchCrumbs
        back-to="/reports"
        back-label="返回列表"
        :items="[{ label: '测试报告', to: '/reports' }, { label: '任务报告' }]"
      />
      <ErrorState :message="error" @retry="loadReport" />
    </div>
  </div>

  <div v-else class="doc-page wb-shell task-flow-page">
    <WorkbenchHeader
      :title="task?.title || '任务报告'"
      subtitle="按时间排列：开始、推理、执行、结束"
      :icon="REPORT_HEADER_ICON"
      :gradient="REPORT_HEADER_GRADIENT"
    />
    <div v-loading="loading" class="doc-body">
      <WorkbenchCrumbs
        back-to="/reports"
        back-label="返回列表"
        :items="[
          { label: '测试报告', to: '/reports' },
          { label: task?.title || '任务报告' },
        ]"
      />

      <section v-if="task" class="flow-meta">
        <span>任务状态 {{ taskStatusText(task.status) }}</span>
        <span v-if="conclusion?.outcome">测试结果 {{ conclusion.outcome }}</span>
        <span>设备 {{ task.device || "—" }}</span>
        <span>用例 {{ task.case_title || "全部" }}</span>
        <span>助手 {{ task.assistant || "—" }}</span>
        <span>{{ formatDateTime(task.started_at) }} → {{ formatDateTime(task.finished_at) }}</span>
        <span v-if="elapsed">{{ elapsed }}</span>
        <span>费用 {{ task.cost_total }}</span>
      </section>

      <section
        v-if="conclusion && (conclusion.outcome || conclusion.verdicts?.length)"
        class="flow-conclusion"
      >
        <div class="flow-conclusion__head">
          <span class="flow-conclusion__label">结论</span>
          <span
            v-if="conclusion.outcome"
            class="badge"
            :class="conclusion.outcome === 'PASS' ? 'badge-pass' : 'badge-fail'"
          >
            {{ conclusion.outcome }}
          </span>
        </div>
        <div class="flow-conclusion__body">
          <p v-for="(verdict, index) in conclusion.verdicts" :key="index" class="flow-conclusion__verdict">
            <span class="flow-conclusion__meta">
              第 {{ verdict.attempt || index + 1 }} 次判决
              {{ verdict.passed ? "PASS" : "FAIL" }}
              <template v-if="verdict.step_seq"> · 步骤 {{ verdict.step_seq }}</template>
              <template v-if="verdict.role_name"> · {{ verdict.role_name }}</template>
            </span>
            {{ verdict.message }}
          </p>
          <p v-if="conclusion.delivery" class="flow-conclusion__delivery">
            交付：{{ conclusion.delivery }}
          </p>
        </div>
      </section>

      <EmptyState
        v-if="task && rounds.length === 0"
        icon="📋"
        text="这次任务还没有事件记录"
        hint="任务跑完后，这里会按时间列出每一轮回复"
      />

      <article v-for="(round, roundIndex) in rounds" :key="roundIndex" class="flow-round">
        <button type="button" class="flow-round__title" @click="toggleRound(roundIndex)">
          <span class="flow-round__mark">{{ roundOpen(roundIndex) ? "▾" : "▸" }}</span>
          第 {{ roundIndex + 1 }} 轮 {{ round.role_name }}
        </button>
        <div v-show="roundOpen(roundIndex)">
        <section
          v-for="(block, blockIndex) in round.blocks"
          :key="`${roundIndex}-${blockIndex}`"
          class="flow-block"
          :class="phaseClass(block.phase)"
        >
          <h4 class="flow-block__title">{{ blockIndex + 1 }}. {{ block.title }}</h4>
          <ol class="flow-list">
            <li v-for="item in block.items" :key="item.seq" class="flow-item">
              <div class="flow-item__head">
                <time>{{ formatDateTime(item.time) }}</time>
                <strong>{{ item.label }}</strong>
                <span v-if="item.count > 1" class="flow-item__count">×{{ item.count }}</span>
                <span v-if="item.step_seq" class="flow-item__step">
                  步骤 {{ item.step_seq }} · 第 {{ item.attempt || 1 }} 次
                </span>
              </div>
              <p v-if="item.detail" class="flow-item__detail">{{ item.detail }}</p>
              <img
                v-if="item.thumb"
                class="flow-item__thumb"
                :src="item.thumb"
                alt="事件缩略图"
              />
            </li>
          </ol>
        </section>
        </div>
      </article>

      <p v-if="!task && !loading" class="flow-missing">
        没有这份报告。
        <button type="button" class="flow-back" @click="router.push('/reports')">返回列表</button>
      </p>
    </div>
  </div>
</template>

<style scoped>
.task-flow-page .doc-body {
  flex: 1 1 0;
  min-height: 0;
  overflow-y: auto;
  padding: var(--app-space-md) var(--app-space-lg) var(--app-space-xl);
}

.flow-meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--app-space-sm) var(--app-space-md);
  align-items: center;
  margin-bottom: var(--app-space-sm);
  padding: var(--app-space-sm) var(--app-space-md);
  border: 2.5px dashed var(--ink);
  border-radius: 6px 10px;
  background: var(--paper);
  box-shadow: var(--app-shadow-sm);
  font-size: var(--app-size-sm);
}

.flow-conclusion {
  margin-bottom: var(--app-space-md);
  padding: var(--app-space-sm) var(--app-space-md);
  border: 2.5px solid var(--ink);
  border-radius: 6px 10px;
  background: var(--paper);
  box-shadow: var(--app-shadow-sm);
}

.flow-conclusion__head {
  display: flex;
  gap: var(--app-space-sm);
  align-items: center;
  margin-bottom: var(--app-space-xs);
}

.flow-conclusion__label {
  font-size: var(--app-size-sm);
  font-weight: 700;
}

.flow-conclusion__verdict,
.flow-conclusion__delivery {
  margin: var(--app-space-xs) 0 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: var(--app-size-sm);
}

.flow-conclusion__body {
  max-height: 25lh;
  overflow: auto;
  font-size: var(--app-size-sm);
  line-height: 1.6;
}

.flow-conclusion__meta {
  display: block;
  margin-bottom: var(--app-space-xs);
  color: var(--app-text-secondary);
  font-size: var(--app-size-xs);
}

.flow-round {
  margin-bottom: var(--app-space-lg);
}

.flow-round__title {
  display: inline-flex;
  align-items: center;
  gap: var(--app-space-xs);
  margin: 0 0 var(--app-space-sm);
  padding: var(--app-space-xs) var(--app-space-sm);
  border: 2.5px solid var(--ink);
  border-radius: 4px 10px 6px 8px;
  background: var(--paper);
  box-shadow: var(--app-shadow-sm);
  color: var(--ink);
  font: inherit;
  font-size: var(--app-size-sm);
  font-weight: 700;
  cursor: pointer;
}

.flow-round__mark {
  font-size: var(--app-size-xs);
}

.flow-block {
  margin-bottom: var(--app-space-sm);
  padding: var(--app-space-sm) var(--app-space-md);
  border: 2.5px solid var(--ink);
  border-radius: 6px 10px;
  background: var(--paper);
}

.flow-block__title {
  margin: 0 0 var(--app-space-sm);
  font-size: var(--app-size-sm);
}

.flow-block.is-start {
  border-color: var(--c-dashboard);
}
.flow-block.is-reason {
  border-color: var(--c-device);
}
.flow-block.is-execute {
  border-color: var(--c-ai);
}
.flow-block.is-end {
  border-color: var(--c-element);
}

.flow-list {
  margin: 0;
  padding: 0;
  list-style: none;
}

.flow-item {
  padding: var(--app-space-xs) 0;
  border-top: 1px dashed var(--ink);
}

.flow-item__head {
  display: flex;
  flex-wrap: wrap;
  gap: var(--app-space-xs) var(--app-space-sm);
  align-items: baseline;
  font-size: var(--app-size-sm);
}

.flow-item__head time,
.flow-item__step {
  color: var(--app-text-secondary);
  font-size: var(--app-size-xs);
}

.flow-item__count {
  font-weight: 700;
}

.flow-item__detail {
  margin: var(--app-space-xs) 0 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: var(--app-size-sm);
}

.flow-item__thumb {
  display: block;
  max-width: 240px;
  margin-top: var(--app-space-xs);
  border: 2.5px solid var(--ink);
  border-radius: 4px 8px;
}

.flow-missing {
  font-size: var(--app-size-sm);
}

.flow-back {
  margin-left: var(--app-space-xs);
  font: inherit;
  cursor: pointer;
  border: 2px solid var(--ink);
  border-radius: 4px 8px;
  background: var(--paper);
}

.badge {
  display: inline-block;
  padding: 0 var(--app-space-xs);
  border: 2px solid var(--ink);
  border-radius: 4px 8px;
  font-size: var(--app-size-xs);
  font-weight: 700;
}
.badge-pass {
  background: var(--app-status-success-bg);
}
.badge-fail {
  background: var(--c-runner);
}
</style>
