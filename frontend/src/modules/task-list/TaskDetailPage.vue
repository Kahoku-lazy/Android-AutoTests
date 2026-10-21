<script setup>
import { computed, onMounted, ref, watch } from "vue"
import { useRoute, useRouter } from "vue-router"
import WorkbenchHeader from "@/shared/components/WorkbenchHeader.vue"
import WorkbenchCrumbs from "@/shared/components/WorkbenchCrumbs.vue"
import ErrorState from "@/shared/components/patterns/ErrorState.vue"
import EmptyState from "@/shared/components/patterns/EmptyState.vue"
import SkeletonCard from "@/shared/components/patterns/SkeletonCard.vue"
import { getTaskReport } from "./api/tasks"
import { TASK_REPORT_HEADER_GRADIENT, TASK_REPORT_HEADER_ICON } from "./constants"

const route = useRoute()
const router = useRouter()
const taskId = computed(() => String(route.params.id))

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
    const payload = await getTaskReport(Number(taskId.value))
    if (payload.status) flow.value = payload
    else error.value = payload.message || "加载报告失败"
  } catch (e) {
    error.value = e?.response?.data?.message || e?.message || "加载报告失败"
  }
  loading.value = false
}

const task = computed(() => flow.value?.task || null)
const conclusion = computed(() => flow.value?.conclusion || null)
const rounds = computed(() => flow.value?.rounds || [])
const cases = computed(() => flow.value?.cases || [])

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
const openCases = ref(new Set())
const openRounds = ref(new Set())

watch(cases, (list) => {
  openCases.value = new Set(list.map((_, index) => index))
  openRounds.value = new Set()
})

function taskStatusText(status) {
  const key = String(status || "").toLowerCase()
  if (key === "pending" || key === "paused") return "待执行"
  if (key === "running") return "执行中"
  return "已完成"
}

function caseOpen(index) {
  return openCases.value.has(index)
}

function toggleCase(index) {
  const next = new Set(openCases.value)
  if (next.has(index)) next.delete(index)
  else next.add(index)
  openCases.value = next
}

const STEP_CN = ["", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]

function stepName(seq) {
  const num = Number(seq)
  if (!num) return "步骤"
  if (num <= 10) return `步骤${STEP_CN[num]}`
  if (num < 20) return `步骤十${STEP_CN[num - 10]}`
  const tens = Math.floor(num / 10)
  const ones = num % 10
  if (num < 100) return `步骤${STEP_CN[tens]}十${ones ? STEP_CN[ones] : ""}`
  return `步骤${num}`
}

function roundTitle(round) {
  const kind =
    round.role_kind === "verifier"
      ? "验收模型"
      : round.role_kind === "planner"
        ? "规划模型"
        : "执行模型"
  const who = [round.role, round.model].filter(Boolean).join(" · ")
  const retry = Number(round.attempt) > 1 ? `第 ${round.attempt} 次 ` : ""
  const subject = round.subject ? `：${round.subject}` : ""
  return `${stepName(round.step_seq)} ${retry}${kind}${who ? ` ${who}` : ""}${subject}`
}

function leadCount(round) {
  return (round.handover ? 1 : 0) + (round.verdict ? 1 : 0)
}

function blockNo(round, blockIndex) {
  return leadCount(round) + blockIndex + 1
}

