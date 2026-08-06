/** Evaluator API helpers — TypeScript */
import djangoClient from '@/shared/api-client'

// ── Question Banks ──

export async function listBanks(): Promise<{ ok: boolean; banks?: object[]; error?: string }> {
  const { data } = await djangoClient.get<{ ok: boolean; banks?: object[]; error?: string }>('/evaluator/banks')
  return data
}

export async function getBank(id: number): Promise<{ ok: boolean; bank?: object; error?: string }> {
  const { data } = await djangoClient.get<{ ok: boolean; bank?: object; error?: string }>(`/evaluator/banks/${id}`)
  return data
}

export async function createBank(payload: object): Promise<{ ok: boolean; bank?: object; error?: string }> {
  const { data } = await djangoClient.post<{ ok: boolean; bank?: object; error?: string }>('/evaluator/banks/create', payload)
  return data
}

export async function updateBank(id: number, payload: object): Promise<{ ok: boolean; bank?: object; error?: string }> {
  const { data } = await djangoClient.post<{ ok: boolean; bank?: object; error?: string }>(`/evaluator/banks/${id}/update`, payload)
  return data
}

export async function deleteBank(id: number): Promise<{ ok: boolean; error?: string }> {
  const { data } = await djangoClient.post<{ ok: boolean; error?: string }>(`/evaluator/banks/${id}/delete`)
  return data
}

export async function seedDefaultBank(): Promise<{ ok: boolean; bank?: object; error?: string }> {
  const { data } = await djangoClient.post<{ ok: boolean; bank?: object; error?: string }>('/evaluator/banks/seed')
  return data
}

// ── Frameworks ──

export async function listFrameworks(): Promise<{ ok: boolean; frameworks?: object[]; error?: string }> {
  const { data } = await djangoClient.get<{ ok: boolean; frameworks?: object[]; error?: string }>('/evaluator/frameworks')
  return data
}

// ── Eval Runs ──

export async function listRuns(): Promise<{ ok: boolean; runs?: object[]; error?: string }> {
  const { data } = await djangoClient.get<{ ok: boolean; runs?: object[]; error?: string }>('/evaluator/runs')
  return data
}

export async function getRun(id: number): Promise<{ ok: boolean; run?: object; error?: string }> {
  const { data } = await djangoClient.get<{ ok: boolean; run?: object; error?: string }>(`/evaluator/runs/${id}`)
  return data
}

export async function startRun(agentId: number, bankId: number, judgeModel?: string, framework?: string): Promise<{ ok: boolean; run?: object; error?: string }> {
  const { data } = await djangoClient.post<{ ok: boolean; run?: object; error?: string }>('/evaluator/runs/start', {
    agent_id: agentId,
    bank_id: bankId,
    judge_model: judgeModel || 'qwen-max',
    framework: framework || 'self',
  })
  return data
}

export async function deleteRun(id: number): Promise<{ ok: boolean; error?: string }> {
  const { data } = await djangoClient.post<{ ok: boolean; error?: string }>(`/evaluator/runs/${id}/delete`)
  return data
}

// ── Human Scoring ──

export async function submitScore(resultId: number, scores: object): Promise<{ ok: boolean; error?: string }> {
  const { data } = await djangoClient.post<{ ok: boolean; error?: string }>(`/evaluator/results/${resultId}/score`, scores)
  return data
}

// ── KB Self-Test ──

export async function kbSelfTest(): Promise<{ ok: boolean; result?: object; error?: string }> {
  const { data } = await djangoClient.post<{ ok: boolean; result?: object; error?: string }>('/evaluator/kb-self-test')
  return data
}

// ── KB Search ──

export async function kbSearch(payload: object): Promise<{ ok: boolean; results?: object[]; error?: string }> {
  const { data } = await djangoClient.post<{ ok: boolean; results?: object[]; error?: string }>('/evaluator/kb-search', payload)
  return data
}

// ── Agents (read-only from ai_assistant) ──

export async function listAgents(): Promise<{ ok: boolean; agents?: object[]; error?: string }> {
  const { data } = await djangoClient.get<{ ok: boolean; agents?: object[]; error?: string }>('/ai/agents')
  return data
}
