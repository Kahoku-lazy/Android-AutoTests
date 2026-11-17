<script setup lang="ts">
/**
 * 测试对话：多栏切换。发送才进入进行中；刷新后轮询；取消只停当前栏。
 *
 * 视觉是该助手的笔色：当前对话栏描边 + 硬影、助手气泡描边、发送钮深到浅渐变。
 * 渐变与描边都从本页行内的 `--assistant-marker` 现算。
 */
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue"
import { useRoute, useRouter } from "vue-router"
import { ElMessage, ElMessageBox } from "element-plus"
import DoodleBtn from "@/shared/components/DoodleBtn.vue"
import WorkbenchHeader from "@/shared/components/WorkbenchHeader.vue"
import { formatApiError } from "@/shared/api-client"
import AssistantLanePanel from "./components/AssistantLanePanel.vue"
import ThreadLogPanel from "./components/ThreadLogPanel.vue"
import {
  cancelThread,
  createThread,
  deleteThread,
  listThreadLogs,
  listThreads,
  pollThread,
  renameThread,
  sendThread,
  issueLogTicket,
  threadLogUrl,
} from "./api/assistants"
import { markerVars } from "./helpers/marker"
import { clockLabel } from "./helpers/time-label"
import { threadStatusLabel } from "./helpers/thread-status"
import type { AssistantThread, ThreadLog, ThreadMessage } from "./types"
import "./tokens.css"

const route = useRoute()
const router = useRouter()
const assistantId = String(route.params.assistantId || "")
const marker = String(route.query.marker || "teal")
const assistantName = String(route.query.name || "") || "对话"
const threads = ref<AssistantThread[]>([])
const currentId = ref("")
const messages = ref<ThreadMessage[]>([])
const logs = ref<ThreadLog[]>([])
const logsOpen = ref(false)
const logsLoading = ref(false)
const logsError = ref("")
const status = ref("idle")
const draft = ref("")
const anchor = ref<HTMLElement | null>(null)
let timer = 0

const statusLabel = computed(() => threadStatusLabel(status.value))
const iconStyle = computed(() => ({
  background: "linear-gradient(135deg, var(--assistant-marker), var(--assistant-marker-soft))",
}))

/** 轮询：同时把当前栏的状态回写到左栏，避免列表停在旧状态。 */
async function refresh(): Promise<void> {
  if (!currentId.value) return
  const wasRunning = status.value === "running"
  const detail = await pollThread(currentId.value)
  messages.value = detail.messages
  status.value = detail.status
  const lane = threads.value.find((item) => item.thread_id === currentId.value)
  if (lane) lane.status = detail.status
  // 一轮刚跑完：日志面板开着就重取，把「还在写」换成可打开的一条
  if (logsOpen.value && wasRunning && detail.status !== "running") await loadLogs()
}

/** 切栏：消息与日志都属于「当前栏」，换栏必须一起清掉，日志面板开着就顺带取新的。 */
async function openLane(threadId: string): Promise<void> {
  currentId.value = threadId
  messages.value = []
  logs.value = []
  if (logsOpen.value) await loadLogs()
  await refresh()
}

async function addLane(): Promise<void> {
  const created = await createThread(assistantId)
  threads.value = await listThreads(assistantId)
  await openLane(created.thread_id)
}

async function send(): Promise<void> {
  const text = draft.value.trim()
  if (!text || !currentId.value || status.value === "running") return
  draft.value = ""
  await sendThread(currentId.value, text)
  status.value = "running"
  await refresh()
}

/** 日志入口：已开再点就收起；打开那一刻才取，取完只换面板内容（不动两栏网格）。 */
async function toggleLogs(): Promise<void> {
  if (logsOpen.value) {
    logsOpen.value = false
    return
  }
  logsOpen.value = true
  await loadLogs()
}

/** 取本栏日志；进行中的一轮由后端标 writing，列表里只显示「还在写」。 */
async function loadLogs(): Promise<void> {
  if (!currentId.value) return
  logsLoading.value = true
  logsError.value = ""
  try {
    logs.value = await listThreadLogs(currentId.value)
  } catch (e) {
    logs.value = []
    logsError.value = formatApiError(e as never, "日志加载失败")
  } finally {
    logsLoading.value = false
  }
}

async function openLog(item: ThreadLog): Promise<void> {
  if (item.writing || !item.report_id) return
  const ticket = await issueLogTicket(currentId.value, item.report_id)
  window.open(threadLogUrl(currentId.value, item.report_id, ticket), "_blank")
}

async function cancel(): Promise<void> {
  if (!currentId.value) return
  await cancelThread(currentId.value)
  await refresh()
}

