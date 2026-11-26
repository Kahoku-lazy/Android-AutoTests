<script setup lang="ts">
import { computed, h, onMounted, ref } from "vue"
import { useRouter } from "vue-router"
import { ElMessage } from "element-plus"
import DoodleBtn from "@/shared/components/DoodleBtn.vue"
import EmptyState from "@/shared/components/patterns/EmptyState.vue"
import ErrorState from "@/shared/components/patterns/ErrorState.vue"
import SkeletonCard from "@/shared/components/patterns/SkeletonCard.vue"
import { formatApiError } from "@/shared/api-client"
import { useAuthUser } from "@/shared/composables/useAuthUser"
import { listSopWorkflows } from "../api/assistants"
import { workflowCards } from "../helpers/sop-card"
import { sopSubmittedMessage } from "../helpers/sop-form"
import AssistantCardView from "./AssistantCard.vue"
import SectionBar from "./SectionBar.vue"
import SopRunForm from "./SopRunForm.vue"
import SopWorkflowEditor from "./SopWorkflowEditor.vue"
import type { AssistantCard, SopWorkflow, SopWorkflowCard } from "../types"

const router = useRouter()
const { isAssistantAuthor } = useAuthUser()

const props = defineProps<{ cards: AssistantCard[] }>()
const emit = defineEmits<{ loaded: [workflows: SopWorkflow[]] }>()

const workflows = ref<SopWorkflow[]>([])
const loading = ref(false)
const loaded = ref(false)
const error = ref("")
const editorOpen = ref(false)
const editing = ref<SopWorkflow | null>(null)
const runOpen = ref(false)
const running = ref<SopWorkflow | null>(null)

const tiles = computed<SopWorkflowCard[]>(() => workflowCards(workflows.value, props.cards))
const runTitle = computed(() => (running.value ? `任务 · ${running.value.name}` : "任务"))

async function load(): Promise<void> {
  loading.value = true
  error.value = ""
  try {
    workflows.value = await listSopWorkflows()
    loaded.value = true
    emit("loaded", workflows.value)
  } catch (e) {
    error.value = formatApiError(e as never, "工作流加载失败")
  } finally {
    loading.value = false
  }
}

function openCreate(): void {
  editing.value = null
  editorOpen.value = true
}

function openEdit(tile: SopWorkflowCard): void {
  editing.value = workflows.value.find((item) => item.id === tile.id) || null
  editorOpen.value = true
}

function openRun(tile: SopWorkflowCard): void {
  running.value = workflows.value.find((item) => item.id === tile.id) || null
  runOpen.value = true
}

function closeEditor(): void {
  editorOpen.value = false
  editing.value = null
}

async function onChanged(): Promise<void> {
  closeEditor()
  await load()
}

function onSubmitted(taskId: number): void {
  runOpen.value = false
  running.value = null
  const { text, action } = sopSubmittedMessage(taskId)
  ElMessage.success({
    duration: 6000,
    message: h("span", { class: "sop-toast" }, [
      h("span", text),
      h(
        "button",
        {
          type: "button",
          class: "el-message__action",
          onClick: () => {
            void router.push("/tasks")
          },
        },
        action,
      ),
    ]),
  })
}

onMounted(load)
</script>

<template>
  <section class="sop-section" aria-label="工作流">
    <SectionBar title="工作流" :count="`共 ${workflows.length} 条`">
      <template #action>
        <DoodleBtn v-if="isAssistantAuthor" tone="yellow" @click="openCreate">新建工作流</DoodleBtn>
      </template>
    </SectionBar>

    <ErrorState v-if="error" :message="error" @retry="load" />
    <SkeletonCard v-else-if="loading && !loaded" variant="list" :lines="3" />
    <template v-else>
      <EmptyState
        v-if="!tiles.length"
        icon="🧩"
        text="还没有工作流"
        hint="新建一条，卡片上只放名称与两个助手"
      />
      <div v-else class="sop-section__grid">
        <AssistantCardView
          v-for="(tile, index) in tiles"
          :key="tile.id"
          :item="{ kind: 'workflow', card: tile }"
          :can-edit="isAssistantAuthor"
          :index="index"
          @edit="openEdit(tile)"
          @activate="openRun(tile)"
        />
      </div>
    </template>

    <el-dialog
      v-model="editorOpen"
      :title="editing ? '配置工作流' : '新建工作流'"
      width="min(520px, 92vw)"
      destroy-on-close
      @closed="editing = null"
    >
      <SopWorkflowEditor
        :workflow="editing"
        :cards="cards"
        @close="closeEditor"
        @saved="onChanged"
        @deleted="onChanged"
      />
    </el-dialog>

    <el-dialog v-model="runOpen" :title="runTitle" width="min(960px, 92vw)" destroy-on-close>
      <SopRunForm
        v-if="running"
        :workflow="running"
        @close="runOpen = false"
        @submitted="onSubmitted"
      />
    </el-dialog>
  </section>
</template>

<style scoped>
.sop-section {
  display: grid;
  gap: var(--app-space-md);
}

.sop-section__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, 280px);
  gap: var(--app-space-lg);
  align-items: start;
}
</style>
