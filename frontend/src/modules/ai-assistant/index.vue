<script setup lang="ts">
import { onMounted, ref } from "vue"
import { ElMessage } from "element-plus"
import { useRouter } from "vue-router"
import DoodleBtn from "@/shared/components/DoodleBtn.vue"
import WorkbenchHeader from "@/shared/components/WorkbenchHeader.vue"
import EmptyState from "@/shared/components/patterns/EmptyState.vue"
import ErrorState from "@/shared/components/patterns/ErrorState.vue"
import SkeletonCard from "@/shared/components/patterns/SkeletonCard.vue"
import { formatApiError } from "@/shared/api-client"
import SectionDivider from "@/shared/components/SectionDivider.vue"
import AssistantCardView from "./components/AssistantCard.vue"
import SectionBar from "./components/SectionBar.vue"
import SopWorkflowSection from "./components/SopWorkflowSection.vue"
import AssistantEditor from "./components/AssistantEditor.vue"
import { useAuthUser } from "@/shared/composables/useAuthUser"
import { listAssistants, publishAssistant } from "./api/assistants"
import type { AssistantCard, SopWorkflow } from "./types"
import "./tokens.css"
import "./editor-form.css"

const router = useRouter()
const { isAssistantAuthor } = useAuthUser()
const cards = ref<AssistantCard[]>([])
const loading = ref(false)
const loaded = ref(false)
const error = ref("")
const editorOpen = ref(false)
const editing = ref<AssistantCard | null>(null)
const workflows = ref<SopWorkflow[]>([])
const publishError = ref<Record<string, string>>({})

async function load(): Promise<void> {
  loading.value = true
  error.value = ""
  try {
    cards.value = await listAssistants()
    loaded.value = true
  } catch (e) {
    error.value = formatApiError(e as never, "助手加载失败")
  } finally {
    loading.value = false
  }
}

function openCreate(): void {
  editing.value = null
  editorOpen.value = true
}

function openEdit(card: AssistantCard): void {
  editing.value = card
  editorOpen.value = true
}

function closeEditor(): void {
  editorOpen.value = false
  editing.value = null
}

async function onSaved(): Promise<void> {
  closeEditor()
  await load()
}

async function publish(card: AssistantCard): Promise<void> {
  publishError.value = { ...publishError.value, [card.assistant_id]: "" }
  try {
    await publishAssistant(card.assistant_id)
    cards.value = cards.value.map((item) =>
      item.assistant_id === card.assistant_id ? { ...item, release_state: "published" } : item,
    )
    ElMessage.success("已发布")
  } catch (cause) {
    const message = formatApiError(cause as never, "发布失败")
    publishError.value = { ...publishError.value, [card.assistant_id]: message }
    ElMessage.error(message)
  }
}

function openChat(card: AssistantCard): void {
  void router.push({
    name: "ai-assistant-chat",
    params: { assistantId: card.assistant_id },
    query: { marker: card.marker, name: card.display_name },
  })
}

onMounted(load)
</script>

<template>
  <div class="doc-page doc-page--fixed wb-shell ai-assistant-page">
    <WorkbenchHeader
      title="平台助手"
      icon="bot"
      icon-gradient="linear-gradient(135deg, var(--c-ai), var(--assistant-marker-teal))"
    />
    <div class="doc-body">
      <SectionBar title="AI 助手" :count="`共 ${cards.length} 位助手`">
        <template #action>
          <DoodleBtn
            v-if="isAssistantAuthor"
            tone="teal"
            @click="router.push('/ai-assistant/evals')"
            >评测</DoodleBtn
          >
          <DoodleBtn v-if="isAssistantAuthor" tone="yellow" @click="openCreate">新建助手</DoodleBtn>
        </template>
      </SectionBar>

      <ErrorState v-if="error" :message="error" @retry="load" />
      <SkeletonCard v-else-if="loading && !loaded" variant="card" :lines="3" />
      <template v-else>
        <EmptyState
          v-if="cards.length === 0"
          icon="🖍️"
          text="还没有助手"
          hint="新建一位，卡片上只放名称、头像与 Agent 配置名"
        />
        <div v-if="cards.length > 0" class="ai-assistant-page__grid">
          <AssistantCardView
            v-for="(card, index) in cards"
            :key="card.assistant_id"
            :item="{ kind: 'assistant', card }"
            :index="index"
            :can-edit="isAssistantAuthor"
            :can-publish="isAssistantAuthor"
            :error="publishError[card.assistant_id] || ''"
            @edit="openEdit(card)"
            @activate="openChat(card)"
            @publish="publish(card)"
          />
        </div>
        <SectionDivider class="ai-assistant-page__divider" />
        <SopWorkflowSection :cards="cards" @loaded="workflows = $event" />
      </template>
    </div>

    <el-dialog
      v-model="editorOpen"
      :title="editing ? '编辑助手' : '新建助手'"
      width="min(520px, 92vw)"
      destroy-on-close
      @closed="editing = null"
    >
      <AssistantEditor
        :card="editing"
        :workflows="workflows"
        @close="closeEditor"
        @saved="onSaved"
        @deleted="onSaved"
      />
    </el-dialog>
  </div>
</template>

<style scoped>
.ai-assistant-page__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: var(--app-space-lg);
  align-items: start;
}

.ai-assistant-page__divider {
  margin: var(--app-space-md) 0;
}
</style>
