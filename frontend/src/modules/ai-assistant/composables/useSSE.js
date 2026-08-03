import { ref, nextTick } from "vue";
import client from "@/shared/api-client.js";
import { ElMessage } from "element-plus";
import { streamChat } from "../api.js";

/** AgentScope 不可用时统一回复文案 */
export const AI_DISCONNECT_MSG = "AgentScope 断开，模型服务无法使用";

/** 无内容 / 鉴权失败 / 通道错误 → 视为断线 */
function isDisconnectContent(content) {
  const text = String(content || "").trim();
  if (!text || text === AI_DISCONNECT_MSG) return true;
  return /API\s*错误\s*\(\s*401\s*\)|authentication_error|api key.*invalid|Authentication Fails|invalid_request_error|请求超时|服务器错误|SSE\s*(subscribe|stream)\s*(failed|error|closed)/i.test(
    text,
  );
}

/**
 * SSE streaming, stop, and HITL confirm handling.
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
  backgroundStreamConvId,
  appendPlaceholder,
}) {
  const streamMode = ref(null);
  const abortController = ref(null);
  const sseBuilder = ref(null);
  const modelStatus = ref("idle");
  const sending = ref(false);
  const pendingConfirm = ref(null);
  const pendingConfirmMsgIdx = ref(-1);
  const degradedMode = ref(false);
  /** 最近一次交互是否处于断线态（不禁用发送，仅影响展示） */
  const aiDisconnected = ref(false);
  let replyWatchdog = null;

  // Background streaming support: when the component unmounts we keep the
  // SSE stream alive so the AI can finish, and save partial state so the
  // user sees content when they return.
  let _detached = false;
  let _streamConvId = null; // captured at stream start, safe to use after unmount

  function clearReplyWatchdog() {
    if (replyWatchdog) {
      clearTimeout(replyWatchdog);
      replyWatchdog = null;
    }
  }

  function settleAssistant(content, extras = {}) {
    const disconnected = isDisconnectContent(content);
    aiDisconnected.value = disconnected;
    const finalContent = disconnected ? AI_DISCONNECT_MSG : content;
    if (assistIdx.value < messages.value.length) {
      const prev = messages.value[assistIdx.value] || {};
      messages.value[assistIdx.value] = {
        ...prev,
        role: "assistant",
        tokens: prev.tokens || 0,
        ...extras,
        content: finalContent,
        // Keep existing flow if settle call omitted it
        flow:
          extras.flow === "sse"
            ? extras.flow
            : prev.flow || null,
        reason: disconnected
          ? "error"
          : extras.reason || prev.reason || "normal",
      };
    }
    return !disconnected;
  }

  /** Save current partial assistant content to backend before navigating away. */
  async function _savePartialToBackend(reason = "detached") {
    if (assistIdx.value >= messages.value.length) return;
    const msg = messages.value[assistIdx.value];
    if (!msg || msg.role !== "assistant") return;
    const content = msg.content || "";
    const thinking = msg.thinking || "";
    const rounds = msg.rounds || [];
    // Check if any rounds have partial data worth saving
    const hasRoundData = rounds.some(
      (r) => r.thinking || (r.tools && r.tools.length),
    );
    // Nothing to save — skip
    if (!content && !thinking && !hasRoundData) return;
    const convId = _streamConvId || activeConv.value;
    if (!convId) return;
    try {
      // Build blocks array preserving per-round grouping so it can be
      // reconstructed when the message is loaded back.
      const blocks = [];
      if (hasRoundData) {
        // Serialize rounds as per-round thinking + tool_pair blocks
        rounds.forEach((round, ri) => {
          if (round.thinking) {
            blocks.push({
              type: "thinking",
              thinking: round.thinking,
              done: !!round.thinkingDone,
              roundIndex: ri + 1,
            });
          }
          for (const tool of round.tools || []) {
            blocks.push({
              type: "tool_pair",
              call: {
                id: tool.id,
                name: tool.name,
                inputRaw: tool.displayArgs || "",
                roundIndex: ri + 1,
              },
              result: {
                id: tool.id,
                name: tool.name,
                output: tool.output || "",
                state: tool.state || "success",
              },
            });
          }
        });
      } else if (thinking) {
        // Legacy: single thinking block (no per-round grouping)
        blocks.push({
          type: "thinking",
          thinking,
          done: !!msg.thinkingDone,
        });
      }
      if (content) {
        blocks.push({ type: "text", text: content });
      }
      await client.post(`/ai/conversations/${convId}/save-message`, {
        role: "assistant",
        content,
        blocks,
        reason,
        tokens: msg.tokens || 0,
        input_tokens: msg.inputTokens || 0,
        model_name: msg.modelName || "",
        flow: msg.flow || "",
      });
    } catch (e) {
      console.warn("Failed to save partial message before detach:", e);
    }
  }

  /** Detach the stream when navigating away from the chat page.
   *  Saves partial content and keeps the SSE stream alive in the
   *  background.  When the user returns, in-memory messages are
   *  preserved via backgroundStreamConvId.
   *  For in-component conversation switching use stopStream() instead
   *  (which also saves partial content but aborts the old stream). */
  async function detachStream() {
    if (!sending.value) return;
    await _savePartialToBackend("detached");
    _detached = true;
    // Keep backgroundStreamConvId set so returning to this conversation
    // preserves in-memory messages.  It will be cleared by finishSending
    // when the background stream completes.
    // Don't abort — let the SSE stream finish in background.
    // When onDone fires it will persist the full response.
  }

  function finishSending() {
    clearReplyWatchdog();
    sending.value = false;
    streamMode.value = null;
    abortController.value = null;
    modelStatus.value = "idle";
    if (!_detached) scrollBottom();
    _detached = false;
    if (backgroundStreamConvId) backgroundStreamConvId.value = null;
    _streamConvId = null;
  }

  function armReplyWatchdog() {
    clearReplyWatchdog();
    replyWatchdog = setTimeout(async () => {
      if (!sending.value) return;
      const cur = messages.value[assistIdx.value];
      if (cur?.role === "assistant" && !String(cur.content || "").trim()) {
        settleAssistant("");
        // Persist the disconnect notice so the message survives a page reload
        const convId = _streamConvId || activeConv.value;
        if (convId) {
          try {
            await client.post(`/ai/conversations/${convId}/save-message`, {
              role: "assistant",
              content: AI_DISCONNECT_MSG,
              blocks: [{ type: "text", text: AI_DISCONNECT_MSG }],
              reason: "error",
              tokens: 0,
              input_tokens: 0,
              model_name: "",
              flow: "",
            });
          } catch (e) {
            console.warn("Failed to save watchdog disconnect notice:", e);
          }
        }
        if (abortController.value) {
          try {
            abortController.value.abort();
          } catch (e) { console.error(e); }
        }
        finishSending();
      }
    }, 45000);
  }

  /** Check platform health; update degradedMode if AgentScope is unavailable. */
  async function checkHealth() {
    try {
      const { data } = await client.get("/ai/agents/health");
      // Health endpoint returns { ok, agents: [{ is_connected, ... }] }
      const anyConnected = data.agents?.some(a => a.is_connected);
      if (data.ok && anyConnected) {
        degradedMode.value = false;
      } else if (data.ok) {
        degradedMode.value = true;
        ElMessage.warning(
          "AgentScope 服务不可用，模型服务暂时无法使用",
          { duration: 5000 },
        );
      }
    } catch (e) {
      // Health endpoint itself unreachable — assume degraded
      degradedMode.value = true;
      console.error(e);
    }
    return degradedMode.value;
  }

  async function trySSEStream(msgText) {
    // Capture conversation ID at stream start so background completion
    // saves to the correct conversation even after component unmount.
    _streamConvId = activeConv.value;
    _detached = false;
    if (backgroundStreamConvId) backgroundStreamConvId.value = _streamConvId;

    const { data: sessionData } = await client.post(
      `/ai/conversations/${_streamConvId}/create-scope-session`,
    );
    if (!sessionData.ok) {
      throw new Error(
        sessionData.error || "AgentScope session creation failed",
      );
    }

    const sessionId = sessionData.session_id;
    const agentScopeId = sessionData.agent_scope_id;

    const conv = conversations.value.find((c) => c.id === _streamConvId);
    if (conv) conv.agent_scope_session_id = sessionId;

    await client.post(`/ai/conversations/${_streamConvId}/save-message`, {
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
    let currentToolArgsJson = "";

    // Per-round thinking: MODEL_CALL_START pushes a new slot.
    // rAF throttle still applies — just to the current round's thinking field.
    let _rounds = [];
    function _curRound() {
      if (_rounds.length === 0) _rounds.push({ thinking: '', thinkingDone: false, tools: [] });
      return _rounds[_rounds.length - 1];
    }

    // rAF throttle: push to Vue at most once/frame
    let _thinkRaf = null, _textRaf = null;
    function _flushThink() {
      _thinkRaf = null;
      _curRound().thinking = _curRound()._pending || _curRound().thinking;
      if (assistIdx.value < messages.value.length) {
        messages.value[assistIdx.value].rounds = [..._rounds];
        if (!_detached) scrollBottom();
      }
    }
    function _flushText() {
      _textRaf = null;
      if (assistIdx.value < messages.value.length) {
        const dc = isDisconnectContent(fullContent);
        messages.value[assistIdx.value].content = dc ? AI_DISCONNECT_MSG : fullContent;
        if (!_detached) scrollBottom();
      }
    }

    const { controller, builder } = streamChat(
      sessionId,
      agentScopeId,
      msgText,
      {
        onStatus: (status) => {
          modelStatus.value = status;
          if (status === "done") {
            setTimeout(() => {
              if (modelStatus.value === "done") modelStatus.value = "idle";
            }, 3000);
          }
        },
        onThinkingStart: () => {
          _curRound()._pending = '';
          _curRound().thinking = '';
          if (assistIdx.value < messages.value.length) {
            messages.value[assistIdx.value].content = fullContent;
            if (!_detached) scrollBottom();
          }
        },
        onThinkingDelta: (delta, full) => {
          const prev = _curRound()._pending || '';
          _curRound()._pending = full || prev + delta;
          if (_thinkRaf === null) _thinkRaf = requestAnimationFrame(_flushThink);
        },
        onThinkingEnd: (evt) => {
          if (_thinkRaf !== null) { cancelAnimationFrame(_thinkRaf); _thinkRaf = null; }
          _curRound()._pending = evt?.block?.thinking || _curRound()._pending;
          _flushThink();
          _curRound().thinkingDone = true;
        },
        onTextDelta: (delta, full) => {
          fullContent = full != null ? full : fullContent + delta;
          if (_textRaf === null) _textRaf = requestAnimationFrame(_flushText);
        },
        onTextEnd: (evt) => {
          if (_textRaf !== null) { cancelAnimationFrame(_textRaf); _textRaf = null; }
          if (evt?.text != null) fullContent = evt.text;
          _flushText();
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
            if (!_detached) scrollBottom();
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
            const tagged = { ...tc, state: "submitted", displayArgs, roundIndex: _rounds.length };
            if (idx >= 0) toolCalls.value[idx] = tagged;
            _curRound().tools.push(tagged);
          }
          if (assistIdx.value < messages.value.length) {
            messages.value[assistIdx.value].toolFlow = [...toolCalls.value];
            messages.value[assistIdx.value].rounds = [..._rounds];
            if (!_detached) scrollBottom();
          }
        },
        onToolResultStart: (evt) => {
          const idx = toolCalls.value.findIndex((t) => t.id === evt.toolCallId);
          if (idx >= 0) toolCalls.value[idx].state = "running";
          if (assistIdx.value < messages.value.length) {
            messages.value[assistIdx.value].toolFlow = [...toolCalls.value];
            if (!_detached) scrollBottom();
          }
        },
        onToolResultDelta: (evt) => {
          const idx = toolCalls.value.findIndex((t) => t.id === evt.toolCallId);
          if (idx >= 0) {
            toolCalls.value[idx].partialOutput =
              evt.output != null
                ? evt.output
                : (toolCalls.value[idx].partialOutput || "") +
                  (evt.delta || "");
          }
          if (assistIdx.value < messages.value.length) {
            messages.value[assistIdx.value].toolFlow = [...toolCalls.value];
            if (!_detached) scrollBottom();
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
            if (!_detached) scrollBottom();
          }
        },
        onModelCallStart: (evt) => {
          // New ReAct round
          _rounds.push({ thinking: '', thinkingDone: false, tools: [], _pending: '' });
          if (assistIdx.value < messages.value.length) {
            messages.value[assistIdx.value].modelName = evt.modelName;
            messages.value[assistIdx.value].rounds = [..._rounds];
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
            if (!_detached) scrollBottom();
          } else if (assistIdx.value < messages.value.length) {
            messages.value[assistIdx.value].hint = hintData;
            if (!_detached) scrollBottom();
          }
        },
        onRequireConfirm: (evt) => {
          modelStatus.value = "idle";
          pendingConfirm.value = evt;
          pendingConfirmMsgIdx.value = assistIdx.value;
        },
        onExceedMaxIters: () => {
          if (assistIdx.value < messages.value.length) {
            const allThinking = builder.getFullThinking();
            // Write to the current round so per-round rendering shows it
            if (_rounds.length > 0) {
              _curRound().thinking = allThinking || _curRound().thinking;
              _curRound().thinkingDone = true;
            }
            // Also write legacy fields for backwards-compatible rendering
            messages.value[assistIdx.value].thinking = allThinking;
            messages.value[assistIdx.value].thinkingDone = true;
            messages.value[assistIdx.value].rounds = [..._rounds];
            messages.value[assistIdx.value].reason = "exceed_max_iters";
            messages.value[assistIdx.value].content =
              (messages.value[assistIdx.value].content || "") +
              "\n\n⚠️ **[智能体已达最大推理次数]** 响应可能被截断，建议简化问题或分步提问。";
            if (!_detached) scrollBottom();
          }
        },
        onDone: async () => {
          if (streamDone) return;
          streamDone = true;
          clearReplyWatchdog();
          const finalContent = builder.getFullText() || fullContent;
          const blocks = builder.getBlocks();
          const reason = builder.getReason();
          const ok = settleAssistant(finalContent, {
            blocks,
            reason: isDisconnectContent(finalContent)
              ? "error"
              : reason || "normal",
            tokens: builder.getTokenUsage().total || 0,
            inputTokens: builder.getTokenUsage().input || 0,
            model_name: builder.modelName || "",
            flow: "sse",
          });
          if (ok) {
            try {
              const saveConvId = _streamConvId || activeConv.value;
              await client.post(
                `/ai/conversations/${saveConvId}/save-message`,
                {
                  role: "assistant",
                  content: finalContent,
                  blocks,
                  reason,
                  tokens: builder.getTokenUsage().total || 0,
                  input_tokens: builder.getTokenUsage().input || 0,
                  model_name: builder.modelName || "",
                  flow: "sse",
                },
              );
              // Only update UI if component is still mounted
              if (!_detached) {
                loadConversations();
                await nextTick();
                renderMermaidBlocks();
              }
            } catch (e) {
              console.error("Failed to save streamed message:", e);
            }
          }
          finishSending();
        },
        onError: async (err) => {
          if (streamDone) return;
          streamDone = true;
          clearReplyWatchdog();
          console.warn("SSE stream error:", err);
          modelStatus.value = "idle";
          settleAssistant("");
          finishSending();
        },
      },
    );

    abortController.value = controller;
    sseBuilder.value = builder;

    try {
      const convItem = conversations.value.find(
        (c) => c.id === activeConv.value,
      );
      if (convItem && convItem.title === "新对话") {
        const { data } = await client.post(
          `/ai/conversations/${activeConv.value}/rename`,
          { title: msgText.slice(0, 30) },
        );
        if (data.ok) convItem.title = data.title;
      }
    } catch (e) { console.error(e); }
  }


  async function sendStreamMessage(msgText, displayText) {
    // 防重入由调用方（ChatView.sendMessage）在置 sending=true 后保证；
    // 此处不再用 sending 短路，避免「先锁再调」时直接 return。
    // 断线时仍允许发送：尝试通道 → 无有效回复则统一「AI助手已断线……」
    if (!activeConv.value) return;
    sending.value = true;
    aiDisconnected.value = false;
    toolCalls.value = [];
    modelStatus.value = "calling_model";
    appendPlaceholder(displayText);
    scrollBottom();
    armReplyWatchdog();

    try {
      await trySSEStream(msgText);
    } catch (e) {
      console.warn("SSE setup failed:", e);
      modelStatus.value = "idle";
      settleAssistant("");
      finishSending();
    }
  }

  function stopStream() {
    clearReplyWatchdog();
    if (abortController.value) {
      abortController.value.abort();
      if (
        assistIdx.value < messages.value.length &&
        messages.value[assistIdx.value].flow === "sse"
      ) {
        const partial = messages.value[assistIdx.value].content;
        const content = String(partial || "").trim()
          ? partial
          : "（用户主动停止）";
        if (assistIdx.value < messages.value.length) {
          messages.value[assistIdx.value].content = content;
          messages.value[assistIdx.value].reason = "stopped";
        }
        client
          .post(
            `/ai/conversations/${_streamConvId || activeConv.value}/save-message`,
            {
              role: "assistant",
              content,
              tokens: 0,
              reason: "stopped",
              blocks: sseBuilder.value ? sseBuilder.value.getBlocks() : [],
              flow: "sse",
            },
          )
          .catch((e) => console.error("Failed to save partial stream:", e));
      }
      finishSending();
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
    aiDisconnected,
    checkHealth,
    trySSEStream,
    sendStreamMessage,
    stopStream,
    detachStream,
    resolveConfirm,
    approveAll,
    denyAll,
  };
}
