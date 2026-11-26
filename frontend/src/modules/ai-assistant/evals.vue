<script setup lang="ts">
import { computed, onMounted, ref } from "vue"
import { ElMessage } from "element-plus"
import { useRouter } from "vue-router"
import AppTable from "@/shared/components/AppTable.vue"
import DoodleBtn from "@/shared/components/DoodleBtn.vue"
import FilterTabs from "@/shared/components/FilterTabs.vue"
import WorkbenchCrumbs from "@/shared/components/WorkbenchCrumbs.vue"
import WorkbenchHeader from "@/shared/components/WorkbenchHeader.vue"
import EmptyState from "@/shared/components/patterns/EmptyState.vue"
import ErrorState from "@/shared/components/patterns/ErrorState.vue"
import SkeletonCard from "@/shared/components/patterns/SkeletonCard.vue"
import { formatApiError } from "@/shared/api-client"
import { formatDateTime } from "@/shared/helpers/datetime"
import {
  fetchEvalReport,
  fetchEvalCandidates,
  fetchEvalCases,
  fetchEvalMethods,
  fetchEvalScores,
  fetchSuiteRuns,
  listAssistants,
  listSopWorkflows,
  publishAssistant,
  publishWorkflow,
  runEval,
  runSuiteEval,
  type EvalCandidate,
  type EvalCase,
  type EvalMethod,
  type EvalScore,
  type EvalSuiteRun,
} from "./api/assistants"
import {
  candidateLabel,
  caseRows,
  historyRows,
  kindTabViews,
  methodViews,
  missingNotes,
  scoreCards,
  scoreText,
  suiteRows,
  trendPoints,
} from "./helpers/eval-view"
import type { AssistantCard, SopWorkflow } from "./types"
import {
  EVAL_CASE_COLUMNS,
  EVAL_CRUMBS,
  EVAL_HISTORY_COLUMNS,
  EVAL_SUITE_COLUMNS,
} from "./constants"

const router = useRouter()
const assistants = ref<AssistantCard[]>([])
const workflows = ref<SopWorkflow[]>([])
const kind = ref<"assistant" | "workflow">("assistant")
const targetId = ref("")
const sourceRef = ref("")
const loading = ref(false)
const loaded = ref(false)
const running = ref(false)
const publishing = ref(false)
const listError = ref("")
const candidates = ref<EvalCandidate[]>([])
const history = ref<EvalScore[]>([])
const latest = ref<EvalScore | null>(null)
const methods = ref<EvalMethod[]>([])
const cases = ref<EvalCase[]>([])
const picked = ref<string[]>([])
const serial = ref("")
const suiteRuns = ref<EvalSuiteRun[]>([])
const boardId = ref(0)

async function showBoard(runId: number): Promise<void> {
  boardId.value = runId
  if (boardUrl.value.startsWith("blob:")) URL.revokeObjectURL(boardUrl.value)
  boardUrl.value = ""
  if (!runId) return
  const html = await fetchEvalReport(runId)
  boardUrl.value = URL.createObjectURL(new Blob([html], { type: "text/html" }))
}
const methodsOpen = ref(false)

const options = computed(() =>
  kind.value === "assistant"
    ? assistants.value.map((item) => ({ id: item.assistant_id, label: item.display_name }))
    : workflows.value.map((item) => ({ id: String(item.id), label: item.name })),
)

const kindTabs = computed(() => kindTabViews(assistants.value.length, workflows.value.length))

const cards = computed(() => scoreCards(latest.value?.items || []))
const missing = computed(() => missingNotes(latest.value))
const historyTable = computed(() => historyRows(history.value))
const caseTable = computed(() => caseRows(cases.value))
const suiteTable = computed(() => suiteRows(suiteRuns.value[0] || null))
const trend = computed(() => trendPoints(history.value))
const methodList = computed(() => methodViews(methods.value))
const boardUrl = ref("")
const latestAt = computed(() =>
  latest.value ? formatDateTime(latest.value.created_at, { precision: "minute" }) : "",
)

