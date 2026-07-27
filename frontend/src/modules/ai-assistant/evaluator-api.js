/** Evaluator API helpers. */
import client from '@/shared/api-client.js'

// ── Question Banks ──

export function listBanks() {
  return client.get('/evaluator/banks')
}

export function getBank(id) {
  return client.get(`/evaluator/banks/${id}`)
}

export function createBank(data) {
  return client.post('/evaluator/banks/create', data)
}

export function updateBank(id, data) {
  return client.post(`/evaluator/banks/${id}/update`, data)
}

export function deleteBank(id) {
  return client.post(`/evaluator/banks/${id}/delete`)
}

export function seedDefaultBank() {
  return client.post('/evaluator/banks/seed')
}

// ── Frameworks ──

export function listFrameworks() {
  return client.get('/evaluator/frameworks')
}

// ── Eval Runs ──

export function listRuns() {
  return client.get('/evaluator/runs')
}

export function getRun(id) {
  return client.get(`/evaluator/runs/${id}`)
}

export function startRun(agentId, bankId, judgeModel, framework) {
  return client.post('/evaluator/runs/start', {
    agent_id: agentId,
    bank_id: bankId,
    judge_model: judgeModel || 'qwen-max',
    framework: framework || 'self',
  })
}

export function deleteRun(id) {
  return client.post(`/evaluator/runs/${id}/delete`)
}

// ── Human Scoring ──

export function submitScore(resultId, scores) {
  return client.post(`/evaluator/results/${resultId}/score`, scores)
}

// ── KB Self-Test ──

export function kbSelfTest() {
  return client.post('/evaluator/kb-self-test')
}

// ── KB Search ──

export function kbSearch(payload) {
  return client.post('/evaluator/kb-search', payload)
}

// ── Agents (read-only from ai_assistant) ──

export function listAgents() {
  return client.get('/ai/agents')
}
