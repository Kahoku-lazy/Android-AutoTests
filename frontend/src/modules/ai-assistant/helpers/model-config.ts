/** Model Config — 内置 provider 模型列表（从 index.vue 提取） */

export const BUILTIN_MODELS: Record<string, string[]> = {
  dashscope: ['qwen-max', 'qwen-plus', 'qwen-turbo', 'qwen3-235b'],
  openai: ['gpt-4o', 'gpt-4-turbo', 'gpt-3.5-turbo', 'o4-mini'],
  anthropic: ['claude-fable-5', 'claude-opus-4-8', 'claude-sonnet-4-6'],
  deepseek: ['deepseek-v4-flash', 'deepseek-v4-pro', 'deepseek-chat', 'deepseek-reasoner'],
  custom: [],
}

export const CUSTOM_PROVIDER_MODELS: Record<string, string[]> = {
  deepseek: ['deepseek-v4-flash', 'deepseek-v4-pro', 'deepseek-chat', 'deepseek-reasoner'],
}

/** 合并内置 + 自定义 + 检测到的模型列表 */
export function getModelOptions(
  agent: { model_provider?: string; model_name?: string; name?: string; available_models?: string[] },
  pendingModel?: string,
): { label: string; value: string }[] {
  const builtin = BUILTIN_MODELS[agent.model_provider || ''] || []
  const detected = Array.isArray(agent.available_models) ? agent.available_models : []
  let customModels: string[] = []
  const searchText = [agent.model_provider || '', agent.name || '', agent.model_name || ''].join(' ').toLowerCase()
  for (const [key, models] of Object.entries(CUSTOM_PROVIDER_MODELS)) {
    if (searchText.includes(key)) { customModels = models; break }
  }
  const all = [...new Set([agent.model_name, pendingModel, ...builtin, ...customModels, ...detected].filter(Boolean) as string[])]
  return all.map(m => ({ label: m, value: m }))
}