const targetState = computed(() => {
  if (kind.value === "assistant") {
    return (
      assistants.value.find((item) => item.assistant_id === targetId.value)?.release_state || ""
    )
  }
  return workflows.value.find((item) => String(item.id) === targetId.value)?.release_state || ""
})

const targetStateText = computed(() => {
  if (targetState.value === "draft") return "草稿"
  if (targetState.value === "published") return "已发布"
  return ""
})

async function load(): Promise<void> {
  loading.value = true
  listError.value = ""
  try {
    ;[assistants.value, workflows.value, methods.value, cases.value] = await Promise.all([
      listAssistants(),
      listSopWorkflows(),
      fetchEvalMethods(),
      fetchEvalCases(),
    ])
    loaded.value = true
  } catch (cause) {
    listError.value = formatApiError(cause as never, "评测对象加载失败")
  } finally {
    loading.value = false
  }
}

function onKindChange(next: string): void {
  switchKind(next === "workflow" ? "workflow" : "assistant")
}

function switchKind(next: "assistant" | "workflow"): void {
  kind.value = next
  targetId.value = ""
  sourceRef.value = ""
  candidates.value = []
  history.value = []
  latest.value = null
  picked.value = []
  suiteRuns.value = []
  boardId.value = 0
  if (boardUrl.value.startsWith("blob:")) URL.revokeObjectURL(boardUrl.value)
  boardUrl.value = ""
}

async function refreshTarget(): Promise<void> {
  candidates.value = []
  history.value = []
  latest.value = null
  suiteRuns.value = []
  picked.value = []
  sourceRef.value = ""
  if (boardUrl.value.startsWith("blob:")) URL.revokeObjectURL(boardUrl.value)
  boardUrl.value = ""
  boardId.value = 0
  if (!targetId.value) return
  try {
    ;[candidates.value, history.value, suiteRuns.value] = await Promise.all([
      fetchEvalCandidates(kind.value, targetId.value),
      fetchEvalScores(kind.value, targetId.value),
      fetchSuiteRuns(`${kind.value}:${targetId.value}`),
    ])
    await showBoard(suiteRuns.value[0]?.id || history.value[0]?.id || 0)
    if (history.value.length > 0) latest.value = history.value[0]
    if (candidates.value.length > 0) sourceRef.value = candidates.value[0].source_ref
  } catch (cause) {
    ElMessage.error(formatApiError(cause as never, "运行产物加载失败"))
  }
}

async function start(): Promise<void> {
  if (!targetId.value || running.value) return
  running.value = true
  try {
    latest.value = await runEval(kind.value, targetId.value, sourceRef.value)
    history.value = await fetchEvalScores(kind.value, targetId.value)
    await showBoard(latest.value.id)
  } catch (cause) {
    ElMessage.error(formatApiError(cause as never, "评分失败"))
  } finally {
    running.value = false
  }
}

async function startSuite(): Promise<void> {
  if (!targetId.value || picked.value.length === 0 || !serial.value || running.value) return
  running.value = true
  try {
    const run = await runSuiteEval({
      target_kind: kind.value,
      target_id: targetId.value,
      case_ids: picked.value,
      serial: serial.value,
    })
    await showBoard(run.id)
    suiteRuns.value = await fetchSuiteRuns(`${kind.value}:${targetId.value}`)
  } catch (cause) {
    ElMessage.error(formatApiError(cause as never, "真题评测失败"))
  } finally {
    running.value = false
  }
}

function togglePick(caseId: number): void {
  const key = String(caseId)
  picked.value = picked.value.includes(key)
    ? picked.value.filter((item) => item !== key)
    : [...picked.value, key]
}

function markPublished(): void {
  if (kind.value === "assistant") {
    const item = assistants.value.find((row) => row.assistant_id === targetId.value)
    if (item) item.release_state = "published"
    return
  }
  const item = workflows.value.find((row) => String(row.id) === targetId.value)
  if (item) item.release_state = "published"
}

