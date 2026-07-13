<script setup>
import { ref, onMounted, onUnmounted, nextTick, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import client from "@/shared/api-client.js";
import { Button as AnimalButton, Collapse } from "animal-island-vue";
import PageHeader from "@/shared/components/PageHeader.vue";
import AnimatedMascot from "@/shared/components/AnimatedMascot.vue";
import {
  IconPlus,
  IconSearch,
  IconArrowLeft,
  IconMessageCircle,
  IconPlay,
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
const { messages, assistIdx } = messageStore;

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

// Task records
const taskRecords = ref([]);
const taskCards = ref({});
const taskHistory = ref([]);
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
  sendStreamMessage,
  stopStream,
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
});

onMounted(() => loadAgent());
onUnmounted(() => {
  if (abortController.value) abortController.value.abort();
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
      loadTaskRecords();
    }
  } catch (_) {}
}

// Task records
async function loadTaskRecords() {
  try {
    const { data } = await client.get("/runner/runs");
    if (data.ok && data.runs)
      taskRecords.value = (data.runs || [])
        .filter((r) => r.run_id?.startsWith("ai-task-"))
        .slice(0, 10);
  } catch (_) {
    taskRecords.value = [];
  }
}

// Load AI task history for the current conversation
async function loadTaskHistory(convId) {
  if (!convId) {
    taskHistory.value = [];
    return;
  }
  try {
    const { data } = await client.get(`/ai/conversations/${convId}/tasks`);
    if (data.ok && data.tasks) {
      taskHistory.value = data.tasks.map((t) => ({
        run_id: t.run_id,
        title: t.summary || t.run_id.replace("ai-task-", "").slice(0, 8),
        status: t.status,
        device: t.device_serial,
        device_model: t.device_model || "",
        cases: t.cases || [],
        case_titles: [],
        loop_count: t.loop_count || 1,
        progress: {
          current: 0,
          total: (t.cases || []).length * (t.loop_count || 1),
        },
        actions: ["view_detail"],
      }));
    }
  } catch (_) {
    taskHistory.value = [];
  }
}
function goToTask(runId) {
  router.push("/runner");
}

