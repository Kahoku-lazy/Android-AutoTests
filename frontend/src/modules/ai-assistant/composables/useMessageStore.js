import { ref } from "vue";

/** Parse hint from stored blocks — handles plain string and JSON object hints. */
export function parseHintFromBlocks(hintBlock, allBlocks) {
  if (!hintBlock) return "";
  const raw = hintBlock.hint || "";
  if (typeof raw === "object") return raw;
  if (typeof raw === "string") {
    try {
      return JSON.parse(raw);
    } catch {
      return raw;
    }
  }
  return raw;
}

/** Rebuild toolFlow array from stored ContentBlocks for cross-session display. */
export function rebuildToolFlow(blocks) {
  if (!blocks.length) return [];
  const pairs = blocks.filter((b) => b.type === "tool_pair");
  if (pairs.length) {
    return pairs.map((p) => ({
      id: p.call?.id || "",
      name: p.call?.name || "",
      displayArgs:
        p.call?.inputRaw || (p.call?.input ? JSON.stringify(p.call.input) : ""),
      state: p.result?.state || "success",
      output: p.result?.output || "",
    }));
  }
  const calls = blocks.filter((b) => b.type === "tool_call");
  const results = blocks.filter((b) => b.type === "tool_result");
  return calls.map((c) => {
    const r = results.find((res) => res.id === c.id);
    return {
      id: c.id || "",
      name: c.name || "",
      displayArgs: c.inputRaw || (c.input ? JSON.stringify(c.input) : ""),
      state: r?.state || "success",
      output: r?.output || "",
    };
  });
}

export function useMessageStore() {
  const messages = ref([]);
  const assistIdx = ref(-1);
  /** Conversation ID that has an active background SSE stream. */
  const backgroundStreamConvId = ref(null);

  function normalizeLoadedMessage(m) {
    // Prefer per-message flow (saved with the reply); legacy rows have no tag
    const flow =
      m.role === "assistant"
        ? m.flow === "sse" || m.flow === "fallback"
          ? m.flow
          : null
        : null;
    const blocks = m.blocks || [];
    const textBlock = blocks.find((b) => b.type === "text");
    const thinkingBlock = blocks.find((b) => b.type === "thinking");
    const toolBlocks = blocks.filter(
      (b) =>
        b.type === "tool_call" ||
        b.type === "tool_result" ||
        b.type === "tool_pair",
    );
    const hintBlock = blocks.find((b) => b.type === "hint");
    return {
      ...m,
      flow,
      content: m.content || textBlock?.text || "",
      thinking: thinkingBlock?.thinking || "",
      thinkingDone: !!thinkingBlock?.thinking,
      toolFlow: rebuildToolFlow(toolBlocks),
      hint: parseHintFromBlocks(hintBlock, blocks),
      reason: m.reason || "normal",
    };
  }

  function hydrateMessages(dataMessages) {
    messages.value = dataMessages.map((m) => normalizeLoadedMessage(m));
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
    return assistIdx.value;
  }

  function clearMessages() {
    messages.value = [];
    assistIdx.value = -1;
  }

  return {
    messages,
    assistIdx,
    backgroundStreamConvId,
    hydrateMessages,
    appendUserAndAssistantPlaceholder,
    clearMessages,
    normalizeLoadedMessage,
  };
}
