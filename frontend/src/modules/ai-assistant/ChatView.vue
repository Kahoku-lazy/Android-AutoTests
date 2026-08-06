<script setup>
import { ref, onMounted, onUnmounted, nextTick, computed } from "vue";
import { useRoute } from "vue-router";
import { getAgentDetail, uploadFile } from "./api/agents";
import WorkbenchHeader from "@/shared/components/WorkbenchHeader.vue";
import { pressFeedback, iconBounce } from "@/shared/animations";
import AnimatedMascot from "@/shared/components/AnimatedMascot.vue";
import { IconMessageCircle } from "@/shared/icons/index";
import { ElMessage } from "element-plus";
import { renderMermaidBlocks } from "./composables/useMarkdown";
import ErrorState from "@/shared/components/patterns/ErrorState.vue";
import {
  AVATAR_PATH_PREFIX,
  MODEL_STATUS_MAP,
  CONNECTION_MODE_LABELS,
  CONNECTION_MODE_ICONS,
} from "./constants";
import MessageBubble from "./components/MessageBubble.vue";
import ConfirmDialog from "./components/ConfirmDialog.vue";
import ChatInput from "./components/ChatInput.vue";
import ChatSidebar from "./components/ChatSidebar.vue";
import { useMessageStore } from "./composables/useMessageStore";
import { useToolCalls } from "./composables/useToolCalls";
import { useConversation } from "./composables/useConversation";
import { useSSE } from "./composables/useSSE";

const route = useRoute();
const agentId = ref(parseInt(route.params.agentId));
const agent = ref(null);
const inputText = ref("");
const chatBody = ref(null);

const messageStore = useMessageStore();
const { messages, assistIdx, backgroundStreamConvId } = messageStore;

const { toolCalls, resetToolCalls } = useToolCalls();

const {
  conversations,
  activeConv,
  connectionMode,
  editingConvId,
  editingTitle,
  loadConversations,
  newChat: createChat,
  selectChat: switchChat,
  startRename,
  finishRename,
  cancelRename,
  deleteConversation,
} = useConversation(agentId, messageStore);

// File upload
const uploading = ref(false);
const uploadedFile = ref(null);

// Task cards (SSE → HintCard；历史任务见工作台看板)
const taskCards = ref({});
const importingPRD = ref(false);

function scrollBottom() {
  nextTick(() => {
    if (chatBody.value) chatBody.value.scrollTop = chatBody.value.scrollHeight;
  });
}

function _parseTaskCardProgress(output) {
  if (!output) return null;
  const str = typeof output === "string" ? output : JSON.stringify(output);
  const passedMatch = str.match(/(?:passed|通过)[=:]?\s*(\d+)/i);
  const failedMatch = str.match(/(?:failed|失败)[=:]?\s*(\d+)/i);
  const totalMatch = str.match(/Total:\s*(\d+)/i);
  if (!passedMatch && !failedMatch) return null;
  const passed = parseInt(passedMatch?.[1] || "0");
  const failed = parseInt(failedMatch?.[1] || "0");
  const total = parseInt(totalMatch?.[1] || passed + failed);
  return { passed, failed, total };
}

function _updateTaskCardProgress(tr) {
  const name = tr?.name || "";
  const output = tr?.output || "";
  const state = tr?.state || "";

  // Find the matching task card by checking if output content overlaps
  let matchedRunId = null
  for (const [runId, card] of Object.entries(taskCards.value)) {
    if (card?.output && output.includes(card.output.slice(0, 30))) {
      matchedRunId = runId
      break
    }
  }
  // Fallback: use the first card if no content match found (for create_runner_task)
  if (!matchedRunId && name === 'create_runner_task') {
    const entries = Object.entries(taskCards.value)
    if (entries.length) matchedRunId = entries[entries.length - 1][0]
  }
  if (!matchedRunId) return

  const card = taskCards.value[matchedRunId]
  if (name === "create_runner_task") {
    taskCards.value[matchedRunId] = { ...card, status: "PENDING", updatedAt: Date.now() }
  } else if (name === "run_test") {
    const parsed = _parseTaskCardProgress(output)
    const isDone = state === "success" || state === "finished"
    const status = isDone ? (parsed?.failed > 0 ? "FAILED" : "COMPLETED") : "RUNNING"
    const progress = parsed ? { current: parsed.total, total: parsed.total } : card.progress
    taskCards.value[matchedRunId] = { ...card, status, progress, updatedAt: Date.now() }
    for (const m of messages.value) {
      if (m.hint?.run_id === matchedRunId) m.hint = { ...card, status, progress }
    }
  } else if (name === "stop_run") {
    taskCards.value[matchedRunId] = { ...card, status: "STOPPED", updatedAt: Date.now() }
  }
}

const {
  streamMode,
  abortController,
  sseBuilder,
  modelStatus,
  sending,
  pendingConfirm,
  pendingConfirmMsgIdx,
  degradedMode,
  checkHealth,
  sendStreamMessage,
  stopStream,
  detachStream,
  resolveConfirm,
  approveAll,
  denyAll,
} = useSSE({
  activeConv,
  conversations,
  messages,
  assistIdx,
  toolCalls,
  taskCards,
  connectionMode,
  scrollBottom,
  renderMermaidBlocks,
  loadConversations,
  updateTaskCardProgress: _updateTaskCardProgress,
  backgroundStreamConvId,
  appendPlaceholder: messageStore.appendUserAndAssistantPlaceholder,
});