async function handleFileUpload(e) {
  const file = e.target.files?.[0];
  if (!file) return;
  uploading.value = true;
  const formData = new FormData();
  formData.append("file", file);
  try {
    const token = localStorage.getItem("access_token");
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
async function newChat() {
  await createChat((id) => selectChat(id));
}

async function selectChat(id) {
  await switchChat(id, {
    onAfterSelect: async (convId) => {
      await loadTaskHistory(convId);
      scrollBottom();
    },
  });
}

async function sendMessage() {
  const text = inputText.value.trim();
  if ((!text && !uploadedFile.value) || !activeConv.value || sending.value) return;
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
  m.thinkingExpanded = !m.thinkingExpanded;
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

// Open task detail page
function viewTaskDetail(runId) {
  router.push(`/runner?run=${runId}`);
}

// Stop a running task — call backend then update card status
async function stopTask(runId) {
  if (taskCards.value[runId]) {
    taskCards.value[runId] = {
      ...taskCards.value[runId],
      status: "STOPPED",
      updatedAt: Date.now(),
    };
  }
  try {
    await client.post(`/runner/run/${runId}/stop`);
    ElMessage.success("任务已停止");
  } catch (e) {
    ElMessage.error("停止任务失败");
  }
}

// Compute CSS class for task status badge
function taskStatusClass(status) {
  return status?.toLowerCase() || "";
}
function taskStatusLabel(status) {
  const map = {
    PENDING: "待执行",
    RUNNING: "执行中",
    COMPLETED: "已完成",
    FAILED: "失败",
    STOPPED: "已停止",
  };
  return map[status?.toUpperCase()] || status || "";
}
function progressPercent(progress) {
  if (!progress) return 0;
  const p = progress.current / progress.total;
  return Math.round(Math.max(0, Math.min(100, p * 100)));
}
</script>

<template>
  <div class="doc-page chat-page">
    <PageHeader
      :title="agent ? `${agent.name} · 对话` : 'AI 对话'"
      :subtitle="
        agent?.description ||
        '与智能体进行多轮对话，支持 Markdown、Mermaid 图表与文件上传'
      "
      color="app-yellow"
    />

    <div class="doc-body">
      <div class="chat-layout">
        <!-- Left: conversation sidebar -->
        <section class="doc-section chat-sidebar">
          <button class="back-btn" @click="router.push('/ai-assistant')">
            <IconArrowLeft :size="18" /><span>返回智能体列表</span>
          </button>
          <button class="new-chat-btn" @click="newChat">
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

          <!-- Task cards — live SSE cards + history -->
          <div class="task-records">
            <Collapse question="📋 AI 任务卡片" :default-expanded="false">
              <!-- Live task cards (from SSE) -->
              <div
                v-if="Object.keys(taskCards).length"
                class="task-records-section"
              >
                <div class="task-section-title">实时</div>
                <div
                  v-for="(card, rid) in taskCards"
                  :key="rid"
                  class="task-record-item task-card-item"
                  :class="card.status?.toLowerCase()"
                  @click="viewTaskDetail(rid)"
                >
                  <span
                    class="task-record-status"
                    :class="card.status?.toLowerCase()"
                  ></span>
                  <div class="task-record-info">
                    <span class="task-record-name">{{
                      card.title || rid
                    }}</span>
                    <span class="task-record-meta"
                      >{{ card.device || "" }} ·
                      {{ (card.case_titles || []).length }} 用例</span
                    >
                  </div>
                  <span
                    class="task-record-badge"
                    :class="card.status?.toLowerCase()"
                    >{{ taskStatusLabel(card.status) }}</span
                  >
                </div>
              </div>
              <!-- Historical tasks from API -->
              <div v-if="taskHistory.length" class="task-records-section">
                <div
                  v-if="Object.keys(taskCards).length"
                  class="task-section-title"
                >
                  历史
                </div>
                <div
                  v-for="t in taskHistory"
                  :key="t.run_id"
                  class="task-record-item"
                  :class="t.status?.toLowerCase()"
                  @click="viewTaskDetail(t.run_id)"
                >
                  <span
                    class="task-record-status"
                    :class="t.status?.toLowerCase()"
                  ></span>
                  <div class="task-record-info">
                    <span class="task-record-name">{{
                      t.title || t.run_id.replace("ai-task-", "").slice(0, 12)
                    }}</span
                    ><span class="task-record-meta"
                      >{{ t.device || "" }} ·
                      {{ (t.cases || []).length }} 用例</span
                    >
                  </div>
                  <IconPlay :size="14" />
                </div>
              </div>
              <div
                v-if="!Object.keys(taskCards).length && !taskHistory.length"
                class="task-records-empty"
              >
                暂无任务卡片
              </div>
            </Collapse>
          </div>
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
                @toggle-thinking="toggleThinking"
                @import-prd="handleImportPRD"
              />
              <div
                v-if="sending && !messages[messages.length - 1]?.content"
                class="msg assistant typing-row"
              >
                <div class="msg-avatar">
                  <span v-if="avatarText(agent?.avatar)">{{
                    avatarText(agent?.avatar)
                  }}</span>
                </div>
                <div class="msg-content">
                  <div class="msg-author">{{ agent?.name || "AI" }}</div>
                  <div class="msg-text typing">
                    <span></span><span></span><span></span>
                  </div>
                </div>
              </div>
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

<style scoped>
.chat-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.chat-page :deep(.doc-body) {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}
.chat-layout {
  flex: 1;
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 20px;
  min-height: 0;
  height: 100%;
}

/* Sidebar */
.chat-sidebar {
  display: flex;
  flex-direction: column;
  padding: 16px;
  overflow: hidden;
  min-height: 0;
  gap: 12px;
  height: 100%;
}
.back-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #19c8b9;
  border-radius: 12px;
  background: #e6f9f6;
  color: #158a80;
  font-size: 15px;
  font-weight: 700;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
}
.back-btn:hover {
  background: #19c8b9;
  color: #fff;
  box-shadow: 0 4px 14px rgba(25, 200, 185, 0.35);
  transform: translateY(-1px);
}
.new-chat-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 12px 16px;
  border: none;
  border-radius: 12px;
  background: linear-gradient(135deg, #f7a8c4 0%, #e88a5f 100%);
  color: #fff;
  font-size: 15px;
  font-weight: 700;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
  box-shadow: 0 3px 10px rgba(232, 138, 95, 0.3);
}
.new-chat-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 18px rgba(232, 138, 95, 0.45);
}

.agent-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px;
  border-radius: 12px;
  background: linear-gradient(135deg, #faf9f4 0%, #f5f3ed 100%);
  border: 1px solid #e8e2d6;
  flex-shrink: 0;
}
.agent-avatar {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: rgba(139, 115, 85, 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26px;
  flex-shrink: 0;
  overflow: hidden;
}
.agent-name {
  font-size: 16px;
  font-weight: 700;
  color: #4a3a28;
  line-height: 1.3;
}
.agent-provider {
  font-size: 12px;
  color: #988b7a;
  margin-top: 3px;
}

.conv-list {
  flex: 1;
  overflow-y: auto;
  padding: 4px 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-height: 0;
}
.conv-list-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 700;
  color: #a0936e;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 8px 6px 6px;
  border-bottom: 1px solid #f0ebe0;
  margin-bottom: 4px;
}
.conv-count {
  font-size: 12px;
  padding: 1px 8px;
  border-radius: 10px;
  background: #f0e8d8;
  color: #8a7b66;
  font-weight: 700;
}

.conv-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 13px 14px;
  border-radius: 10px;
  cursor: pointer;
  font-size: 15px;
  color: #5c4b38;
  transition: all 0.18s ease;
  border: 1px solid transparent;
}
.conv-item:hover {
  background: #f5f3ed;
  border-color: #e8e2d6;
}
.conv-item.active {
  background: #e6f9f6;
  border-color: #19c8b9;
  color: #158a80;
  font-weight: 700;
  box-shadow: 0 2px 8px rgba(25, 200, 185, 0.12);
}
.conv-indicator {
  width: 4px;
  height: 24px;
  border-radius: 4px;
  background: #d0c8b8;
  flex-shrink: 0;
  transition: all 0.18s ease;
}
.conv-indicator.active {
  background: #19c8b9;
  height: 32px;
  box-shadow: 0 0 8px rgba(25, 200, 185, 0.4);
}
.conv-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: default;
}
.conv-rename-input {
  width: 100%;
  border: 1.5px solid #19c8b9;
  border-radius: 6px;
  padding: 4px 8px;
  font-size: 14px;
  font-family: inherit;
  color: #4a3a28;
  background: #fff;
  outline: none;
}
.conv-delete-btn {
  display: none;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border: none;
  border-radius: 6px;
  background: none;
  color: #c4b89e;
  font-size: 12px;
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.15s;
}
.conv-item:hover .conv-delete-btn {
  display: flex;
}
.conv-delete-btn:hover {
  background: rgba(232, 95, 95, 0.12);
  color: #e85f5f;
}
.conv-status {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.conv-status.active {
  background: #6fba2c;
}
.conv-status.paused {
  background: #e8a735;
}
.conv-status.error {
  background: #e85f5f;
}
.conv-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 40px 16px;
  color: #a0936e;
  font-size: 14px;
  text-align: center;
}
.conv-empty-hint {
  font-size: 12px;
  color: #c4b89e;
}

