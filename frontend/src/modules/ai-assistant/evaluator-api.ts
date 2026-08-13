/** Evaluator API helpers — TypeScript */
import djangoClient from '@/shared/api-client'

// ── Question Banks ──

export async function listBanks(): Promise<{ status: boolean; banks?: object[]; message?: string }> {
  const { data } = await djangoClient.get<{ status: boolean; banks?: object[]; message?: string }>('/evaluator/banks')
  return data
}

export async function getBank(id: number): Promise<{ status: boolean; bank?: object; message?: string }> {
  const { data } = await djangoClient.get<{ status: boolean; bank?: object; message?: string }>(`/evaluator/banks/${id}`)
  return data
}

export async function createBank(payload: object): Promise<{ status: boolean; bank?: object; message?: string }> {
  const { data } = await djangoClient.post<{ status: boolean; bank?: object; message?: string }>('/evaluator/banks/create', payload)
  return data
}

export async function updateBank(id: number, payload: object): Promise<{ status: boolean; bank?: object; message?: string }> {
  const { data } = await djangoClient.post<{ status: boolean; bank?: object; message?: string }>(`/evaluator/banks/${id}/update`, payload)
  return data
}

export async function deleteBank(id: number): Promise<{ status: boolean; message?: string }> {
  const { data } = await djangoClient.post<{ status: boolean; message?: string }>(`/evaluator/banks/${id}/delete`)
  return data
}

export async function seedDefaultBank(): Promise<{ status: boolean; bank?: object; message?: string }> {
  const { data } = await djangoClient.post<{ status: boolean; bank?: object; message?: string }>('/evaluator/banks/seed')
  return data
}

// ── Frameworks ──

export async function listFrameworks(): Promise<{ status: boolean; frameworks?: object[]; message?: string }> {
  const { data } = await djangoClient.get<{ status: boolean; frameworks?: object[]; message?: string }>('/evaluator/frameworks')
  return data
}

// ── Eval Runs ──

export async function listRuns(): Promise<{ status: boolean; runs?: object[]; message?: string }> {
  const { data } = await djangoClient.get<{ status: boolean; runs?: object[]; message?: string }>('/evaluator/runs')
  return data
}

export async function getRun(id: number): Promise<{ status: boolean; run?: object; message?: string }> {
  const { data } = await djangoClient.get<{ status: boolean; run?: object; message?: string }>(`/evaluator/runs/${id}`)
  return data
}

export async function startRun(agentId: number, bankId: number, judgeModel?: string, framework?: string): Promise<{ status: boolean; run?: object; message?: string }> {
  const { data } = await djangoClient.post<{ status: boolean; run?: object; message?: string }>('/evaluator/runs/start', {
    agent_id: agentId,
    bank_id: bankId,
    judge_model: judgeModel || 'qwen-max',
    framework: framework || 'self',
  })
  return data
}

export async function deleteRun(id: number): Promise<{ status: boolean; message?: string }> {
  const { data } = await djangoClient.post<{ status: boolean; message?: string }>(`/evaluator/runs/${id}/delete`)
  return data
}

// ── Human Scoring ──

export async function submitScore(resultId: number, scores: object): Promise<{ status: boolean; message?: string }> {
  const { data } = await djangoClient.post<{ status: boolean; message?: string }>(`/evaluator/results/${resultId}/score`, scores)
  return data
}

// ── KB Self-Test ──

export async function kbSelfTest(): Promise<{ status: boolean; result?: object; message?: string }> {
  const { data } = await djangoClient.post<{ status: boolean; result?: object; message?: string }>('/evaluator/kb-self-test')
  return data
}

// ── KB Search ──

export async function kbSearch(payload: object): Promise<{ status: boolean; results?: object[]; message?: string }> {
  const { data } = await djangoClient.post<{ status: boolean; results?: object[]; message?: string }>('/evaluator/kb-search', payload)
  return data
}

// ── Agents (read-only from ai_assistant) ──

export async function listAgents(): Promise<{ status: boolean; agents?: object[]; message?: string }> {
  const { data } = await djangoClient.get<{ status: boolean; agents?: object[]; message?: string }>('/ai/agents')
  return data
}
