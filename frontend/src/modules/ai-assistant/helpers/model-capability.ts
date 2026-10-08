/**
 * 模型能力：清单项类型与能力判定（组件只渲染，判定逻辑集中在此以便单测）。
 *
 * 与后端/引擎的模型目录（`engines/ai/agents/config.py` 的 `DEEPSEEK_MODELS`）保持一致，
 * 由后端对拍用例 `tests/graybox/unit/test_ai_deepseek_model_catalog.py` 守住。
 */

export type ModelOption = { name: string; multimodal?: boolean }

/** 下拉选项文案：多模态模型标「支持图片」，其余标「纯文本」 */
export function modelOptionLabel(option: ModelOption): string {
  return option.multimodal ? `${option.name}（多模态 · 支持图片）` : `${option.name}（纯文本）`
}

/**
 * 当前选中的模型是否为**已知纯文本**模型。
 *
 * 只认清单内的已知模型：手工输入的自定义模型名能力未知，返回 false —— 不提示，避免误报。
 */
export function isKnownTextOnly(options: ModelOption[], modelName?: string): boolean {
  const hit = options.find((m) => m.name === modelName)
  return hit ? !hit.multimodal : false
}
