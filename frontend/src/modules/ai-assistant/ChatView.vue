<script setup>
import { ref, onMounted, onUnmounted, nextTick, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import client, { getToken } from "@/shared/api-client.js";
import WorkbenchHeader from "@/shared/components/WorkbenchHeader.vue";
import { pressFeedback, iconBounce } from "@/shared/animations.js";
import AnimatedMascot from "@/shared/components/AnimatedMascot.vue";
import {
  IconPlus,
  IconSearch,
  IconArrowLeft,
  IconMessageCircle,
} from "@/shared/icons/index.js";
import { ElMessage } from "element-plus";
import { renderMermaidBlocks } from "./composables/useMarkdown.js";
import MessageBubble from "./components/MessageBubble.vue";
import ConfirmDialog from "./components/ConfirmDialog.vue";
import ChatInput from "./components/ChatInput.vue";
import { useMessageStore } from "./composables/useMessageStore.js";
import { useToolCalls } from "./composables/useToolCalls.js";
import { useConversation } from "./composables/useConversation.js";
import { useSSE } from "./composables/useSSE.js";

const route = useRoute();
const router = useRouter();
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
  for (const [runId, card] of Object.entries(taskCards.value)) {
    if (name === "create_runner_task") {
      taskCards.value[runId] = {
        ...card,
        status: "PENDING",
        updatedAt: Date.now(),
      };
    } else if (name === "run_test") {
      const parsed = _parseTaskCardProgress(output);
      const isDone = state === "success" || state === "finished";
      const status = isDone
        ? parsed?.failed > 0
          ? "FAILED"
          : "COMPLETED"
        : "RUNNING";
      const progress = parsed
        ? { current: parsed.total, total: parsed.total }
        : card.progress;
      taskCards.value[runId] = {
        ...card,
        status,
        progress,
        updatedAt: Date.now(),
      };
      for (const m of messages.value) {
        if (m.hint?.run_id === runId) m.hint = { ...card, status, progress };
      }
    } else if (name === "stop_run") {
      taskCards.value[runId] = {
        ...card,
        status: "STOPPED",
        updatedAt: Date.now(),
      };
    }
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
  if (streamMode.value === "fallback") return "⏳ 降级模式";
  return null;
});

const connectionModeLabel = computed(() => {
  if (connectionMode.value === "sse") return "SSE 流式通道";
  if (connectionMode.value === "fallback") return "Django 直连通道";
  if (connectionMode.value === "connecting") return "发送时自动连接";
  return "检测中...";
});

const connectionModeIcon = computed(() => {
  if (connectionMode.value === "sse") return "⚡";
  if (connectionMode.value === "fallback") return "⏳";
  if (connectionMode.value === "connecting") return "🔗";
  return "🔍";
});

// Live model activity status — driven by SSE onStatus callback
const modelStatusLabel = computed(() => {
  switch (modelStatus.value) {
    case "thinking":
      return "🤔 思考中";
    case "calling_model":
      return "🧠 调用模型";
    case "tool_calling":
      return "🔧 调用工具";
    case "streaming":
      return "✍️ 输出中";
    case "done":
      return "✅ 已完成";
    case "idle":
      return null;
    default:
      return null;
  }
});
const modelStatusIcon = computed(() => {
  switch (modelStatus.value) {
    case "thinking":
      return "🤔";
    case "calling_model":
      return "🧠";
    case "tool_calling":
      return "🔧";
    case "streaming":
      return "✍️";
    case "done":
      return "✅";
    case "idle":
      return null;
    default:
      return null;
  }
});

async function loadAgent() {
  try {
    const { data } = await client.get(`/ai/agents/${agentId.value}`);
    if (data.ok) {
      agent.value = data.agent;
      loadConversations();
    }
  } catch (_) {}
}

async function handleFileUpload(e) {
  const file = e.target.files?.[0];
  if (!file) return;
  uploading.value = true;
  const formData = new FormData();
  formData.append("file", file);
  try {
    const token = getToken();
    const resp = await fetch("/api/ai/upload-file", {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: formData,
    });
    const data = await resp.json();
    if (data.ok) {
      uploadedFile.value = data.data;
      ElMessage.success(
        `已解析: ${file.name} (${(data.data.size / 1024).toFixed(1)}KB)`,
      );
    } else ElMessage.error(data.error || "文件上传失败");
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
  // 同步占位，防止 Enter 连触 / 重复事件在 await 前再次进入
  sending.value = true;
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

  await sendStreamMessage(msgText, displayText);
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
  return avatar?.startsWith("/api/ai/avatars/")
    ? {
        backgroundImage: `url(${avatar})`,
        backgroundSize: "cover",
        backgroundPosition: "center",
      }
    : {};
}
function avatarText(avatar) {
  return avatar?.startsWith("/api/ai/avatars/") ? "" : avatar || "";
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
      mark="💬"
    />

    <div class="doc-body">
      <div class="chat-layout">
        <!-- Left: conversation sidebar -->
        <section class="doc-section chat-sidebar">
          <button class="back-btn" @click="router.push('/ai-assistant')">
            <IconArrowLeft :size="18" /><span>返回智能体列表</span>
          </button>
          <button class="new-chat-btn" @click="newChat($event)">
            <IconPlus :size="18" /><span>开启新对话</span>
          </button>

          <!-- Agent card -->
          <div class="agent-card" v-if="agent">
            <div class="agent-avatar" :style="avatarStyle(agent.avatar)">
              <span v-if="avatarText(agent.avatar)">{{
                avatarText(agent.avatar)
              }}</span>
            </div>
            <div class="agent-info">
              <div class="agent-name">{{ agent.name }}</div>
              <div class="agent-provider">
                {{ agent.model_provider }} / {{ agent.model_name }}
              </div>
            </div>
          </div>

          <!-- Conversation list -->
          <div class="conv-list">
            <div class="conv-list-title">
              <IconMessageCircle :size="15" /><span>对话历史</span
              ><span class="conv-count">{{ conversations.length }}</span>
            </div>
            <div
              v-for="c in conversations"
              :key="c.id"
              :class="['conv-item', { active: activeConv === c.id }]"
              @click="selectChat(c.id)"
            >
              <span
                class="conv-indicator"
                :class="{ active: activeConv === c.id }"
              />
              <span
                v-if="editingConvId === c.id"
                class="conv-title"
                @click.stop
              >
                <input
                  class="conv-rename-input"
                  v-model="editingTitle"
                  @keydown.enter="finishRename"
                  @keydown.escape="cancelRename"
                  @blur="finishRename"
                />
              </span>
              <span
                v-else
                class="conv-title"
                @dblclick.stop="startRename(c)"
                :title="'双击修改名称'"
                >{{ c.title }}</span
              >
              <span class="conv-status" :class="c.status" />
              <button
                class="conv-delete-btn"
                @click.stop="deleteConversation(c)"
                title="删除对话"
              >
                ✕
              </button>
            </div>
            <div v-if="!conversations.length" class="conv-empty">
              <IconSearch :size="36" /><span>暂无对话记录</span
              ><span class="conv-empty-hint">点击上方「开启新对话」</span>
            </div>
          </div>

          <button class="wb-tasks-link" @click="router.push('/ai-assistant')">
            📋 在工作台查看任务看板
          </button>
        </section>

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
                <IconMessageCircle :size="20" :color="'#19c8b9'" />
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
              ⚠️ AgentScope 服务不可用，当前为
              <strong>Django 降级模式</strong>
              — AI 对话直接调用模型 API，SSE 流式输出和工具调用暂不可用
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
