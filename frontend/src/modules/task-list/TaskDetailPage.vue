<script setup>
import { computed, onMounted, onUnmounted, reactive, ref, watch } from "vue"
import { useRoute, useRouter } from "vue-router"
import WorkbenchHeader from "@/shared/components/WorkbenchHeader.vue"
import WorkbenchCrumbs from "@/shared/components/WorkbenchCrumbs.vue"
import ErrorState from "@/shared/components/patterns/ErrorState.vue"
import EmptyState from "@/shared/components/patterns/EmptyState.vue"
import SkeletonCard from "@/shared/components/patterns/SkeletonCard.vue"
import { getTaskReport } from "./api/tasks"
import TaskMediaThumb from "./components/TaskMediaThumb.vue"
import CaseImportCard from "./components/CaseImportCard.vue"
import {
  executorRoundNumbers,
  reportPageCount,
  reportPageSlice,
  roundTitleLead,
  roundTitleTail,
} from "./helpers/task-detail"
import {
  CASE_EVENT_POLL_MS,
  DEFAULT_OPEN_CASE_INDEX,
  ROUNDS_PER_PAGE,
  TASK_REPORT_HEADER_GRADIENT,
  TASK_REPORT_HEADER_ICON,
} from "./constants"

const route = useRoute()
const router = useRouter()
const taskId = computed(() => String(route.params.id))

const flow = ref(null)
const loading = ref(false)
const error = ref("")

onMounted(() => loadReport())
watch(taskId, () => loadReport())
onUnmounted(stopPoll)

let pollTimer = null

function stopPoll() {
  if (pollTimer) {
    clearTimeout(pollTimer)
    pollTimer = null
  }
}

function schedulePoll() {
  stopPoll()
  if (task.value?.task_kind !== "case_authoring") return
  if (task.value?.status !== "running" && task.value?.status !== "pending") return
  pollTimer = setTimeout(() => loadReport(false), CASE_EVENT_POLL_MS)
}

async function loadReport(initial = true) {
  if (initial) {
    loading.value = true
    error.value = ""
    flow.value = null
    stopPoll()
  }
  try {
    const payload = await getTaskReport(Number(taskId.value))
    if (payload.status) {
      flow.value = payload.data
      error.value = ""
    } else if (initial) {
      error.value = payload.message || "加载报告失败"
    }
  } catch (e) {
    if (initial) error.value = e?.response?.data?.message || e?.message || "加载报告失败"
  }
  if (initial) loading.value = false
  schedulePoll()
}

const task = computed(() => flow.value?.task || null)
const conclusion = computed(() => flow.value?.conclusion || null)
const rounds = computed(() => flow.value?.rounds || [])
const cases = computed(() => flow.value?.cases || [])
const isCaseAuthoring = computed(() => task.value?.task_kind === "case_authoring")
const isRunning = computed(
  () => task.value?.status === "running" || task.value?.status === "pending",
)
const caseImport = computed(() => flow.value?.case_import || null)
const caseVerdicts = computed(() => conclusion.value?.verdicts || [])
const caseEvents = computed(() => flow.value?.events || [])
const expandedEvents = ref(new Set())

function eventExpanded(index) {
  return expandedEvents.value.has(index)
}

function toggleEvent(index) {
  const next = new Set(expandedEvents.value)
  if (next.has(index)) next.delete(index)
  else next.add(index)
  expandedEvents.value = next
}

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
const openCases = ref(new Set([DEFAULT_OPEN_CASE_INDEX]))
const openRounds = ref(new Set())
const casePages = reactive({})

watch(cases, () => {
  openCases.value = new Set([DEFAULT_OPEN_CASE_INDEX])
  openRounds.value = new Set()
  for (const key of Object.keys(casePages)) delete casePages[key]
})

/** 轮次编号 → 轮次对象；用例只存 round_ids，避免复制整份轮次。 */
const roundsById = computed(() => {
  const map = new Map()
  for (const round of rounds.value) map.set(round.round_id, round)
  return map
})

/** 某用例按 round_ids 取到的轮次，顺序与接口一致。 */
function caseRounds(caseItem) {
  const picked = []
  for (const roundId of caseItem?.round_ids || []) {
    const round = roundsById.value.get(roundId)
    if (round) picked.push(round)
  }
  return picked
}

/** 轮次编号 → 执行步骤序号；验收轮不入表，号在整份用例上算，换页不跳号。 */
const execNoById = computed(() => {
  const map = new Map()
  for (const caseItem of cases.value) {
    for (const [roundId, no] of executorRoundNumbers(caseRounds(caseItem))) map.set(roundId, no)
  }
  return map
})

function pageCount(caseItem) {
  return reportPageCount(caseRounds(caseItem).length, ROUNDS_PER_PAGE)
}

function pageOf(caseIndex) {
  return casePages[caseIndex] || 1
}

function pagedRounds(caseIndex, caseItem) {
  return reportPageSlice(caseRounds(caseItem), pageOf(caseIndex), ROUNDS_PER_PAGE)
}

function setPage(caseIndex, page, total) {
  casePages[caseIndex] = Math.min(Math.max(1, page), total)
}

