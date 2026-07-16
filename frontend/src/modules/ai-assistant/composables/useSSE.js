import { ref, nextTick } from "vue";
import client from "@/shared/api-client.js";
import { ElMessage } from "element-plus";
import { streamChat } from "../api.js";

/**
 * SSE streaming, fallback send, stop, and HITL confirm handling.
 */
export function useSSE({
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
  updateTaskCardProgress,
}) {
  const streamMode = ref(null);
  const abortController = ref(null);
  const sseBuilder = ref(null);
  const modelStatus = ref("idle");
  const sending = ref(false);
  const pendingConfirm = ref(null);
  const pendingConfirmMsgIdx = ref(-1);
  const degradedMode = ref(false);

  /** Check platform health; update degradedMode if AgentScope is unavailable. */
  async function checkHealth() {
    try {
      const { data } = await client.get("/ai/health");
      if (data.ok && data.mode !== "full") {
        degradedMode.value = true;
        if (data.mode === "offline") {
          ElMessage.warning(
            "AgentScope 和 Redis 均不可用，AI 对话将使用 Django 降级模式（直接调用模型 API）",
            { duration: 6000 },
          );
        } else {
          ElMessage.warning(
            "AgentScope 服务不可用，AI 对话已切换到 Django 降级模式",
            { duration: 5000 },
          );
        }
      } else {
        degradedMode.value = false;
      }
    } catch (_) {
      // Health endpoint itself unreachable — assume degraded
      degradedMode.value = true;
    }
    return degradedMode.value;
  }

  async function fallbackSend(msgText) {
    try {
      const { data } = await client.post(
        `/ai/conversations/${activeConv.value}/send`,
        { message: msgText },
      );
      if (data.ok) {
        if (data.degraded) degradedMode.value = true;
        if (assistIdx.value < messages.value.length) {
          messages.value[assistIdx.value] = {
            ...data.message,
            flow: "fallback",
          };
        }
        loadConversations();
        await nextTick();
        renderMermaidBlocks();
      } else if (assistIdx.value < messages.value.length) {
        messages.value[assistIdx.value] = {
          role: "assistant",
          content: data.error || "发送失败",
          tokens: 0,
          flow: "fallback",
        };
      }
    } catch (e) {
      console.error("Fallback send failed:", e);
      const errMsg =
        e.code === "ECONNABORTED"
          ? "请求超时，请重试"
          : e.response?.status === 500
            ? "服务器错误"
            : "发送失败，请检查服务状态。";
      if (assistIdx.value < messages.value.length) {
        messages.value[assistIdx.value] = {
          role: "assistant",
          content: errMsg,
          tokens: 0,
          flow: "fallback",
        };
      }
    }
    sending.value = false;
    streamMode.value = null;
    abortController.value = null;
    scrollBottom();
  }

  async function trySSEStream(msgText) {
    const { data: sessionData } = await client.post(
      `/ai/conversations/${activeConv.value}/create-scope-session`,
    );
    if (!sessionData.ok) {
      throw new Error(sessionData.error || "AgentScope session creation failed");
    }

    const sessionId = sessionData.session_id;
    const agentScopeId = sessionData.agent_scope_id;

    const conv = conversations.value.find((c) => c.id === activeConv.value);
    if (conv) conv.agent_scope_session_id = sessionId;

    await client.post(`/ai/conversations/${activeConv.value}/save-message`, {
      role: "user",
      content: msgText,
    });

    streamMode.value = "sse";
    connectionMode.value = "sse";
    if (assistIdx.value < messages.value.length) {
      messages.value[assistIdx.value].flow = "sse";
    }

    let streamDone = false;
    let fullContent = "";
    let thinkingContent = "";
    let currentToolArgsJson = "";

    const { controller, builder } = streamChat(sessionId, agentScopeId, msgText, {
      onStatus: (status) => {
        modelStatus.value = status;
        if (status === "done") {
          setTimeout(() => {
            if (modelStatus.value === "done") modelStatus.value = "idle";
          }, 3000);
        }
      },
      onThinkingStart: () => {
        thinkingContent = "";
        if (assistIdx.value < messages.value.length) {
          messages.value[assistIdx.value].thinking = "";
          messages.value[assistIdx.value].content = fullContent;
          scrollBottom();
        }
      },
      onThinkingDelta: (delta, full) => {
        thinkingContent = full || thinkingContent + delta;
        if (assistIdx.value < messages.value.length) {
          messages.value[assistIdx.value].thinking = thinkingContent;
          scrollBottom();
        }
      },
      onThinkingEnd: (evt) => {
        if (assistIdx.value < messages.value.length) {
          messages.value[assistIdx.value].thinkingDone = true;
          if (evt?.block?.thinking) {
            messages.value[assistIdx.value].thinking = evt.block.thinking;
          }
          scrollBottom();
        }
      },
      onTextDelta: (delta, full) => {
        fullContent = full != null ? full : fullContent + delta;
        if (assistIdx.value < messages.value.length) {
          messages.value[assistIdx.value].content = fullContent;
          scrollBottom();
        }
      },
      onTextEnd: (evt) => {
        if (evt?.text != null) {
          fullContent = evt.text;
          if (assistIdx.value < messages.value.length) {
            messages.value[assistIdx.value].content = fullContent;
          }
        }
      },
      onToolCallStart: (evt) => {
        currentToolArgsJson = "";
        toolCalls.value.push({
          id: evt.toolCallId,
          name: evt.name,
          state: "calling",
        });
        if (assistIdx.value < messages.value.length) {
          messages.value[assistIdx.value].toolFlow = [...toolCalls.value];
          scrollBottom();
        }
      },
      onToolCallDelta: (evt) => {
        currentToolArgsJson =
          evt.argsJson != null
            ? evt.argsJson
            : currentToolArgsJson + (evt.delta || "");
      },
      onToolCallEnd: (evt) => {
        const tc = evt.toolCall;
        if (tc) {
          const idx = toolCalls.value.findIndex((t) => t.id === tc.id);
          const displayArgs = tc.inputRaw || currentToolArgsJson;
          if (idx >= 0) {
            toolCalls.value[idx] = { ...tc, state: "submitted", displayArgs };
          }
        }
        if (assistIdx.value < messages.value.length) {
          messages.value[assistIdx.value].toolFlow = [...toolCalls.value];
          scrollBottom();
        }
      },
      onToolResultStart: (evt) => {
        const idx = toolCalls.value.findIndex((t) => t.id === evt.toolCallId);
        if (idx >= 0) toolCalls.value[idx].state = "running";
        if (assistIdx.value < messages.value.length) {
          messages.value[assistIdx.value].toolFlow = [...toolCalls.value];
          scrollBottom();
        }
      },
      onToolResultDelta: (evt) => {
        const idx = toolCalls.value.findIndex((t) => t.id === evt.toolCallId);
        if (idx >= 0) {
          toolCalls.value[idx].partialOutput =
            evt.output != null
              ? evt.output
              : (toolCalls.value[idx].partialOutput || "") + (evt.delta || "");
        }
        if (assistIdx.value < messages.value.length) {
          messages.value[assistIdx.value].toolFlow = [...toolCalls.value];
          scrollBottom();
        }
      },
      onToolResultEnd: (evt) => {
        const tr = evt.toolResult;
        if (tr) {
          const idx = toolCalls.value.findIndex((t) => t.id === tr.id);
          if (idx >= 0) {
            toolCalls.value[idx].state = tr.state || "success";
            toolCalls.value[idx].output = tr.output;
            toolCalls.value[idx].partialOutput = null;
          }
          updateTaskCardProgress(tr);
        }
        if (assistIdx.value < messages.value.length) {
          messages.value[assistIdx.value].toolFlow = [...toolCalls.value];
          scrollBottom();
        }
      },
      onModelCallStart: (evt) => {
        if (assistIdx.value < messages.value.length) {
          messages.value[assistIdx.value].modelName = evt.modelName;
        }
      },
      onModelCallEnd: (evt) => {
        if (assistIdx.value < messages.value.length) {
          messages.value[assistIdx.value].tokens = evt.outputTokens || 0;
          messages.value[assistIdx.value].inputTokens = evt.inputTokens || 0;
        }
      },
      onHint: (evt) => {
        let hintData = evt.hint;
        if (typeof hintData === "string") {
          try {
            hintData = JSON.parse(hintData);
          } catch {}
        }
        if (hintData?.type === "task_card" && hintData?.run_id) {
          const existing = taskCards.value[hintData.run_id] || {};
          taskCards.value[hintData.run_id] = {
            ...existing,
            ...hintData,
            updatedAt: Date.now(),
          };
          if (assistIdx.value < messages.value.length) {
            messages.value[assistIdx.value].hint = hintData;
          }
          scrollBottom();
        } else if (assistIdx.value < messages.value.length) {
          messages.value[assistIdx.value].hint = hintData;
          scrollBottom();
        }
      },
      onRequireConfirm: (evt) => {
        modelStatus.value = "idle";
        pendingConfirm.value = evt;
        pendingConfirmMsgIdx.value = assistIdx.value;
      },
      onExceedMaxIters: () => {
        if (assistIdx.value < messages.value.length) {
          const block = builder.getFullThinking();
          messages.value[assistIdx.value].thinking = block;
          messages.value[assistIdx.value].thinkingDone = true;
          messages.value[assistIdx.value].reason = "exceed_max_iters";
          messages.value[assistIdx.value].content =
            (messages.value[assistIdx.value].content || "") +
            "\n\n⚠️ **[智能体已达最大推理次数]** 响应可能被截断，建议简化问题或分步提问。";
          scrollBottom();
        }
      },
      onDone: async () => {
        if (streamDone) return;
        streamDone = true;
        const finalContent = builder.getFullText() || fullContent;
        const blocks = builder.getBlocks();
        const reason = builder.getReason();
        try {
          await client.post(
            `/ai/conversations/${activeConv.value}/save-message`,
            {
              role: "assistant",
              content: finalContent,
              blocks,
              reason,
              tokens: builder.getTokenUsage().total || 0,
              input_tokens: builder.getTokenUsage().input || 0,
              model_name: builder.modelName || "",
            },
          );
          loadConversations();
          await nextTick();
          renderMermaidBlocks();
        } catch (e) {
          console.error("Failed to save streamed message:", e);
        }
        sending.value = false;
        streamMode.value = null;
        abortController.value = null;
        scrollBottom();
      },
      onError: async (err) => {
        if (streamDone) return;
        streamDone = true;
        console.warn("SSE stream error, falling back:", err);
        streamMode.value = "fallback";
        connectionMode.value = "fallback";
        modelStatus.value = "idle";
        if (assistIdx.value < messages.value.length) {
          messages.value[assistIdx.value].flow = "fallback";
        }
        await fallbackSend(msgText);
      },
    });

    abortController.value = controller;
    sseBuilder.value = builder;

    try {
      const convItem = conversations.value.find((c) => c.id === activeConv.value);
      if (convItem && convItem.title === "新对话") {
        const { data } = await client.post(
          `/ai/conversations/${activeConv.value}/rename`,
          { title: msgText.slice(0, 30) },
        );
        if (data.ok) convItem.title = data.title;
      }
    } catch (_) {}
  }

  function appendUserAndAssistantPlaceholder(displayText) {
    messages.value.push({ role: "user", content: displayText });
    assistIdx.value = messages.value.length;
    messages.value.push({
      role: "assistant",
      content: "",
      tokens: 0,
      flow: null,
    });
    scrollBottom();
  }

  async function sendStreamMessage(msgText, displayText) {
    if (!activeConv.value || sending.value) return;
    sending.value = true;
    toolCalls.value = [];
    modelStatus.value = "calling_model";
    appendUserAndAssistantPlaceholder(displayText);

    try {
      await trySSEStream(msgText);
    } catch (e) {
      console.warn("SSE setup failed, falling back to Django /send:", e);
      streamMode.value = "fallback";
      connectionMode.value = "fallback";
      if (assistIdx.value < messages.value.length) {
        messages.value[assistIdx.value].flow = "fallback";
      }
      await fallbackSend(msgText);
    }
  }

  function stopStream() {
    if (abortController.value) {
      abortController.value.abort();
      if (
        assistIdx.value < messages.value.length &&
        messages.value[assistIdx.value].flow === "sse"
      ) {
        const partial = messages.value[assistIdx.value].content;
        client
          .post(`/ai/conversations/${activeConv.value}/save-message`, {
            role: "assistant",
            content: partial || "（用户主动停止）",
            tokens: 0,
            reason: "stopped",
            blocks: sseBuilder.value ? sseBuilder.value.getBlocks() : [],
          })
          .catch((e) => console.error("Failed to save partial stream:", e));
      }
      sending.value = false;
      abortController.value = null;
      streamMode.value = null;
      modelStatus.value = "idle";
      scrollBottom();
    }
    pendingConfirm.value = null;
  }

  async function resolveConfirm(toolCallId, approved, reason = "") {
    const confirm = pendingConfirm.value;
    if (!confirm) return;
    if (
      pendingConfirmMsgIdx.value >= 0 &&
      pendingConfirmMsgIdx.value < messages.value.length
    ) {
      const msg = messages.value[pendingConfirmMsgIdx.value];
      if (!msg.toolFlow) msg.toolFlow = [];
      const idx = msg.toolFlow.findIndex((t) => t.id === toolCallId);
      if (idx >= 0) {
        msg.toolFlow[idx] = {
          ...msg.toolFlow[idx],
          state: approved ? "submitted" : "denied",
        };
      } else {
        msg.toolFlow.push({
          id: toolCallId,
          state: approved ? "submitted" : "denied",
          name: "",
        });
      }
    }
    pendingConfirm.value = null;
    modelStatus.value = "tool_calling";

    const result = {
      reply_id: confirm.replyId || "",
      confirm_results: [
        {
          tool_call_id: toolCallId,
          approved,
          ...(reason ? { reason } : {}),
        },
      ],
    };
    try {
      await client.post(
        `/ai/conversations/${activeConv.value}/confirm-result`,
        result,
      );
    } catch (e) {
      console.error("Failed to send confirm result:", e);
      ElMessage.warning("确认结果发送失败，工具调用可能无法继续");
    }
  }

  async function approveAll() {
    const confirm = pendingConfirm.value;
    if (!confirm?.toolCalls) return;
    for (const tc of confirm.toolCalls) {
      await resolveConfirm(tc.tool_call_id, true);
    }
  }

  async function denyAll() {
    const confirm = pendingConfirm.value;
    if (!confirm?.toolCalls) return;
    for (const tc of confirm.toolCalls) {
      await resolveConfirm(tc.tool_call_id, false, "用户拒绝");
    }
  }

  return {
    streamMode,
    abortController,
    sseBuilder,
    modelStatus,
    sending,
    pendingConfirm,
    pendingConfirmMsgIdx,
    degradedMode,
    checkHealth,
    trySSEStream,
    fallbackSend,
    sendStreamMessage,
    stopStream,
    resolveConfirm,
    approveAll,
    denyAll,
  };
}
