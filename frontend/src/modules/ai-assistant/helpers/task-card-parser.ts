/** Task Card Parser — 从 ChatView.vue 提取的工具输出解析逻辑 */

export interface TaskCardProgress {
  passed: number
  failed: number
  total: number
}

/** 从工具输出文本中提取 passed/failed/total 进度 */
export function parseTaskCardProgress(output: unknown): TaskCardProgress | null {
  if (!output) return null
  const str = typeof output === 'string' ? output : JSON.stringify(output)
  const passedMatch = str.match(/(?:passed|通过)[=:]?\s*(\d+)/i)
  const failedMatch = str.match(/(?:failed|失败)[=:]?\s*(\d+)/i)
  const totalMatch = str.match(/Total:\s*(\d+)/i)
  if (!passedMatch && !failedMatch) return null
  const passed = parseInt(passedMatch?.[1] || '0')
  const failed = parseInt(failedMatch?.[1] || '0')
  const total = parseInt(totalMatch?.[1] || String(passed + failed))
  return { passed, failed, total }
}

/** 更新 taskCards 中的进度信息（create_runner_task / run_test / stop_run） */
export function updateTaskCardProgress(
  tr: { name?: string; output?: string },
  taskCards: Record<string, object>,
): void {
  const name = tr?.name || ''
  const output = tr?.output || ''
  if (!['create_runner_task', 'run_test', 'stop_run'].includes(name)) return

  const progress = parseTaskCardProgress(output)
  if (!progress) return

  // Find task card by matching output content
  for (const key of Object.keys(taskCards)) {
    const card = taskCards[key] as { output?: string; progress?: TaskCardProgress }
    if (card?.output && output.includes(card.output.slice(0, 30))) {
      card.progress = progress
      return
    }
  }
}
