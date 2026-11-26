export function estimateEvalTokens(
  posCount: number,
  negCount: number,
  chunkSize = 400,
): { chat_input_tokens: number; chat_output_tokens: number; embedding_tokens: number } {
  const total = posCount + negCount
  return {
    chat_input_tokens: posCount * chunkSize * 2 + negCount * 200,
    chat_output_tokens: total * 80,
    embedding_tokens: total * 60,
  }
}

export function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`
}
