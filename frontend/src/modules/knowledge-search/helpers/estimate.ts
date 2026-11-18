/** 评测纯函数：token 预估（与后端启发式同口径）与百分比展示。 */

/** 与后端 eval_runner.estimate_cost 同口径的启发式预估。 */
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

/** 指标展示为百分比，保留一位小数。 */
export function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`
}