async function publish(): Promise<void> {
  if (!targetId.value || publishing.value) return
  publishing.value = true
  try {
    if (kind.value === "assistant") await publishAssistant(targetId.value)
    else await publishWorkflow(Number(targetId.value))
    markPublished()
    ElMessage.success("已发布")
  } catch (cause) {
    ElMessage.error(formatApiError(cause as never, "发布失败"))
  } finally {
    publishing.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="doc-page doc-page--fixed wb-shell eval-page">
    <WorkbenchHeader title="评测" icon="bot" />
    <div class="doc-body">
      <WorkbenchCrumbs :items="EVAL_CRUMBS" back-to="/ai-assistant" back-label="返回助手" />

      <ErrorState v-if="listError" :message="listError" @retry="load" />
      <SkeletonCard v-else-if="loading && !loaded" variant="list" :lines="4" />

      <template v-else>
        <div class="eval-bar">
          <FilterTabs :model-value="kind" :tabs="kindTabs" @update:model-value="onKindChange" />
          <label class="eval-field">
            <span>评测对象</span>
            <el-select
              v-model="targetId"
              class="eval-field__control"
              placeholder="请选择评测对象"
              @change="refreshTarget"
            >
              <el-option
                v-for="item in options"
                :key="item.id"
                :label="item.label"
                :value="item.id"
              />
            </el-select>
          </label>
          <label v-if="targetId" class="eval-field">
            <span>交接文本来源</span>
            <el-select v-model="sourceRef" class="eval-field__control">
              <el-option label="不评交接文本" value="" />
              <el-option
                v-for="item in candidates"
                :key="item.source_ref"
                :label="candidateLabel(item)"
                :value="item.source_ref"
              />
            </el-select>
          </label>
          <div class="eval-bar__tail">
            <span v-if="targetStateText" class="eval-chip">{{ targetStateText }}</span>
            <DoodleBtn tone="paper" @click="router.push('/ai-assistant/eval-cases')"
              >编辑题库</DoodleBtn
            >
            <DoodleBtn tone="yellow" :disabled="!targetId || running" @click="start">
              {{ running ? "评分中…" : "开始评分" }}
            </DoodleBtn>
          </div>
        </div>

        <EmptyState
          v-if="options.length === 0"
          icon="🧪"
          text="还没有可评测的对象"
          hint="先新建一条助手或工作流"
        />
        <EmptyState
          v-else-if="!targetId"
          icon="🧪"
          text="先选一个评测对象"
          hint="选完才会出现评分结果、真题集与历史；评测口径默认收起"
        />

        <template v-else>
          <section class="doc-section">
            <div class="doc-section__header">
              <h3 class="doc-section__title">
                评分结果
                <span class="doc-tag">{{ latest ? latest.judge_model : "未评分" }}</span>
              </h3>
              <div class="eval-actions">
                <span class="eval-meta">{{ latest ? `评分于 ${latestAt}` : "还没有评分" }}</span>
                <DoodleBtn
                  v-if="targetStateText === '草稿'"
                  tone="teal"
                  :disabled="publishing"
                  @click="publish"
                >
                  {{ publishing ? "发布中…" : "发布" }}
                </DoodleBtn>
              </div>
            </div>

            <div v-if="cards.length" class="eval-scores">
              <article
                v-for="card in cards"
                :key="card.key"
                class="eval-score"
                :style="{ '--score-tone': `var(${card.tone})` }"
              >
                <header>
                  <b>{{ card.label }}</b>
                  <span v-if="card.warning" class="eval-chip eval-chip--warn">{{
                    card.warning
                  }}</span>
                </header>
                <strong class="eval-score__num">{{ card.text }}</strong>
                <p class="eval-score__reason">{{ card.reason }}</p>
              </article>
            </div>
            <p v-else class="eval-hint">
              选好对象与交接文本来源后点「开始评分」，这里会出现两项分数与理由。
            </p>

            <p v-for="note in missing" :key="note.key" class="eval-hint eval-hint--warn">
              {{ note.label }} 未评分：{{ note.reason }}
            </p>
            <p v-if="latest" class="eval-meta">提示词指纹 {{ latest.prompt_fingerprint }}</p>
          </section>

          <section class="doc-section">
            <div class="doc-section__header">
              <h3 class="doc-section__title">
                真题集 <span class="doc-tag">共 {{ cases.length }} 条</span>
              </h3>
              <div class="eval-actions">
                <label class="eval-field eval-field--inline">
                  <span>设备串号</span>
                  <el-input
                    v-model="serial"
                    class="eval-field__control"
                    placeholder="例如 H6810-0207"
                  />
                </label>
                <DoodleBtn
                  tone="teal"
                  :disabled="running || picked.length === 0"
                  @click="startSuite"
                >
                  {{ running ? "评测中…" : "跑真题" }}
                </DoodleBtn>
              </div>
            </div>

            <EmptyState
              v-if="!caseTable.length"
              icon="🧾"
              text="题库里还没有题目"
              hint="去「编辑题库」新增题目后，这里才能勾选并执行"
            />
            <AppTable
              v-else
              :columns="EVAL_CASE_COLUMNS"
              :data-source="caseTable"
              row-key="id"
              table-layout="fixed"
              accent="var(--c-case)"
            >
              <template #cell-pick="{ record }">
                <el-checkbox
                  :model-value="picked.includes(String(record.id))"
                  @update:model-value="togglePick(record.id)"
                />
              </template>
            </AppTable>

            <template v-if="suiteTable.length">
              <h4 class="eval-subtitle">最近一次逐条结果</h4>
              <AppTable
                :columns="EVAL_SUITE_COLUMNS"
                :data-source="suiteTable"
                row-key="id"
                table-layout="fixed"
                accent="var(--c-case)"
              >
                <template #cell-verdict="{ record }">
                  <span class="eval-chip" :class="{ 'eval-chip--warn': record.verdict !== '达成' }">
                    {{ record.verdict }}
                  </span>
                </template>
              </AppTable>
            </template>

            <div v-if="boardUrl" class="eval-board">
              <h4 class="eval-subtitle">评测看板</h4>
              <iframe class="eval-board__frame" :src="boardUrl" title="评测看板" />
            </div>
          </section>

          <section class="doc-section">
            <div class="doc-section__header">
              <h3 class="doc-section__title">
                历史评分 <span class="doc-tag">共 {{ historyTable.length }} 次</span>
              </h3>
            </div>

            <div v-if="trend.length > 1" class="eval-trend" aria-hidden="true">
              <span
                v-for="point in trend"
                :key="point.id"
                class="eval-trend__bar"
                :style="{ height: `${Math.round(point.score * 100)}%` }"
                :title="`${point.label} ${scoreText(point.score)}`"
              />
            </div>

            <AppTable
              v-if="historyTable.length"
              :columns="EVAL_HISTORY_COLUMNS"
              :data-source="historyTable"
              row-key="id"
              table-layout="fixed"
              accent="var(--c-case)"
            >
              <template #cell-metrics="{ record }">
                <span v-for="chip in record.metrics" :key="chip.key" class="eval-chip">
                  {{ chip.label }} {{ chip.text }}
                </span>
              </template>
              <template #cell-fingerprint="{ record }">
                <span class="eval-fingerprint">{{ record.fingerprint }}</span>
              </template>
            </AppTable>
            <EmptyState
              v-else
              icon="🗂️"
              text="还没有历史评分"
              hint="评一次分后，这里按时间倒序列出每次的分值"
            />
          </section>

          <section class="doc-section eval-fold">
            <button
              type="button"
              class="eval-fold__head"
              :aria-expanded="methodsOpen"
              @click="methodsOpen = !methodsOpen"
            >
              <span>评测口径 · {{ methodList.length }} 项打分规则</span>
              <span class="eval-fold__caret">{{ methodsOpen ? "收起" : "展开" }}</span>
            </button>
            <div v-if="methodsOpen" class="eval-fold__body">
              <article v-for="item in methodList" :key="item.key" class="eval-method">
                <strong>{{ item.name }}</strong>
                <p class="eval-meta">{{ item.summary }}</p>
                <ul>
                  <li v-for="point in item.points" :key="point">{{ point }}</li>
                </ul>
              </article>
            </div>
          </section>
        </template>
      </template>
    </div>
  </div>
</template>

<style src="./evals.style.css" scoped></style>