onMounted(() => {
  loadAgent();
  checkHealth();
});
onUnmounted(() => {
  // Save partial content and detach — let the SSE stream finish in background.
  // When the user returns, completed messages will be loaded from the backend.
  detachStream();
});

const activeConvTitle = computed(() => {
  const c = conversations.value.find((c) => c.id === activeConv.value);
  return c?.title || "当前对话";
});

const streamModeLabel = computed(() => {
  if (streamMode.value === "sse") return "⚡ SSE 流式";
  return null;
});

const connectionModeLabel = computed(() => {
  return CONNECTION_MODE_LABELS[connectionMode.value] || "检测中...";
});

const connectionModeIcon = computed(() => {
  return CONNECTION_MODE_ICONS[connectionMode.value] || "🔍";
});

// Live model activity status — driven by SSE onStatus callback
const modelStatusLabel = computed(() => {
  return MODEL_STATUS_MAP[modelStatus.value]?.label || null;
});
const modelStatusIcon = computed(() => {
  return MODEL_STATUS_MAP[modelStatus.value]?.icon || null;
});

const loadError = ref("");

async function loadAgent() {
  loadError.value = "";
  try {
    const data = await getAgentDetail(agentId.value);
    if (data.status) {
      agent.value = data.agent;
      loadConversations();
    } else {
      loadError.value = data.message || "加载 Agent 失败";
    }
  } catch (e) {
    loadError.value = "网络请求失败，请检查连接";
    console.error(e);
  }
}

async function handleFileUpload(e) {
  const file = e.target.files?.[0];
  if (!file) return;
  uploading.value = true;
  const formData = new FormData();
  formData.append("file", file);
  try {
    const data = await uploadFile(formData);
    if (data.status) {
      uploadedFile.value = data.data;
      const sizeKB = ((data.data && data.data.size) || 0) / 1024;
      ElMessage.success(
        `已解析: ${file.name} (${sizeKB.toFixed(1)}KB)`,
      );
    } else ElMessage.error(data.message || "文件上传失败");
  } catch (e) {
    ElMessage.error("文件上传失败");
  }
  uploading.value = false;
  e.target.value = "";
}
function removeFile() {
  uploadedFile.value = null;
}

// Chat
async function newChat(ev) {
  if (ev?.currentTarget) pressFeedback(ev.currentTarget, ev);
  const mark = document.querySelector(".chat-page .brand-mark");
  if (mark) iconBounce(mark);
  await createChat((id) => selectChat(id));
}

async function selectChat(id) {
  // Save partial content of current conversation before switching.
  // Use stopStream (not detachStream) here because switching conversations
  // replaces messages.value — the old stream's callbacks would write to
  // the wrong array otherwise.
  stopStream();
  await switchChat(id, {
    onAfterSelect: async () => {
      scrollBottom();
    },
  });
}

async function sendMessage() {
  const text = inputText.value.trim();
  if ((!text && !uploadedFile.value) || !activeConv.value || sending.value)
    return;

  inputText.value = "";

  let msgText = text;
  let displayText = text || "";
  if (uploadedFile.value) {
    const f = uploadedFile.value;
    msgText += `\n\n[上传文件: ${f.filename} (${f.type})]\n\`\`\`\n${f.content}\n\`\`\``;
    displayText =
      (text ? text + "\n" : "") +
      `📎 ${f.filename} (${(f.size / 1024).toFixed(1)}KB)` +
      (text ? "" : "\n文件内容已发送给 AI");
    uploadedFile.value = null;
  }

  // 同步占位，防止 Enter 连触 / 重复事件在 await 前再次进入
  sending.value = true;
  try {
    await sendStreamMessage(msgText, displayText);
  } finally {
    // Fallback: ensure sending is released even if an unexpected
    // error escapes sendStreamMessage's internal catch.
    if (sending.value) sending.value = false;
  }
}

function handleKey(e) {
  if (e.key === "Enter" && !e.shiftKey) {
    // 中文输入法确认选词时不发送
    if (e.isComposing || e.keyCode === 229) return;
    e.preventDefault();
    sendMessage();
  }
}

// Avatars
function avatarStyle(avatar) {
  return avatar?.startsWith(AVATAR_PATH_PREFIX)
    ? {
        backgroundImage: `url(${avatar})`,
        backgroundSize: "cover",
        backgroundPosition: "center",
      }
    : {};
}
function avatarText(avatar) {
  return avatar?.startsWith(AVATAR_PATH_PREFIX) ? "" : avatar || "";
}

function toggleThinking(m) {
  // Replace the object in the array to trigger Vue reactivity.
  // Direct property mutation (m.thinkingExpanded = ...) on a plain object
  // inside a ref array is not tracked by Vue.
  const idx = messages.value.findIndex((msg) => msg === m);
  if (idx >= 0) {
    messages.value[idx] = { ...m, thinkingExpanded: !m.thinkingExpanded };
  }
}