/** 就地改名：只改标题，不动消息与该栏实例。 */
async function renameLane(id: string, title: string): Promise<void> {
  try {
    const updated = await renameThread(id, title)
    const lane = threads.value.find((item) => item.thread_id === id)
    if (lane) lane.title = updated.title
  } catch (e) {
    ElMessage.error(formatApiError(e as never, "重命名失败"))
  }
}

/** 删除对话栏：先二次确认；删的是当前栏就切到第一条，没有就新建一栏。 */
async function removeLane(id: string): Promise<void> {
  const lane = threads.value.find((item) => item.thread_id === id)
  const name = lane?.title || "该对话"
  try {
    await ElMessageBox.confirm(`删除「${name}」？消息记录一并删除，不可恢复。`, "删除对话", {
      type: "warning",
      confirmButtonText: "删除",
      cancelButtonText: "取消",
    })
  } catch {
    return
  }
  try {
    await deleteThread(id)
  } catch (e) {
    ElMessage.error(formatApiError(e as never, "删除失败"))
    return
  }
  threads.value = await listThreads(assistantId)
  if (currentId.value !== id) return
  if (threads.value.length) await openLane(threads.value[0].thread_id)
  else await addLane()
}

/* 返回入口现在属于页面正文（页头不再放按钮） */
function back(): void {
  void router.push({ name: "ai-assistant" })
}

watch(
  () => messages.value.length,
  async () => {
    await nextTick()
    anchor.value?.scrollIntoView?.({ block: "end" })
  },
)

onMounted(async () => {
  threads.value = await listThreads(assistantId)
  if (threads.value.length === 0) await addLane()
  else await openLane(threads.value[0].thread_id)
  timer = window.setInterval(() => void refresh(), 2000)
})

onUnmounted(() => window.clearInterval(timer))
</script>

<template>
  <div
    class="doc-page doc-page--fixed wb-shell ai-assistant-page ai-chat"
    :style="markerVars(marker)"
  >
    <WorkbenchHeader :title="assistantName" icon="bot" :icon-gradient="iconStyle.background" />

    <div class="doc-body">
      <div class="ai-chat__toolbar">
        <DoodleBtn tone="paper" @click="back">‹ 返回助手</DoodleBtn>
        <DoodleBtn tone="paper" :aria-expanded="logsOpen" @click="toggleLogs">日志</DoodleBtn>
      </div>

      <div class="ai-chat__body" :class="{ 'is-logs-open': logsOpen }">
        <AssistantLanePanel
          :lanes="threads"
          :current-id="currentId"
          @create="addLane"
          @open="openLane"
          @rename="renameLane"
          @remove="removeLane"
        >
          <!-- 日志卡住对话栏下面：与「这一栏」同属左栏，展开时只把左栏加宽 -->
          <ThreadLogPanel
            v-if="logsOpen"
            :logs="logs"
            :loading="logsLoading"
            :error="logsError"
            @open="openLog"
            @retry="loadLogs"
            @close="logsOpen = false"
          />
        </AssistantLanePanel>

        <section class="ai-chat__pane">
          <div class="ai-chat__meta">
            <span class="ai-chat__status" :data-state="status">{{ statusLabel }}</span>
            <span class="ai-chat__meta-text">{{ messages.length }} 条消息</span>
          </div>

          <div class="ai-chat__stream">
            <p v-if="!messages.length" class="ai-chat__empty">
              这个对话栏还没有消息，发送第一句开始。
            </p>
            <div
              v-for="(item, index) in messages"
              :key="index"
              class="ai-chat__row"
              :class="`ai-chat__row--${item.role}`"
            >
              <div class="ai-chat__bubble-wrap">
                <p class="ai-chat__bubble">{{ item.content }}</p>
                <time v-if="item.created_at" class="ai-chat__time" :datetime="item.created_at">
                  {{ clockLabel(item.created_at) }}
                </time>
              </div>
            </div>
            <p v-if="status === 'running'" class="ai-chat__running">这一轮还在跑</p>
            <div ref="anchor" class="ai-chat__anchor" aria-hidden="true" />
          </div>

          <form class="ai-chat__composer" @submit.prevent="send">
            <input
              v-model="draft"
              class="ai-chat__input"
              aria-label="消息"
              placeholder="输入一句话，回车发送"
              :disabled="status === 'running'"
            />
            <button type="submit" class="ai-chat__send" :disabled="status === 'running'">
              发送
            </button>
            <button
              v-if="status === 'running'"
              type="button"
              class="ai-chat__cancel"
              @click="cancel"
            >
              取消
            </button>
          </form>
        </section>
      </div>
    </div>
  </div>
</template>

<style src="./chat.style.css" scoped></style>
