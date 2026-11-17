<script setup lang="ts">
/**
 * 工作流区块：卡片网格 + 新建/配置弹窗 + 任务弹窗。
 *
 * 工作流不再是页内常驻表单：卡片上只有「配置」与「任务」两个动作，
 * 运行输入（平台用例或里程碑 YAML、必选设备）只在任务弹窗里出现。
 * 任务弹窗按两栏呈现，宽度定在这里（960px，窄屏 92vw）。
 */
import { computed, h, onMounted, ref } from "vue"
import { useRouter } from "vue-router"
import { ElMessage } from "element-plus"
import DoodleBtn from "@/shared/components/DoodleBtn.vue"
import EmptyState from "@/shared/components/patterns/EmptyState.vue"
import ErrorState from "@/shared/components/patterns/ErrorState.vue"
import SkeletonCard from "@/shared/components/patterns/SkeletonCard.vue"
import { formatApiError } from "@/shared/api-client"
import { listSopWorkflows } from "../api/assistants"
import { workflowCards } from "../helpers/sop-card"
import { sopSubmittedMessage } from "../helpers/sop-form"
import AssistantCardView from "./AssistantCard.vue"
import SectionBar from "./SectionBar.vue"
import SopRunForm from "./SopRunForm.vue"
import SopWorkflowEditor from "./SopWorkflowEditor.vue"
import type { AssistantCard, SopWorkflow, SopWorkflowCard } from "../types"

const router = useRouter()

const props = defineProps<{ cards: AssistantCard[] }>()

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

/** 保存或删除后重取列表：卡片的名称、绑定与笔色都要跟着变。 */
async function onChanged(): Promise<void> {
  closeEditor()
  await load()
}

/** 提交成功：留在本页，提示里给可点的任务清单链接。未点击不跳转。 */
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
        <DoodleBtn tone="yellow" @click="openCreate">新建工作流</DoodleBtn>
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
          :index="index"
          @edit="openEdit(tile)"
          @activate="openRun(tile)"
        />
      </div>
    </template>

    <!-- 不 append-to-body：弹窗留在 .ai-assistant-page 里才继承模块令牌 -->
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

/* 便签卡正文三行 + 一排色块；列宽固定 280px（2026-11-17 需求方按参考图指定），
   不再往上限 360px 拉宽——卡片右侧会留一大片空白 */
.sop-section__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, 280px);
  gap: var(--app-space-lg);
  align-items: start;
}
</style>
