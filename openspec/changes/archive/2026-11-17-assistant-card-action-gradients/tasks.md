# 任务：卡片动作键改成语义渐变

## 1. 实现

- [x] 1.1 助手卡「配置 / 对话」加修饰类 `--config` / `--chat`，分别给天蓝、薄荷绿渐变
- [x] 1.2 工作流卡「配置」改天蓝渐变、「任务」改薰衣草紫渐变；三块占位块不变
- [x] 1.3 渐变统一 `linear-gradient(180deg, color-mix(语义色 20%, 纸), color-mix(语义色 5%, 纸))`
- [x] 1.4 悬停不再替换底色（原 `--assistant-marker-tint` 会冲掉渐变），只保留位移与笔色硬影

## 2. 文档同步

- [x] 2.1 `ai-assistant/AGENTS.md` 与 `doodle-craft/references/components/assistant-marker-card.md` 里「配置柠黄 / 任务青绿」的旧描述改成新口径

## 3. 验证

- [x] 3.1 浏览器量测 `/ai-assistant`：四枚键 `background-image` 均为 `linear-gradient`，两端分别为语义色 20% / 5% 与纸色混合；描边仍 dashed / 圆角不变
- [x] 3.2 `npx prettier --check`、`npx eslint src/modules/ai-assistant`、`npx vue-tsc --noEmit` 对本模块无新错
- [x] 3.3 `npx vitest run tests/ai-assistant` 全绿；截图 `temps/assistant-actions.png`
