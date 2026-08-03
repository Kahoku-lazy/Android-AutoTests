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

/** Rebuild per-round ReAct groups from persisted content blocks.
 *  Blocks saved by SSEMessageBuilder carry roundIndex on thinking and
 *  tool_call / tool_pair entries.  This reconstructs the rounds array
 *  that the streaming UI builds live, so loaded messages display the
 *  same per-round thinking + tool grouping. */
function rebuildRoundsFromBlocks(blocks) {
  if (!blocks || !blocks.length) return [];

  // Prefer tool_pair blocks (modern format); fall back to tool_call + tool_result
  const toolPairs = blocks.filter((b) => b.type === "tool_pair");
  const hasPairs = toolPairs.length > 0;

  // Index thinking blocks by roundIndex
  const thinkingByRound = {};
  for (const b of blocks) {
    if (b.type === "thinking" && typeof b.roundIndex === "number") {
      thinkingByRound[b.roundIndex] = b.thinking || "";
    }
  }

  // Index tools by roundIndex
  const toolsByRound = {};
  if (hasPairs) {
    for (const p of toolPairs) {
      const ri = p.call?.roundIndex;
      if (typeof ri !== "number") continue;
      if (!toolsByRound[ri]) toolsByRound[ri] = [];
      toolsByRound[ri].push({
        id: p.call?.id || "",
        name: p.call?.name || "",
        displayArgs:
          p.call?.inputRaw ||
          (p.call?.input ? JSON.stringify(p.call.input) : ""),
        state: p.result?.state || "success",
        output: p.result?.output || "",
      });
    }
  } else {
    const toolCalls = blocks.filter((b) => b.type === "tool_call");
    const toolResults = blocks.filter((b) => b.type === "tool_result");
    for (const c of toolCalls) {
      const ri = c.roundIndex;
      if (typeof ri !== "number") continue;
      const r = toolResults.find((res) => res.id === c.id);
      if (!toolsByRound[ri]) toolsByRound[ri] = [];
      toolsByRound[ri].push({
        id: c.id || "",
        name: c.name || "",
        displayArgs:
          c.inputRaw || (c.input ? JSON.stringify(c.input) : ""),
        state: r?.state || "success",
        output: r?.output || "",
      });
    }
  }

  // Collect and sort all round indices
  const allIndices = new Set([
    ...Object.keys(thinkingByRound).map(Number),
    ...Object.keys(toolsByRound).map(Number),
  ]);
  if (allIndices.size === 0) return [];

  return [...allIndices]
    .sort((a, b) => a - b)
    .map((ri) => ({
      thinking: thinkingByRound[ri] || "",
      thinkingDone: true, // Persisted blocks are always complete
      thinkingExpanded: false,
      tools: toolsByRound[ri] || [],
    }));
}

export function useMessageStore() {
  const messages = ref([]);
  const assistIdx = ref(-1);
  /** Conversation ID that has an active background SSE stream. */
  const backgroundStreamConvId = ref(null);

  function normalizeLoadedMessage(m) {
    // Guard against malformed data
    if (!m || typeof m !== "object") return null;
    // Prefer per-message flow (saved with the reply); legacy rows have no tag
    const flow =
      m.role === "assistant"
        ? m.flow === "sse"
          ? m.flow
          : null
        : null;
    const blocks = Array.isArray(m.blocks) ? m.blocks : [];

    // Rebuild per-round grouping from blocks (SSE multi-round ReAct)
    const rounds =
      m.role === "assistant" ? rebuildRoundsFromBlocks(blocks) : [];

    const textBlock = blocks.find((b) => b?.type === "text");
    // Legacy fallback: single thinking block (only used when no rounds)
    const thinkingBlock = !rounds.length
      ? blocks.find((b) => b?.type === "thinking")
      : null;
    const toolBlocks = !rounds.length
      ? blocks.filter(
          (b) =>
            b?.type === "tool_call" ||
            b?.type === "tool_result" ||
            b?.type === "tool_pair",
        )
      : [];
    const hintBlock = blocks.find((b) => b?.type === "hint");
    const content =
      typeof m.content === "string"
        ? m.content
        : textBlock?.text || "";
    return {
      ...m,
      flow,
      content,
      rounds,
      thinking: thinkingBlock?.thinking || "",
      thinkingDone: !!thinkingBlock?.thinking,
      toolFlow: rounds.length ? [] : rebuildToolFlow(toolBlocks),
      hint: parseHintFromBlocks(hintBlock, blocks),
      reason: m.reason || "normal",
    };
  }

  function hydrateMessages(dataMessages) {
    messages.value = dataMessages
      .map((m) => normalizeLoadedMessage(m))
      .filter(Boolean);
  }

  function appendUserAndAssistantPlaceholder(displayText) {
    messages.value.push({ role: "user", content: displayText });
    assistIdx.value = messages.value.length;
    messages.value.push({
      role: "assistant",
      content: "",
      tokens: 0,
      flow: null,
      rounds: [],
      deliveryStatus: "sending",  // 使用字符串避免循环依赖
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