function toggleRoundThinking(msg, roundIdx) {
  const idx = messages.value.findIndex((m) => m === msg);
  if (idx >= 0 && messages.value[idx].rounds) {
    const rounds = [...messages.value[idx].rounds];
    if (rounds[roundIdx]) {
      rounds[roundIdx] = { ...rounds[roundIdx], thinkingExpanded: !rounds[roundIdx].thinkingExpanded };
      messages.value[idx] = { ...messages.value[idx], rounds };
    }
  }
}

async function handleImportPRD({ sessionId }) {
  if (!sessionId || sending.value) return;
  importingPRD.value = true;
  inputText.value = `请将 session_id=${sessionId} 的设计用例全部导入到用例库（调用 import_designed_cases）`;
  try {
    await sendMessage();
  } finally {
    importingPRD.value = false;
  }
}
</script>

<template>
  <div class="doc-page wb-shell chat-page ai-workbench">
    <WorkbenchHeader
      :title="agent ? `${agent.name} · 对话` : 'AI 对话'"
      :subtitle="
        agent?.description ||
        '与智能体进行多轮对话，支持 Markdown、Mermaid 图表与文件上传'
      "
      icon="message-circle"
      icon-gradient="linear-gradient(135deg,#5EEAD4,#14b8a6)"
    />

    <ErrorState v-if="loadError" :message="loadError" @retry="loadAgent" />

    <div class="doc-body">
      <div class="chat-layout">
        <!-- Left: conversation sidebar -->
        <ChatSidebar
          :agent="agent"
          :conversations="conversations"
          :active-conv="activeConv"
          :editing-conv-id="editingConvId"
          :editing-title="editingTitle"
          @update:editing-title="editingTitle = $event"
          @new-chat="newChat"
          @select-chat="selectChat"
          @start-rename="startRename"
          @finish-rename="finishRename"
          @cancel-rename="cancelRename"
          @delete-conversation="deleteConversation"
        />

        <!-- Right: chat area -->
        <section class="doc-section chat-main">
          <div v-if="!activeConv" class="chat-empty">
            <div class="empty-avatar"><AnimatedMascot :size="72" /></div>
            <p class="empty-title">开始一场对话</p>
            <p class="empty-desc">
              在左侧选择已有对话，或点击「开启新对话」创建新会话
            </p>
          </div>

          <template v-else>
            <div class="chat-header">
              <div class="chat-header-left">
                <IconMessageCircle :size="20" :color="'var(--ai-teal)'" />
                <span class="chat-header-title">{{ activeConvTitle }}</span>
                <span
                  v-if="streamModeLabel"
                  class="stream-mode-badge"
                  :class="streamMode"
                  >{{ streamModeLabel }}</span
                >
                <span
                  v-if="modelStatusLabel"
                  class="model-status-badge"
                  :class="modelStatus"
                >
                  <span class="model-status-dot"></span>{{ modelStatusLabel }}
                </span>
              </div>
              <div class="chat-header-right">
                <span
                  class="connection-indicator"
                  :class="connectionMode"
                  :title="connectionModeLabel"
                  >{{ connectionModeIcon }} {{ connectionModeLabel }}</span
                >
                <span class="msg-count">{{ messages.length }} 条消息</span>
                <button
                  v-if="sending && streamMode === 'sse'"
                  class="stop-btn"
                  @click="stopStream"
                  title="停止生成"
                >
                  ⏹ 停止
                </button>
              </div>
            </div>

            <div v-if="degradedMode" class="degraded-banner">
              ⚠️ AI 模型服务暂不可用，请检查 Agent 的 API Key 和网络配置
            </div>
            <div ref="chatBody" class="chat-body">
              <MessageBubble
                v-for="(m, i) in messages"
                :key="i"
                :message="m"
                :agent-name="agent?.name || 'AI'"
                :agent-avatar="agent?.avatar || ''"
                :avatar-style-fn="avatarStyle"
                :avatar-text-fn="avatarText"
                :importing-prd="importingPRD"
                :typing="
                  sending &&
                  i === messages.length - 1 &&
                  m.role === 'assistant' &&
                  !m.content
                "
                @toggle-thinking="toggleThinking"
                @toggle-round-thinking="toggleRoundThinking"
                @import-prd="handleImportPRD"
              />
            </div>

            <ConfirmDialog
              :confirm="pendingConfirm"
              @approve="resolveConfirm($event, true)"
              @deny="resolveConfirm($event, false)"
              @approve-all="approveAll"
              @deny-all="denyAll"
              @cancel="denyAll"
            />

            <ChatInput
              v-model="inputText"
              :sending="sending"
              :uploaded-file="uploadedFile"
              :uploading="uploading"
              @send="sendMessage"
              @keydown="handleKey"
              @upload="handleFileUpload"
              @remove-file="removeFile"
            />
          </template>
        </section>
      </div>
    </div>
  </div>
</template>

<style scoped src="./ChatView.css"></style>