function roundKey(caseIndex, roundIndex) {
  return `${caseIndex}-${roundIndex}`
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

function outcomeClass(outcome) {
  if (outcome === "PASS") return "badge-pass"
  if (outcome === "FAIL") return "badge-fail"
  return "badge-pending"
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
      title="任务详情"
      subtitle="按时间查看智能体事件"
      :icon="TASK_REPORT_HEADER_ICON"
      :gradient="TASK_REPORT_HEADER_GRADIENT"
    />
    <div class="doc-body">
      <WorkbenchCrumbs
        back-to="/tasks"
        back-label="返回列表"
        :items="[{ label: '任务清单', to: '/tasks' }, { label: '任务详情' }]"
      />
      <ErrorState :message="error" @retry="loadReport" />
    </div>
  </div>

  <div v-else class="doc-page wb-shell task-flow-page">
    <WorkbenchHeader
      :title="task?.title || '任务详情'"
      subtitle="查看任务执行、验收与结论"
      :icon="TASK_REPORT_HEADER_ICON"
      :gradient="TASK_REPORT_HEADER_GRADIENT"
    />
    <div class="doc-body">
      <WorkbenchCrumbs
        back-to="/tasks"
        back-label="返回列表"
        :items="[{ label: '任务清单', to: '/tasks' }, { label: task?.title || '任务详情' }]"
      />

      <SkeletonCard v-if="loading && !task" variant="list" :lines="6" />

      <template v-else-if="task">
        <section class="flow-summary" aria-label="任务详情摘要">
          <div class="flow-fact">
            <p class="flow-fact__label">1. 任务结果</p>
            <p class="flow-fact__value">任务状态：{{ taskStatusText(task.status) }}</p>
            <p class="flow-fact__extra">
              测试结果：
              <span class="badge" :class="outcomeClass(conclusion?.outcome)">{{
                conclusion?.outcome || "—"
              }}</span>
            </p>
          </div>
          <div class="flow-fact">
            <p class="flow-fact__label">2. 任务执行时间</p>
            <p class="flow-fact__value">{{ elapsed || "—" }}</p>
            <p class="flow-fact__extra">
              {{ formatDateTime(task.started_at) }} → {{ formatDateTime(task.finished_at) }}
            </p>
          </div>
          <div class="flow-fact">
            <p class="flow-fact__label">3. 执行环境</p>
            <p class="flow-fact__value">{{ task.assistant || "—" }}</p>
            <p class="flow-fact__extra">设备：{{ task.device || "—" }}</p>
          </div>
          <div class="flow-fact">
            <p class="flow-fact__label">4. 费用</p>
            <p class="flow-fact__value">{{ task.cost_total }} 元</p>
          </div>
        </section>

        <h2 class="flow-section-title">用例执行详情</h2>

        <EmptyState
          v-if="cases.length === 0 && rounds.length === 0"
          icon="📋"
          text="这次任务还没有事件记录"
          hint="任务跑完后，这里会按用例和步骤展开"
        />

        <section v-for="(caseItem, caseIndex) in cases" :key="caseIndex" class="flow-case">
          <button type="button" class="flow-case__title" @click="toggleCase(caseIndex)">
            <span class="flow-round__mark">{{ caseOpen(caseIndex) ? "▾" : "▸" }}</span>
            <span class="flow-case__name"
              >{{ caseIndex + 1 }}. 测试用例：{{ caseItem.title || "未命名用例" }}</span
            >
            <span class="badge" :class="outcomeClass(caseItem.outcome)">{{
              caseItem.outcome
            }}</span>
          </button>
          <div v-show="caseOpen(caseIndex)" class="flow-case__body">
            <article
              v-for="(round, roundIndex) in caseItem.rounds"
              :key="roundKey(caseIndex, roundIndex)"
              class="flow-round"
            >
              <button
                type="button"
                class="flow-round__title"
                :class="round.role_kind === 'verifier' ? 'is-verifier' : 'is-executor'"
                @click="toggleRound(roundKey(caseIndex, roundIndex))"
              >
                <span class="flow-round__mark">{{
                  roundOpen(roundKey(caseIndex, roundIndex)) ? "▾" : "▸"
                }}</span>
                <span
                  v-if="round.verdict"
                  class="badge"
                  :class="round.verdict.passed ? 'badge-pass' : 'badge-fail'"
                >
                  {{ round.verdict.passed ? "PASS" : "FAIL" }}
                </span>
                <span class="flow-round__text">{{ roundIndex + 1 }}. {{ roundTitle(round) }}</span>
              </button>
              <div v-show="roundOpen(roundKey(caseIndex, roundIndex))" class="flow-round__body">
                <section v-if="round.handover" class="flow-lead is-handover">
                  <h4 class="flow-lead__title">交付</h4>
                  <p class="flow-note">{{ round.handover }}</p>
                </section>
                <section v-if="round.verdict" class="flow-lead is-verdict">
                  <h4 class="flow-lead__title">结论</h4>
                  <p class="flow-note">{{ round.verdict.message }}</p>
                </section>
                <ol class="flow-timeline">
                  <li
                    v-for="(block, blockIndex) in round.blocks"
                    :key="`${caseIndex}-${roundIndex}-${blockIndex}`"
                    class="flow-phase"
                    :class="phaseClass(block.phase)"
                  >
                    <h4 class="flow-phase__title">
                      {{ blockNo(round, blockIndex) }}. {{ block.title }}
                    </h4>
                    <div v-for="item in block.items" :key="item.seq" class="flow-item">
                      <div class="flow-item__head">
                        <time>{{ formatDateTime(item.time) }}</time>
                        <strong>{{ item.label }}</strong>
                        <span v-if="item.count > 1" class="flow-item__count"
                          >×{{ item.count }}</span
                        >
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
                    </div>
                  </li>
                </ol>
              </div>
            </article>
          </div>
        </section>
      </template>

      <p v-if="!task && !loading" class="flow-missing">
        没有这份报告。
        <button type="button" class="flow-back" @click="router.push('/tasks')">返回任务清单</button>
      </p>
    </div>
  </div>
</template>

<style src="./TaskDetailPage.style.css" scoped></style>
