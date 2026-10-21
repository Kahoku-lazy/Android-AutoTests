/** AI 助手看板页 — 逻辑编排器（从 index.vue 提取） */
import { ref, onMounted, onActivated, type Ref } from "vue"
import { selectPop, iconBounce } from "@/shared/animations"
import { listAgents } from "./api/agents"
import type { AgentRecord } from "@/shared/types/ai"
import { agentDetailRoute } from "./constants"

// ── 页面配置 ──

export const PAGE_HEADER = {
  title: "AI 助手",
  subtitle: "智能体看板贴便签，配置小助手身份与线路",
  icon: "bot" as const,
  iconGradient: "linear-gradient(135deg, var(--ai-teal), var(--ai-teal-hover))",
}

// ── 展示辅助 ──

const TAPE_HUES = ["mint", "peach", "sky", "lilac", "honey"]
const NOTE_ROTATIONS = [-2.8, 1.6, -1.4, 2.2, -2.1, 1.2, -1.8, 2.5]

// ── 返回类型 ──

export interface AgentBoardState {
  agents: Ref<AgentRecord[]>
  loading: Ref<boolean>
  agentsError: Ref<string>
  // helpers
  PAGE_HEADER: typeof PAGE_HEADER
  noteRotation: (agent: AgentRecord) => number
  tapeHue: (agent: AgentRecord) => string
  // actions
  loadAgents: () => Promise<void>
  openAgent: (agent: AgentRecord) => void
  editAgent: (id: number, routeKey?: string) => void
  onAgentCardClick: (ev: Event) => void
}

// ── Composable ──

import { useRouter } from "vue-router"

export function useAgentBoard(dutyRosterRef: Ref<HTMLElement | null>): AgentBoardState {
  const router = useRouter()

  // ── State ──
  const agents = ref<AgentRecord[]>([])
  const loading = ref(false)
  const agentsError = ref("")

  // ── Derived ──

  // ── Sticky note display ──

  function hashString(s: string, mod: number): number {
    let hash = 0
    for (const c of s) hash = (hash * 31 + c.charCodeAt(0)) >>> 0
    return mod ? hash % mod : hash
  }

  function noteRotation(agent: AgentRecord) {
    return NOTE_ROTATIONS[hashString(String(agent.id), NOTE_ROTATIONS.length)]
  }
  function tapeHue(agent: AgentRecord) {
    return TAPE_HUES[hashString(agent.name || String(agent.id), TAPE_HUES.length)]
  }

  // ── Animations ──

  function onAgentCardClick(ev: Event) {
    const card = (ev as unknown as { currentTarget?: HTMLElement }).currentTarget
    if (card) selectPop(card as HTMLElement)
    const container = dutyRosterRef.value
    if (container) {
      const mark = container.querySelector(".brand-mark")
      if (mark) iconBounce(mark as HTMLElement)
    }
  }

  // ── Data loading ──

  async function loadAgents() {
    loading.value = true
    agentsError.value = ""
    try {
      const data = await listAgents()
      if (data.status && data.data) {
        agents.value = data.data.agents
      } else {
        agentsError.value = data.message || "加载失败"
      }
    } catch {
      agentsError.value = "加载智能体列表失败，请检查网络连接"
    }
    loading.value = false
  }

  function openAgent(agent: AgentRecord) {
    router.push(agentDetailRoute(agent.id))
  }
  function editAgent(id: number, routeKey?: string) {
    router.push({ path: agentDetailRoute(id), query: routeKey ? { route: routeKey } : {} })
  }

  // ── Lifecycle ──

  onMounted(async () => {
    await loadAgents()
  })
  onActivated(() => {
    loadAgents()
  })

  return {
    agents,
    loading,
    agentsError,
    PAGE_HEADER,
    noteRotation,
    tapeHue,
    loadAgents,
    openAgent,
    editAgent,
    onAgentCardClick,
  }
}