/* Task records */
.task-records {
  margin-top: 12px;
  flex-shrink: 0;
}
.task-records :deep(.animal-collapse__question) {
  font-size: 13px;
  font-weight: 700;
  color: #6b5b48;
}
.task-records-section {
  margin-bottom: 4px;
}
.task-section-title {
  font-size: 11px;
  color: #9ca3af;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 4px 6px 2px;
}
.task-records-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-height: 200px;
  overflow-y: auto;
}
.task-record-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s;
  font-size: 12px;
}
.task-record-item:hover {
  background: rgba(25, 200, 185, 0.06);
}
.task-record-item.task-card-item {
  border-left: 3px solid #534ab7;
}
.task-record-item.running {
  border-left-color: #f59e0b;
}
.task-record-item.pending {
  border-left-color: #6366f1;
}
.task-record-item.completed {
  border-left-color: #10b981;
}
.task-record-item.failed {
  border-left-color: #ef4444;
}
.task-record-item.stopped {
  border-left-color: #9ca3af;
}
.task-record-status {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.task-record-status.running {
  background: #409eff;
  animation: pulse-dot 1.5s infinite;
}
.task-record-status.pending {
  background: #e6a23c;
}
.task-record-status.completed {
  background: #6fba2c;
}
.task-record-status.failed {
  background: #e85f5f;
}
.task-record-status.stopped {
  background: #9ca3af;
}
.task-record-badge {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 6px;
  font-weight: 700;
  flex-shrink: 0;
}
.task-record-badge.running {
  background: #fef3c7;
  color: #92400e;
}
.task-record-badge.pending {
  background: #eef2ff;
  color: #4f46e5;
}
.task-record-badge.completed {
  background: #d1fae5;
  color: #065f46;
}
.task-record-badge.failed {
  background: #fee2e2;
  color: #991b1b;
}
.task-record-badge.stopped {
  background: #f3f4f6;
  color: #374151;
}
.task-record-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}
.task-record-name {
  font-weight: 600;
  color: #4a3a28;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.task-record-meta {
  font-size: 10px;
  color: #a0936e;
}
.task-records-empty {
  font-size: 12px;
  color: #9ca3af;
  padding: 8px 6px;
  text-align: center;
}
@keyframes pulse-dot {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.3;
  }
}