function taskStatusText(status) {
  const key = String(status || "").toLowerCase()
  if (key === "pending" || key === "paused") return "待执行"
  if (key === "running") return "执行中"
  if (key === "failed") return "失败"
  if (key === "interrupted") return "已中断"
  if (key === "cancelled") return "已取消"
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

/** 角色类别对应的配色类（执行 / 验收两色，与左侧强调色同源）。 */
function roundKindClass(round) {
  return round?.role_kind === "verifier" ? "is-verifier" : "is-executor"
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
        back-label="返回任务清单"
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
        back-label="返回任务清单"
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

        <template v-if="isCaseAuthoring">
          <CaseImportCard :case-import="caseImport" :is-running="isRunning" />
          <section v-if="caseEvents.length || isRunning" class="flow-case-notes">
            <h2 class="flow-section-title">
              模型事件流
              <span v-if="isRunning" class="flow-live">运行中，自动刷新…</span>
            </h2>
            <p v-if="caseEvents.length" class="flow-verdict-summary">
              共 {{ caseEvents.length }} 条事件，按时间顺序；长文本在框内滚动查看
            </p>
            <p v-else class="flow-verdict-summary">模型正在运行，事件写入后会自动出现…</p>
            <article
              v-for="(event, index) in caseEvents"
              :key="event.seq || index"
              class="flow-event"
            >
              <div class="flow-event__head">
                <time>{{ formatDateTime(event.time) }}</time>
                <span
                  class="badge badge-role"
                  :class="event.role_kind === 'verifier' ? 'is-verifier' : 'is-executor'"
                >
                  {{ event.role_name || "系统" }}
                </span>
                <strong class="flow-event__label">{{ event.label || event.event_type }}</strong>
                <span v-if="event.model" class="flow-event__model">{{ event.model }}</span>
                <span v-if="event.status" class="badge">{{ event.status }}</span>
                <span v-if="event.count > 1" class="flow-event__count">×{{ event.count }}</span>
              </div>
              <pre
                v-if="event.detail"
                class="flow-event__detail"
                :class="{ 'is-expanded': eventExpanded(index) }"
                >{{ event.detail }}</pre>
              <button
                v-if="event.detail && event.detail.length > 600"
                type="button"
                class="flow-event__toggle"
                @click="toggleEvent(index)"
              >
                {{ eventExpanded(index) ? "收起" : "展开全文" }}
              </button>
            </article>
          </section>
          <section v-if="caseVerdicts.length" class="flow-case-notes">
            <h2 class="flow-section-title">验收意见</h2>
            <p class="flow-verdict-summary">
              <span
                class="badge"
                :class="conclusion?.outcome === 'PASS' ? 'badge-pass' : 'badge-fail'"
              >
                最终 {{ conclusion?.outcome || "—" }}
              </span>
              共 {{ caseVerdicts.length }} 次判决，按时间顺序：
            </p>
            <article v-for="(verdict, index) in caseVerdicts" :key="index" class="flow-note-row">
              <span class="badge" :class="verdict.passed ? 'badge-pass' : 'badge-fail'">
                第 {{ index + 1 }} 次 · {{ verdict.passed ? "通过" : "驳回" }}
              </span>
              <p class="flow-note">{{ verdict.message || "—" }}</p>
            </article>
          </section>
        </template>
        <template v-else>
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
            <div v-if="caseOpen(caseIndex)" class="flow-case__body">
              <article
                v-for="(round, roundIndex) in pagedRounds(caseIndex, caseItem)"
                :key="roundKey(caseIndex, round.round_id)"
                class="flow-round"
              >
                <button
                  type="button"
                  class="flow-round__title"
                  :class="roundKindClass(round)"
                  @click="toggleRound(roundKey(caseIndex, round.round_id))"
                >
                  <span class="flow-round__mark">{{
                    roundOpen(roundKey(caseIndex, round.round_id)) ? "▾" : "▸"
                  }}</span>
                  <span class="flow-round__text"
                    >{{ roundTitleLead(round, execNoById.get(round.round_id))
                    }}<span
                      v-if="round.role"
                      class="badge badge-role"
                      :class="roundKindClass(round)"
                      >{{ round.role }}</span
                    >{{ roundTitleTail(round) }}</span
                  >
                </button>
                <div v-if="roundOpen(roundKey(caseIndex, round.round_id))" class="flow-round__body">
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
                        <TaskMediaThumb
                          v-if="item.media_id"
                          :task-id="Number(taskId)"
                          :media-id="item.media_id"
                        />
                      </div>
                    </li>
                  </ol>
                </div>
              </article>
              <div v-if="pageCount(caseItem) > 1" class="flow-pager">
                <button
                  type="button"
                  :disabled="pageOf(caseIndex) <= 1"
                  @click="setPage(caseIndex, pageOf(caseIndex) - 1, pageCount(caseItem))"
                >
                  上一页
                </button>
                <span>第 {{ pageOf(caseIndex) }} / {{ pageCount(caseItem) }} 页</span>
                <button
                  type="button"
                  :disabled="pageOf(caseIndex) >= pageCount(caseItem)"
                  @click="setPage(caseIndex, pageOf(caseIndex) + 1, pageCount(caseItem))"
                >
                  下一页
                </button>
              </div>
            </div>
          </section>
        </template>
      </template>

      <p v-if="!task && !loading" class="flow-missing">
        没有这份报告。
        <button type="button" class="flow-back" @click="router.push('/tasks')">返回任务清单</button>
      </p>
    </div>
  </div>
</template>

<style src="./TaskDetailPage.style.css" scoped></style>
