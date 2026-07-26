import { ref, nextTick } from "vue";
import client from "@/shared/api-client.js";
import { ElMessage, ElMessageBox } from "element-plus";

export function useConversation(agentIdRef, messageStore) {
  const conversations = ref([]);
  const activeConv = ref(null);
  const connectionMode = ref("unknown");
  const editingConvId = ref(null);
  const editingTitle = ref("");

  async function loadConversations() {
    try {
      const { data } = await client.get(
        `/ai/agents/${agentIdRef.value}/conversations`,
      );
      if (data.ok) conversations.value = data.conversations;
    } catch (e) { console.error(e); }
  }

  async function newChat(onSelect) {
    try {
      const { data } = await client.post(
        `/ai/agents/${agentIdRef.value}/conversations/create`,
        { title: "新对话" },
      );
      if (data.ok) {
        conversations.value.unshift({
          id: data.id,
          title: "新对话",
          status: "active",
          agent_scope_session_id: data.agent_scope_session_id || "",
        });
        connectionMode.value = data.agent_scope_session_id ? "sse" : "fallback";
        if (onSelect) await onSelect(data.id);
      }
    } catch (e) {
      connectionMode.value = "unknown";
      console.error(e);
    }
  }

  async function selectChat(id, { onAfterSelect } = {}) {
    activeConv.value = id;
    try {
      const { data } = await client.get(`/ai/conversations/${id}/messages`);
      if (data.ok) {
        const conv = conversations.value.find((c) => c.id === id);
        if (conv?.agent_scope_session_id) {
          connectionMode.value = "sse";
        } else {
          connectionMode.value = "connecting";
        }
        // If there is an active background stream for this conversation,
        // keep the in-memory messages (which have live partial content)
        // instead of overwriting with stale backend data.
        if (messageStore.backgroundStreamConvId?.value === id) {
          // Don't hydrate — in-memory messages are being updated by the
          // background SSE stream.  The backend will get the final content
          // when the stream completes.
        } else {
          messageStore.backgroundStreamConvId.value = null;
          messageStore.hydrateMessages(data.messages);
        }
      }
    } catch (e) {
      connectionMode.value = "unknown";
      console.error(e);
    }
    if (onAfterSelect) await onAfterSelect(id);
  }

  function startRename(conv) {
    editingConvId.value = conv.id;
    editingTitle.value = conv.title;
    nextTick(() => {
      const input = document.querySelector(".conv-rename-input");
      if (input) {
        input.focus();
        input.select();
      }
    });
  }

  async function finishRename() {
    const id = editingConvId.value;
    const title = editingTitle.value.trim();
    editingConvId.value = null;
    if (!title || !id) return;
    try {
      const { data } = await client.post(`/ai/conversations/${id}/rename`, {
        title,
      });
      if (data.ok) {
        const c = conversations.value.find((x) => x.id === id);
        if (c) c.title = data.title;
      }
    } catch (e) { console.error(e); }
  }

  function cancelRename() {
    editingConvId.value = null;
  }

  async function deleteConversation(conv) {
    try {
      await ElMessageBox.confirm(`删除对话「${conv.title}」？`, "确认删除", {
        confirmButtonText: "删除",
        cancelButtonText: "取消",
        type: "warning",
      });
      const { data } = await client.post(`/ai/conversations/${conv.id}/delete`);
      if (data.ok) {
        ElMessage.success("已删除");
        if (activeConv.value === conv.id) {
          activeConv.value = null;
          messageStore.clearMessages();
        }
        loadConversations();
      }
    } catch (e) { console.error(e); }
  }

  return {
    conversations,
    activeConv,
    connectionMode,
    editingConvId,
    editingTitle,
    loadConversations,
    newChat,
    selectChat,
    startRename,
    finishRename,
    cancelRename,
    deleteConversation,
  };
}