/* Chat main */
.chat-main {
  display: flex;
  flex-direction: column;
  padding: 0;
  min-height: 0;
  overflow: hidden;
  height: 100%;
}
.chat-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14px;
  color: #988b7a;
  padding: 40px;
}
.empty-avatar {
  padding: 24px;
  background: #faf9f4;
  border-radius: 28px;
  border: 2px dashed #d8cfc0;
}
.empty-title {
  font-size: 20px;
  font-weight: 700;
  color: #4a3a28;
}
.empty-desc {
  font-size: 15px;
  color: #988b7a;
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 24px;
  background: #fff;
  border-bottom: 2px solid #e8e2d6;
  flex-shrink: 0;
}
.chat-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}
.chat-header-title {
  font-size: 16px;
  font-weight: 700;
  color: #4a3a28;
}
.msg-count {
  font-size: 13px;
  color: #a0936e;
  padding: 3px 10px;
  background: #f5f3ed;
  border-radius: 10px;
  font-weight: 600;
}

/* Stream mode badge */
.stream-mode-badge {
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 8px;
  font-weight: 700;
}
.stream-mode-badge.sse {
  background: #e6f9f6;
  color: #158a80;
  border: 1px solid #19c8b9;
  animation: pulse-badge 1.5s infinite;
}
.stream-mode-badge.fallback {
  background: #fef6e6;
  color: #8a6d14;
  border: 1px solid #e8a735;
}
@keyframes pulse-badge {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}

