/** toolbox-assembly — 装配台来源定义与生效清单（纯函数，无 HTTP） */
import type { PlatformToolCategory } from "../api/toolbox"
import type { SharedToolItem } from "../api/toolbox"

export type AssemblySourceKey = "biz" | "skill" | "prompt" | "port" | "debug" | "keywords"

export interface AssemblySourceDef {
  key: AssemblySourceKey
  name: string
  desc: string
  /** 空串 = 无「交给助手」总闸（如设备提示词） */
  gateKey: string
  /**
   * 来源行副标题文案。无总闸来源必填——它们不参与「交给助手」装配，
   * 不存在「n/m 生效」语义，不得借用其它来源的数量充当分母。
   */
  meta?: string
  accent: string
}

export const ASSEMBLY_SOURCES: AssemblySourceDef[] = [
  {
    key: "biz",
    name: "平台业务",
    desc: "设备 / 用例 / 报告等平台 Tool",
    gateKey: "enable_business_tools",
    accent: "var(--c-device)",
  },
  {
    key: "skill",
    name: "自定义 Skill",
    desc: "engines/ai/skills 下的本地与上传 Skill",
    gateKey: "enable_skills",
    accent: "var(--c-runner)",
  },
  {
    key: "prompt",
    name: "设备提示词",
    desc: "规划 / 执行 / 验收三角色系统提示词（Markdown）",
    gateKey: "",
    meta: "规划 / 执行 / 验收 · 始终交给助手",
    accent: "var(--c-ai)",
  },
  {
    key: "port",
    name: "无线端口",
    desc: "日志端口监听与原始日志查看（不交给助手）",
    gateKey: "",
    meta: "监听开关 · 原始日志 · 不交给助手",
    accent: "var(--c-ai)",
  },
  {
    key: "debug",
    name: "模型调试",
    desc: "单模型调试台：提示词 / 工具 / Skill + 对话验证",
    gateKey: "",
    meta: "规划 / 执行 / 验收 · 仅调试不交给助手",
    accent: "var(--c-ai)",
  },
  {
    key: "keywords",
    name: "日志关键词",
    desc: "关键词 → 功能模块 / 功能点（判定口径，只读）",
    gateKey: "",
    meta: "关键词 → 功能模块 / 功能点 · 只读",
    accent: "var(--c-ai)",
  },
]

export interface LiveChip {
  name: string
  source: AssemblySourceKey
  /** 业务工具所属模块 key，便于跳转展开 */
  moduleKey?: string
}

export const LIVE_CHIP_PREVIEW = 8

export function buildLiveChips(input: {
  gates: Record<string, boolean>
  categories: PlatformToolCategory[]
  sharedItems: SharedToolItem[]
}): LiveChip[] {
  const chips: LiveChip[] = []
  if (input.gates.enable_business_tools) {
    for (const cat of input.categories) {
      for (const tool of cat.tools) {
        if (tool.enabled) chips.push({ name: tool.name, source: "biz", moduleKey: cat.key })
      }
    }
  }
  if (input.gates.enable_skills) {
    for (const item of input.sharedItems) {
      if (item.enabled && item.item_type === "skill" && !item.missing) {
        chips.push({ name: item.name, source: "skill" })
      }
    }
  }
  return chips
}

export function matchQuery(text: string, query: string): boolean {
  const q = query.trim().toLowerCase()
  if (!q) return true
  return text.toLowerCase().includes(q)
}

/** 有总闸的来源才参与「未装配」提示 */
export function gatedSources(): AssemblySourceDef[] {
  return ASSEMBLY_SOURCES.filter((s) => Boolean(s.gateKey))
}

/** 按 key 取来源定义（名称 / 说明的唯一真相源，子区块不得自行硬编码） */
export function sourceDef(key: AssemblySourceKey): AssemblySourceDef {
  const def = ASSEMBLY_SOURCES.find((s) => s.key === key)
  if (!def) throw new Error(`未登记的工具来源: ${key}`)
  return def
}
