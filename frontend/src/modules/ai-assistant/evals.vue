<script setup lang="ts">
/** 评测页：作者选择一条助手或工作流，跑固定样本并查看失败清单。 */
import { computed, onMounted, ref } from "vue"
import { useRouter } from "vue-router"
import WorkbenchHeader from "@/shared/components/WorkbenchHeader.vue"
import DoodleBtn from "@/shared/components/DoodleBtn.vue"
import EmptyState from "@/shared/components/patterns/EmptyState.vue"
import ErrorState from "@/shared/components/patterns/ErrorState.vue"
import SkeletonCard from "@/shared/components/patterns/SkeletonCard.vue"
import { formatApiError } from "@/shared/api-client"
import {
  fetchEvalRun,
  listAssistants,
  listSopWorkflows,
  runEval,
  type EvalRunDetail,
} from "./api/assistants"
import { EVAL_POLL_MS } from "./constants"
import { evalBlocked, evalVerdict } from "./helpers/eval-view"
import type { AssistantCard, SopWorkflow } from "./types"

const router = useRouter()
const assistants = ref<AssistantCard[]>([])
const workflows = ref<SopWorkflow[]>([])
const kind = ref<"assistant" | "workflow">("assistant")
const targetId = ref("")
const loading = ref(false)
const loaded = ref(false)
const running = ref(false)
const error = ref("")
const detail = ref<EvalRunDetail | null>(null)
const opened = ref("")
let timer = 0

const options = computed(() =>
  kind.value === "assistant"
    ? assistants.value.map((item) => ({ id: item.assistant_id, label: item.display_name }))
    : workflows.value.map((item) => ({ id: String(item.id), label: item.name })),
)

async function load(): Promise<void> {
  loading.value = true
  error.value = ""
  try {
    ;[assistants.value, workflows.value] = await Promise.all([listAssistants(), listSopWorkflows()])
    loaded.value = true
  } catch (cause) {
    error.value = formatApiError(cause as never, "评测对象加载失败")
  } finally {
    loading.value = false
  }
}

const blocked = computed(() => {
  if (kind.value !== "workflow") return ""
  const workflow = workflows.value.find((item) => String(item.id) === targetId.value)
  return evalBlocked(workflow?.orchestration || "sop")
})

function switchKind(next: "assistant" | "workflow"): void {
  kind.value = next
  targetId.value = ""
  detail.value = null
  window.clearInterval(timer)
}

async function refresh(id: number): Promise<void> {
  detail.value = await fetchEvalRun(id)
  if (detail.value.status === "done" || detail.value.status === "failed") {
    running.value = false
    window.clearInterval(timer)
  }
}

async function start(): Promise<void> {
  if (!targetId.value || blocked.value) return
  running.value = true
  error.value = ""
  opened.value = ""
  try {
    const started = await runEval(kind.value, targetId.value)
    await refresh(started.id)
    timer = window.setInterval(() => void refresh(started.id), EVAL_POLL_MS)
  } catch (cause) {
    running.value = false
    error.value = formatApiError(cause as never, "评测失败")
  }
}

onMounted(load)
</script>

<template>
  <div class="doc-page doc-page--fixed wb-shell eval-page">
    <WorkbenchHeader title="评测" icon="bot" />
    <div class="doc-body">
      <DoodleBtn tone="teal" @click="router.push('/ai-assistant')">返回助手</DoodleBtn>
      <ErrorState v-if="error" :message="error" @retry="load" />
      <SkeletonCard v-else-if="loading && !loaded" variant="list" :lines="3" />
      <section v-else class="eval-page__panel">
        <div class="eval-page__kinds">
          <button
            type="button"
            :class="{ 'is-on': kind === 'assistant' }"
            @click="switchKind('assistant')"
          >
            助手
          </button>
          <button
            type="button"
            :class="{ 'is-on': kind === 'workflow' }"
            @click="switchKind('workflow')"
          >
            工作流
          </button>
        </div>
        <EmptyState
          v-if="options.length === 0"
          icon="🧪"
          text="还没有可评测的对象"
          hint="先新建一条助手或工作流"
        />
        <template v-else>
          <select v-model="targetId" class="eval-page__select">
            <option value="">请选择</option>
            <option v-for="item in options" :key="item.id" :value="item.id">
              {{ item.label }}
            </option>
          </select>
          <p v-if="blocked" class="eval-page__verdict">{{ blocked }}</p>
          <DoodleBtn v-else tone="yellow" :disabled="!targetId || running" @click="start"
            >开始评测</DoodleBtn
          >
          <p v-if="detail" class="eval-page__verdict">
            {{ detail.progress_done }} / {{ detail.progress_total }}
          </p>
          <ul v-if="detail">
            <li v-for="sample in detail.samples" :key="sample.sample">
              <button type="button" @click="opened = opened === sample.sample ? '' : sample.sample">
                {{ sample.title || sample.sample }}：{{ evalVerdict(sample.passed) }}
              </button>
              <p v-for="(item, index) in sample.failures" :key="index">{{ item.text }}</p>
              <ol v-if="opened === sample.sample">
                <li v-for="(step, index) in sample.steps" :key="index">
                  {{ step.role }} {{ step.text }} {{ step.tool }}
                </li>
              </ol>
            </li>
          </ul>
        </template>
      </section>
    </div>
  </div>
</template>

<style scoped>
.eval-page__panel {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  margin-top: var(--space-md);
  padding: var(--space-md);
  background: var(--paper);
  border: 1px solid color-mix(in srgb, var(--ink) 10%, transparent);
  border-radius: var(--radius-md);
}

.eval-page__kinds,
.eval-page__select {
  display: flex;
  gap: var(--space-sm);
}

.eval-page__kinds button,
.eval-page__select {
  min-height: 32px;
  padding: var(--space-xs) var(--space-sm);
  background: var(--paper);
  border: 1px solid color-mix(in srgb, var(--ink) 10%, transparent);
  border-radius: var(--radius-sm);
}

.eval-page__kinds button.is-on {
  background: var(--c-ai);
}

.eval-page__verdict {
  font-size: var(--font-size-md);
}
</style>