/* Model status badge — shows live model activity (thinking / calling / streaming / done) */
.model-status-badge {
  font-size: 12px;
  padding: 3px 10px 3px 8px;
  border-radius: 8px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid;
}
.model-status-badge.idle {
  display: none;
}
.model-status-badge.thinking {
  background: #f0f4ff;
  color: #4256b8;
  border-color: #6c80d4;
}
.model-status-badge.calling_model {
  background: #fef0ff;
  color: #9448b3;
  border-color: #c97adb;
}
.model-status-badge.tool_calling {
  background: #fff5e6;
  color: #a36600;
  border-color: #e0a13a;
}
.model-status-badge.streaming {
  background: #e6f9f6;
  color: #158a80;
  border-color: #19c8b9;
}
.model-status-badge.done {
  background: #e6f5e6;
  color: #2a7a2a;
  border-color: #4caf50;
}
/* Animated dot for "in progress" states */
.model-status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  display: inline-block;
}
.model-status-badge.thinking .model-status-dot,
.model-status-badge.calling_model .model-status-dot,
.model-status-badge.tool_calling .model-status-dot,
.model-status-badge.streaming .model-status-dot {
  animation: status-blink 1.2s infinite ease-in-out;
}
@keyframes status-blink {
  0%,
  100% {
    opacity: 0.3;
    transform: scale(0.85);
  }
  50% {
    opacity: 1;
    transform: scale(1.2);
  }
}

/* Connection indicator — always visible in header */
.connection-indicator {
  font-size: 12px;
  padding: 4px 12px;
  border-radius: 10px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 4px;
}
.connection-indicator.sse {
  background: #e6f9f6;
  color: #158a80;
  border: 1.5px solid #19c8b9;
}
.connection-indicator.fallback {
  background: #fef6e6;
  color: #8a6d14;
  border: 1.5px solid #e8a735;
}
.connection-indicator.connecting {
  background: #eef0f7;
  color: #4a5a8a;
  border: 1.5px solid #7889c4;
}
.connection-indicator.unknown {
  background: #f5f3ed;
  color: #988b7a;
  border: 1.5px solid #d0c8b8;
}


.chat-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px 28px;
  display: flex;
  flex-direction: column;
  gap: 22px;
  background: #faf9f4;
}

/* Typing indicator (stream placeholder) */
.typing-row {
  display: flex;
  gap: 14px;
  max-width: 80%;
  align-self: flex-start;
}
.typing-row .msg-avatar {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: #fff;
  border: 1px solid #e8e2d6;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  flex-shrink: 0;
}
.typing-row .msg-content {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.typing-row .msg-author {
  font-size: 13px;
  font-weight: 700;
  color: #a0936e;
  padding: 0 6px;
}
.typing-row .msg-text {
  padding: 16px 20px;
  border-radius: 18px;
  background: #fff;
  border: 1px solid #e8e2d6;
  border-bottom-left-radius: 6px;
}


.mermaid-placeholder {
  opacity: 0.6;
  transition: opacity 0.2s;
}
.mermaid-diagram {
  margin: 10px 0;
  padding: 14px;
  background: #fff;
  border-radius: 12px;
  border: 2px solid #19c8b9;
  overflow-x: auto;
  display: flex;
  justify-content: center;
}
.mermaid-diagram svg {
  max-width: 100%;
  height: auto;
}

/* Typing */
.typing {
  display: flex;
  align-items: center;
  gap: 6px;
  min-height: 28px;
}
.typing span {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: #19c8b9;
  animation: bounce 1.4s ease-in-out infinite;
}
.typing span:nth-child(1) {
  animation-delay: 0s;
}
.typing span:nth-child(2) {
  animation-delay: 0.2s;
}
.typing span:nth-child(3) {
  animation-delay: 0.4s;
}
@keyframes bounce {
  0%,
  80%,
  100% {
    transform: translateY(0);
  }
  40% {
    transform: translateY(-7px);
  }
}

/* File preview */
</style>
